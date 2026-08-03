from engine.agents.approval_agent import ApprovalManager
from engine.agents.executor_agent import ExecutorAgent
from engine.agents.requirement_agent import RequirementAgent
from engine.generators.compose_generator import ComposeGenerator
from engine.models.provision_state import ProvisionState
from engine.validators.compose_validator import ComposeValidator

from langgraph.graph import StateGraph, END, START

class InfraPilotWorkflow:
    def __init__(self):
        self._requirement = RequirementAgent()
        self._generator = ComposeGenerator()
        self._validator = ComposeValidator()
        self._approval = ApprovalManager()
        self._executor = ExecutorAgent()

        self._graph = self._build()


    def _build(self):
        def requirement_node(state: ProvisionState) -> ProvisionState:
            return self._requirement.generate_spec(state)

        def generate_node(state: ProvisionState) -> ProvisionState:
            return self._generator.generate(state)

        def validate_node(state: ProvisionState) -> ProvisionState:
            return self._validator.validate(state)

        def approval_node(state: ProvisionState) -> ProvisionState:
            return self._approval.review(state)

        def execute_node(state: ProvisionState) -> ProvisionState:
            return self._executor.execute(state)

        def validation_router(state: ProvisionState):
            if state.validation_result.success:
                return "approval"

            return END

        def approval_router(state: ProvisionState):
            if state.approved:
                return "execute"

            if state.feedback:
                return "requirement"

            return END
        
        workflow = StateGraph(ProvisionState)

        workflow.add_node("requirement", requirement_node)
        workflow.add_node("generate", generate_node)
        workflow.add_node("validate", validate_node)
        workflow.add_node("approval", approval_node)
        workflow.add_node("execute", execute_node)

        workflow.add_edge(START, "requirement")

        workflow.add_edge("requirement", "generate")
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
        return workflow.compile()

    def run(
        self,
        state: ProvisionState
    ) -> ProvisionState:
        return ProvisionState.model_validate(self._graph.invoke(state))