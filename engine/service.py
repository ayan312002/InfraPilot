import asyncio
import uuid
from collections import deque
from pathlib import Path

from langgraph.types import Command

from engine.graph.workflow import InfraPilotWorkflow
from engine.mock.registry import MockRegistry
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
            return f"Parsed {len(services) if services else 0} service(s): {', '.join(names)}"

        if node == "image_fetch":
            spec = obj.get("provision_spec") or {}
            services = spec.get("services", []) if isinstance(spec, dict) else []
            if services:
                images = [f'{s.get("name","?")}:{s.get("image","")}' for s in services]
                return f"Resolved images: {', '.join(images)}"
            return "Images resolved"

        if node == "generate":
            config = obj.get("generated_config", "")
            if config:
                lines = config.split("\n")
                return f"docker-compose.yml ({len(lines)} lines)\n" + "\n".join(lines)
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
    # Mock pipeline simulation
    # ------------------------------------------------------------------

    async def _stream_mock(
        self,
        session_id: str,
        example_id: str,
        state: ProvisionState,
    ) -> None:
        """Simulate the pipeline using pre-saved mock data.

        Emits the same SSE event sequence as the real pipeline
        (agent_start/agent_end for each step, then an interrupt) so the
        frontend timeline animates naturally.  No LLM, Docker Hub, or
        Docker execution calls are made.
        """
        mock_state = MockRegistry.get_mock(example_id)
        if mock_state is None:
            return

        # Copy pipeline outputs from the mock into the session state.
        state.provision_spec = mock_state.provision_spec
        state.generated_config = mock_state.generated_config
        state.generated_config_path = state.output_dir / "docker-compose.yml"
        state.validation_result = mock_state.validation_result
        state.docker_search_results = mock_state.docker_search_results

        # Persist files to disk so the output mirrors a real run.
        (state.output_dir / "docker-compose.yml").write_text(
            state.generated_config or ""
        )
        if state.provision_spec:
            (state.output_dir / "spec.json").write_text(
                state.provision_spec.model_dump_json(indent=2)
            )
        if state.validation_result:
            (state.output_dir / "validation.json").write_text(
                state.validation_result.model_dump_json(indent=2)
            )

        state_dump = state.model_dump()

        pipeline_steps = [
            ("requirement", NODE_AGENT_MAP["requirement"]),
            ("image_fetch", NODE_AGENT_MAP["image_fetch"]),
            ("generate", NODE_AGENT_MAP["generate"]),
            ("validate", NODE_AGENT_MAP["validate"]),
        ]

        for i, (node, agent_name) in enumerate(pipeline_steps):
            delay = 0.5 if i > 0 else 0.3
            await asyncio.sleep(delay)
            self._emit(
                session_id,
                {"type": "agent_start", "agent": agent_name, "node": node},
            )
            await asyncio.sleep(5)
            output = self._extract_agent_output(node, state_dump)
            self._emit(
                session_id,
                {
                    "type": "agent_end",
                    "agent": agent_name,
                    "node": node,
                    "output": output,
                },
            )

        # Build interrupt value (mirrors _service_approval_node).
        interrupt_value = {
            "generated_config": state.generated_config,
            "validation_success": (
                state.validation_result.success if state.validation_result else None
            ),
            "validation_errors": (
                state.validation_result.errors if state.validation_result else []
            ),
            "provision_spec": (
                state.provision_spec.model_dump() if state.provision_spec else None
            ),
        }
        self._emit(session_id, {"type": "interrupt", "value": interrupt_value})

        # Update session — now awaiting approval.
        self._sessions[session_id]["state"] = state
        self._sessions[session_id]["status"] = "awaiting_approval"
        self._sessions[session_id]["interrupt_value"] = interrupt_value
        self._emit(
            session_id, {"type": "status", "status": "awaiting_approval"}
        )

    async def _stream_mock_approval(
        self,
        session_id: str,
        example_id: str,
    ) -> None:
        """Complete a mock pipeline after the user approves the review."""
        mock_state = MockRegistry.get_mock(example_id)
        session = self._sessions[session_id]
        state = session["state"]

        # Simulated executor step.
        self._emit(
            session_id,
            {
                "type": "agent_start",
                "agent": NODE_AGENT_MAP["execute"],
                "node": "execute",
            },
        )
        await asyncio.sleep(0.5)
        state_dump = mock_state.model_dump()
        output = self._extract_agent_output("execute", state_dump)
        self._emit(
            session_id,
            {
                "type": "agent_end",
                "agent": NODE_AGENT_MAP["execute"],
                "node": "execute",
                "output": output,
            },
        )

        # Populate final state.
        state.approved = True
        state.execution_result = mock_state.execution_result
        state.status = "completed"

        session["state"] = state
        session["status"] = "completed"
        session["error"] = None
        self._emit(
            session_id,
            {"type": "status", "status": "completed", "error": None},
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start(
        self,
        user_request: str,
        project_name: str | None = None,
        example_id: str | None = None,
    ) -> str:
        """Start a provisioning flow and return a session_id immediately.

        If *example_id* maps to a pre-saved mock entry in :class:`MockRegistry`,
        a simulated pipeline is run instead of the real workflow.  The client
        observes the same SSE event sequence (agent_start/agent_end, interrupt,
        status updates) as a real run, but no LLM, Docker Hub, or Docker calls
        are made.
        """
        session_id = uuid.uuid4().hex
        state = ProvisionState(
            user_request=user_request,
            project_name=project_name,
        )
        state = self._prepare_workspace(state)

        is_mock = example_id is not None and MockRegistry.has_mock(example_id)

        self._sessions[session_id] = {
            "status": "processing",
            "thread_id": session_id,
            "error": None,
            "state": state,
            "interrupt_value": None,
            "is_mock": is_mock,
            "example_id": example_id if is_mock else None,
        }
        self._event_queues[session_id] = deque()
        self._emit(session_id, {"type": "status", "status": "processing"})

        if is_mock:
            asyncio.create_task(
                self._stream_mock(session_id, example_id, state)
            )
        else:
            config = {"configurable": {"thread_id": session_id}}
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

        # --- Mock path — skip real graph, replay pre-saved execution ---
        if session.get("is_mock"):
            self._sessions[session_id]["status"] = "processing"
            self._emit(session_id, {"type": "status", "status": "processing"})

            if approved:
                asyncio.create_task(
                    self._stream_mock_approval(
                        session_id, session.get("example_id")
                    )
                )
            elif feedback:
                # Regenerate: re-run the mock pipeline from scratch.
                asyncio.create_task(
                    self._stream_mock(
                        session_id,
                        session.get("example_id"),
                        session["state"],
                    )
                )
            else:
                # Cancel.
                self._sessions[session_id]["status"] = "completed"
                self._emit(
                    session_id,
                    {"type": "status", "status": "completed", "error": None},
                )
            return self._sessions[session_id]

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
