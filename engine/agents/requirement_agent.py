import json

from engine.llm.factory import LLMFactory
from engine.models.provision_state import ProvisionState
from engine.models.provisioning_spec import ProvisioningSpec
from engine.utils.prompt_loader import PromptLoader


class RequirementAgent:

    def __init__(self):
        self.llm = LLMFactory.create()
    
    def _build_system_prompt(self):
        template = PromptLoader.load("requirement/system.txt")
        schema = json.dumps(
            ProvisioningSpec.model_json_schema(),
            indent=2
        )

        return template.format(schema=schema)

    def _build_user_prompt(self, state: ProvisionState) -> str:
        if self._is_validation_retry(state):
            return self._validation_prompt(state)

        if state.feedback:
            return self._feedback_prompt(state)

        return self._initial_prompt(state)

    def _initial_prompt(self, state: ProvisionState) -> str:
        template = PromptLoader.load("requirement/initial.txt")
        return template.format(user_request=state.user_request)
        
    def _feedback_prompt(self, state: ProvisionState) -> str:
        template = PromptLoader.load("requirement/feedback.txt")
        return template.format(
            user_request=state.user_request, 
            provision_spec=state.provision_spec.model_dump_json(indent=2),
            feedback=state.feedback
        )
    
    def _validation_prompt(self, state: ProvisionState) -> str:
        template = PromptLoader.load("requirement/validation.txt")
        return template.format(
            user_request=state.user_request,
            provision_spec=state.provision_spec.model_dump_json(indent=2),
            validation_errors="\n".join(state.validation_result.errors),
        )

    def _is_validation_retry(self, state: ProvisionState) -> bool:
        return (
            state.validation_result is not None
            and not state.validation_result.success
        )

    def generate_spec(self, state: ProvisionState) -> ProvisionState:

        spec = self.llm.generate(
            system_prompt=self._build_system_prompt(),
            user_prompt=self._build_user_prompt(state),
            response_model=ProvisioningSpec,
        )

        state.provision_spec = spec

        self.save_spec_output(state)

        return state

    def save_spec_output(self, state):
        output_file = (state.output_dir / "spec.json")
        output_file.write_text(state.provision_spec.model_dump_json(indent=2))

        return True