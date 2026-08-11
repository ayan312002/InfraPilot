import asyncio
import uuid
from collections import deque
from pathlib import Path

from langgraph.types import Command

from engine.graph.workflow import InfraPilotWorkflow
from engine.models.provision_state import ProvisionState


NODE_AGENT_MAP = {
    "requirement": "Requirement Agent",
    "image_fetch": "Image Fetcher Agent",
    "generate": "Compose Generator",
    "validate": "Validator",
    "approval": "Approval",
    "execute": "Executor",
}


class ProvisionService:
    """Service layer for running InfraPilot provisioning as a REST API.

    Uses LangGraph checkpointing + astream_events to pause at the
    human-in-the-loop approval step and resume when the client submits
    a decision. Events are emitted to per-session deques for SSE streaming.
    """

    def __init__(self):
        self._workflow = InfraPilotWorkflow()
        self._sessions: dict[str, dict] = {}
        self._event_queues: dict[str, deque] = {}

    @staticmethod
    def _prepare_workspace(state: ProvisionState) -> ProvisionState:
        if state.project_name is None:
            state.project_name = uuid.uuid4().hex[:6]

        state.output_dir = Path("generated") / state.project_name
        state.output_dir.mkdir(parents=True, exist_ok=True)

        (state.output_dir / "request.txt").write_text(state.user_request)

        return state

    # ------------------------------------------------------------------
    # Event formatting
    # ------------------------------------------------------------------

    def _format_event(self, event: dict) -> dict | None:
        """Map a LangChain stream event into a simple JSON-serializable dict."""
        event_type = event.get("event", "")
        name = event.get("name", "")
        metadata = event.get("metadata", {})
        node = metadata.get("langgraph_node", "")

        if event_type == "on_chain_start" and node:
            return {
                "type": "agent_start",
                "agent": NODE_AGENT_MAP.get(node, node),
                "node": node,
            }

        if event_type == "on_chain_end" and node:
            data = event.get("data", {})
            output = data.get("output", "")

            extracted = self._extract_agent_output(node, output)

            return {
                "type": "agent_end",
                "agent": NODE_AGENT_MAP.get(node, node),
                "node": node,
                "output": extracted,
            }

        if event_type == "on_chain_stream":
            chunk = event.get("data", {}).get("chunk", {})
            if isinstance(chunk, dict) and "__interrupt__" in chunk:
                interrupts = chunk["__interrupt__"]
                interrupt_value = None
                if interrupts:
                    interrupt_obj = interrupts[0]
                    if hasattr(interrupt_obj, "value"):
                        interrupt_value = interrupt_obj.value
                    else:
                        interrupt_value = interrupt_obj
                return {"type": "interrupt", "value": interrupt_value or {}}
            return None

        if event_type == "on_tool_start":
            data = event.get("data", {})
            return {
                "type": "tool_start",
                "tool": name,
                "input": data.get("input", {}),
            }

        if event_type == "on_tool_end":
            data = event.get("data", {})
            output = data.get("output", "")
            if isinstance(output, str) and len(output) > 1000:
                output = output[:1000] + "..."
            return {
                "type": "tool_end",
                "tool": name,
                "output": output,
            }

        return None

    def _extract_agent_output(self, node: str, output) -> str:
        """Extract a concise, useful output string from a node's result."""
        obj = output
        if isinstance(output, str) and output:
            return output[:200]
        if output is None:
            obj = getattr(output, "__dict__", {})
        if not isinstance(obj, dict):
            obj = getattr(obj, "model_dump", lambda: {})() if hasattr(obj, "model_dump") else {}

        if node == "requirement":
            spec = obj.get("provision_spec") or {}
            services = spec.get("services", []) if isinstance(spec, dict) else []
            names = [s.get("name", s.get("image", "unknown")) for s in services] if services else ["unknown"]
            return f"Parsed {len(services) if services else 0} service(s): {', '.join(names[:3])}"

        if node == "image_fetch":
            spec = obj.get("provision_spec") or {}
            services = spec.get("services", []) if isinstance(spec, dict) else []
            if services:
                images = [f'{s.get("name","?")}:{s.get("image","")}' for s in services[:3]]
                return f"Resolved images: {', '.join(images)}"
            return "Images resolved"

        if node == "generate":
            config = obj.get("generated_config", "")
            if config:
                lines = config.split("\n")
                return f"docker-compose.yml ({len(lines)} lines)\n" + "\n".join(lines[:3])
            return "docker-compose.yml generated"

        if node == "validate":
            vr = obj.get("validation_result") or {}
            if isinstance(vr, dict):
                if vr.get("success"):
                    return "✓ Compose validation passed — no errors"
                errors = vr.get("errors", [])
                return f"✗ Validation failed: {errors[0] if errors else 'unknown'}"
            return "Validation completed"

        if node == "approval":
            approved = obj.get("approved")
            if approved:
                return "✓ Configuration approved"
            return "✗ Changes requested"

        if node == "execute":
            er = obj.get("execution_result") or {}
            if isinstance(er, dict):
                if er.get("success"):
                    container = er.get("container_id", "")
                    return f"✓ Deployed (container: {container[:12]}...)"
                errors = er.get("errors", [])
                return f"✗ Execution issues: {errors[0] if errors else 'none'}"
            return "Execution completed"

        return "Completed"

    def _emit(self, session_id: str, event: dict):
        queue = self._event_queues.get(session_id)
        if queue is not None:
            queue.append(event)

    # ------------------------------------------------------------------
    # Pipeline execution
    # ------------------------------------------------------------------

    async def _stream_graph(
        self,
        session_id: str,
        graph_input,
        config: dict,
    ):
        """Run the graph via astream_events, emitting events to the session queue."""
        try:
            async for event in self._workflow.service_graph.astream_events(
                graph_input, config=config
            ):
                evt = self._format_event(event)
                if evt:
                    self._emit(session_id, evt)
        except Exception as exc:
            self._sessions[session_id]["status"] = "failed"
            self._sessions[session_id]["error"] = f"Pipeline error: {exc}"
            self._emit(session_id, {"type": "error", "message": str(exc)})
            return

        # Determine final state via checkpoint
        snap = self._workflow.service_graph.get_state(config=config)
        if snap is None:
            return

        if snap.next:
            # Graph was interrupted — awaiting approval
            self._sessions[session_id]["status"] = "awaiting_approval"
            state = self._workflow.get_service_state(config)
            if state:
                self._sessions[session_id]["state"] = state
            self._emit(
                session_id,
                {"type": "status", "status": "awaiting_approval"},
            )
        elif snap.values:
            # Graph completed
            final_state = ProvisionState.model_validate(snap.values)
            self._sessions[session_id]["status"] = "completed"
            self._sessions[session_id]["state"] = final_state
            self._sessions[session_id]["error"] = final_state.error
            self._emit(
                session_id,
                {
                    "type": "status",
                    "status": "completed",
                    "error": final_state.error,
                },
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start(
        self,
        user_request: str,
        project_name: str | None = None,
    ) -> str:
        """Start a provisioning flow and return a session_id immediately.

        The pipeline runs as a background task and emits events via SSE.
        """
        session_id = uuid.uuid4().hex
        state = ProvisionState(
            user_request=user_request,
            project_name=project_name,
        )
        state = self._prepare_workspace(state)

        self._sessions[session_id] = {
            "status": "processing",
            "thread_id": session_id,
            "error": None,
            "state": state,
            "interrupt_value": None,
        }
        self._event_queues[session_id] = deque()
        config = {"configurable": {"thread_id": session_id}}
        self._emit(session_id, {"type": "status", "status": "processing"})

        asyncio.create_task(
            self._stream_graph(session_id, state, config)
        )
        return session_id

    async def approve(
        self,
        session_id: str,
        approved: bool,
        feedback: str | None = None,
    ) -> dict:
        """Resume the pipeline with an approval decision (async, returns immediately).

        If feedback is provided, the graph loops back to the Requirement Agent
        and re-runs the pipeline. If approved, it proceeds to execution.
        The client polls GET /provision/{id} or subscribes to SSE for updates.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Session {session_id} not found")

        if session["status"] != "awaiting_approval":
            raise ValueError(
                f"Session {session_id} is not awaiting approval "
                f"(status: {session['status']})"
            )

        config = {"configurable": {"thread_id": session_id}}
        decision = {"approved": approved, "feedback": feedback}

        self._sessions[session_id]["status"] = "processing"
        self._emit(session_id, {"type": "status", "status": "processing"})

        asyncio.create_task(
            self._stream_graph(
                session_id, Command(resume=decision), config
            )
        )
        return self._sessions[session_id]

    def get_session(self, session_id: str) -> dict | None:
        """Return the session dict or None if not found."""
        return self._sessions.get(session_id)

    def get_event_queue(self, session_id: str) -> deque | None:
        """Return the SSE event deque for a session, or None."""
        return self._event_queues.get(session_id)
