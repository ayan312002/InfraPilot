from engine.agents.approval_agent import ApprovalManager
from engine.agents.executor_agent import ExecutorAgent
from engine.agents.image_fetcher_agent import ImageFetcherAgent
from engine.agents.requirement_agent import RequirementAgent
from engine.generators.compose_generator import ComposeGenerator
from engine.models.provision_state import ProvisionState
from engine.validators.compose_validator import ComposeValidator

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt

from ui.progress import PipelineProgress

class InfraPilotWorkflow:
    def __init__(self):
        self._requirement = RequirementAgent()
        self._image_fetcher = ImageFetcherAgent()
        self._generator = ComposeGenerator()
        self._validator = ComposeValidator()
        self._approval = ApprovalManager()
        self._executor = ExecutorAgent()

        self._graph = self._build()
        self._checkpointer = InMemorySaver()
        self._service_graph = None
        self._progress = None

    def set_progress(self, progress: PipelineProgress):
        self._progress = progress

    def _step(self, text: str):
        if self._progress:
            self._progress.step(text)

    def _build(self):
        """Build the CLI graph — no checkpointer, input()-based approval."""
        return self._build_graph(
            approval_node_fn=self._cli_approval_node,
            checkpointer=None,
        )

    def _cli_approval_node(self, state: ProvisionState) -> ProvisionState:
        self._step("Approval")
        with self._progress.suspend():
            return self._approval.review(state)

    def _service_approval_node(self, state: ProvisionState) -> ProvisionState:
        self._step("Approval")
        decision = interrupt({
            "generated_config": state.generated_config,
            "validation_success": (
                state.validation_result.success
                if state.validation_result
                else None
            ),
            "validation_errors": (
                state.validation_result.errors
                if state.validation_result
                else []
            ),
            "provision_spec": (
                state.provision_spec.model_dump()
                if state.provision_spec
                else None
            ),
        })
        state.approved = decision["approved"]
        state.feedback = decision.get("feedback")
        return state

    def build_service_graph(self, checkpointer: InMemorySaver):
        """Build a checkpointed graph with interrupt-based approval for the service layer."""
        return self._build_graph(
            approval_node_fn=self._service_approval_node,
            checkpointer=checkpointer,
        )

    def _build_graph(self, approval_node_fn, checkpointer=None):
        def requirement_node(state: ProvisionState) -> ProvisionState:
            self._step("Requirement Agent")
            state.retry_count += 1
            return self._requirement.generate_spec(state)

        def generate_node(state: ProvisionState) -> ProvisionState:
            self._step("Compose Generator")
            return self._generator.generate(state)

        def image_fetch_node(state: ProvisionState) -> ProvisionState:
            self._step("Image Fetcher Agent")
            return self._image_fetcher.enrich_spec(state)

        def validate_node(state: ProvisionState) -> ProvisionState:
            self._step("Compose Validator")
            return self._validator.validate(state)

        def execute_node(state: ProvisionState) -> ProvisionState:
            self._step("Executor")
            return self._executor.execute(state)

        def validation_router(state: ProvisionState):
            MAX_RETRIES = 3
            if state.validation_result.success:
                return "approval"

            if state.retry_count < MAX_RETRIES:
                state.retry_count += 1
                return "requirement"

            state.error = (
                f"Validation failed after {MAX_RETRIES} attempts."
            )
            return END

        def approval_router(state: ProvisionState):
            if state.approved:
                return "execute"

            if state.feedback:
                return "requirement"

            return END

        workflow = StateGraph(ProvisionState)

        workflow.add_node("requirement", requirement_node)
        workflow.add_node("image_fetch", image_fetch_node)
        workflow.add_node("generate", generate_node)
        workflow.add_node("validate", validate_node)
        workflow.add_node("approval", approval_node_fn)
        workflow.add_node("execute", execute_node)

        workflow.add_edge(START, "requirement")

        workflow.add_edge("requirement", "image_fetch")
        workflow.add_edge("image_fetch", "generate")
        workflow.add_edge("generate", "validate")

        workflow.add_conditional_edges(
            "validate",
            validation_router,
        )

        workflow.add_conditional_edges(
            "approval",
            approval_router,
        )

        workflow.add_edge("execute", END)

        if checkpointer:
            return workflow.compile(checkpointer=checkpointer)
        return workflow.compile()

    def run(
        self,
        state: ProvisionState
    ) -> ProvisionState:
        return ProvisionState.model_validate(self._graph.invoke(state))

    def run_service(
        self,
        state: ProvisionState,
        config: dict,
    ) -> ProvisionState | dict:
        """Invoke the service graph and return raw result dict (may contain __interrupt__)."""
        return self.service_graph.invoke(state, config=config)

    def get_service_state(self, config: dict) -> ProvisionState | None:
        """Retrieve the current checkpoint state for a thread."""
        snapshot = self.service_graph.get_state(config=config)
        if snapshot is None or snapshot.values is None:
            return None
        return ProvisionState.model_validate(snapshot.values)

    def resume_service(self, command, config: dict) -> ProvisionState | dict:
        """Resume an interrupted service graph with a Command."""
        return self.service_graph.invoke(command, config=config)

    @property
    def service_graph(self):
        if self._service_graph is None:
            self._service_graph = self.build_service_graph(self._checkpointer)
        return self._service_graph
