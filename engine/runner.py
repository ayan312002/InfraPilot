from pathlib import Path
import uuid

from engine.agents.approval_agent import ApprovalManager
from engine.agents.executor_agent import ExecutorAgent
from engine.agents.requirement_agent import RequirementAgent
from engine.generators.compose_generator import ComposeGenerator
from engine.models.provision_state import ProvisionState
from engine.validators.compose_validator import ComposeValidator


class ProvisionRunner:

    def __init__(self):
        self.requirement = RequirementAgent()
        self.generator = ComposeGenerator()
        self.validator = ComposeValidator()
        self.approval = ApprovalManager()
        self.executor = ExecutorAgent()

    def run(self, state: ProvisionState) -> ProvisionState:

        if state.project_name is None:
            state.project_name = uuid.uuid4().hex[:6]

        state.output_dir = Path("generated") / state.project_name
        state.output_dir.mkdir(parents=True, exist_ok=True)

        state = self.requirement.generate_spec(state)

        state = self.generator.generate(state)
        state = self.generator.save(state)

        state = self.validator.validate(state)

        if not state.validation_result.success:
            state = self.save_artifacts(state)
            return state

        state = self.save_outputs(state)

        state = self.approval.review(state)
        
        if not state.approved:
            return state

        state = self.executor.execute(state)
        return state

    def save_outputs(self, state):
        (state.output_dir / "request.txt").write_text(
                    state.user_request
        )
        
        (state.output_dir / "spec.json").write_text(
            state.provision_spec.model_dump_json(indent=2)
        )

        (state.output_dir / "validation.json").write_text(
            state.validation_result.model_dump_json(indent=2)
        )

        return state