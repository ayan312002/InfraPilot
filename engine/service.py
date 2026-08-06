import asyncio
import uuid
from pathlib import Path

from langgraph.types import Command

from engine.graph.workflow import InfraPilotWorkflow
from engine.models.provision_state import ProvisionState


class ProvisionService:
    """Service layer for running InfraPilot provisioning as a REST API.

    Uses LangGraph checkpointing to pause at the human-in-the-loop approval
    step and resume when the client submits a decision.
    """

    def __init__(self):
        self._workflow = InfraPilotWorkflow()
        self._sessions: dict[str, dict] = {}

    @staticmethod
    def _prepare_workspace(state: ProvisionState) -> ProvisionState:
        if state.project_name is None:
            state.project_name = uuid.uuid4().hex[:6]

        state.output_dir = Path("generated") / state.project_name
        state.output_dir.mkdir(parents=True, exist_ok=True)

        (state.output_dir / "request.txt").write_text(state.user_request)

        return state

    async def start(
        self,
        user_request: str,
        project_name: str | None = None,
    ) -> str:
        """Start a provisioning flow and return a session_id immediately.

        The pipeline runs in a background task up to the approval interrupt.
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

        asyncio.create_task(self._run_pipeline(session_id, state))
        return session_id

    async def _run_pipeline(
        self,
        session_id: str,
        state: ProvisionState,
    ):
        config = {"configurable": {"thread_id": session_id}}
        try:
            result = await asyncio.to_thread(
                self._workflow.run_service, state, config
            )
        except Exception as exc:
            self._sessions[session_id]["status"] = "failed"
            self._sessions[session_id]["error"] = f"Pipeline error: {exc}"
            return

        self._resolve_result(session_id, result, config)

    def _resolve_result(
        self,
        session_id: str,
        result: dict,
        config: dict,
    ):
        """Store the outcome of a graph invoke — interrupt or completion."""
        if isinstance(result, dict) and "__interrupt__" in result:
            self._sessions[session_id]["status"] = "awaiting_approval"
            checkpoint_state = self._workflow.get_service_state(config)
            if checkpoint_state is not None:
                self._sessions[session_id]["state"] = checkpoint_state
            interrupt_value = result["__interrupt__"][0].value
            self._sessions[session_id]["interrupt_value"] = interrupt_value
        else:
            final_state = ProvisionState.model_validate(result)
            self._sessions[session_id]["status"] = "completed"
            self._sessions[session_id]["state"] = final_state
            self._sessions[session_id]["error"] = final_state.error

    async def approve(
        self,
        session_id: str,
        approved: bool,
        feedback: str | None = None,
    ) -> dict:
        """Resume the pipeline with an approval decision.

        The graph may complete (approved → execute → END) or hit another
        interrupt if the user provided feedback (approval_router → requirement).
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

        result = await asyncio.to_thread(
            self._workflow.resume_service,
            Command(resume=decision),
            config,
        )

        self._resolve_result(session_id, result, config)
        return self._sessions[session_id]

    def get_session(self, session_id: str) -> dict | None:
        """Return the session dict or None if not found."""
        return self._sessions.get(session_id)
