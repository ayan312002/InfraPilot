import json

from openai import OpenAI

from engine.llm.factory import LLMFactory
from engine.models.provision_state import ProvisionState
from engine.models.provisioning_spec import ProvisioningSpec
from engine.utils.prompt_loader import PromptLoader


class RequirementAgent:

    def __init__(self):
        self.llm = LLMFactory.create()
        self.system_prompt = PromptLoader.load("requirement_prompt.txt")

    def generate_spec(self, state: ProvisionState) -> ProvisionState:

        schema = json.dumps(
            ProvisioningSpec.model_json_schema(),
            indent=2
        )

        self.system_prompt += f"""

        Return JSON that conforms to this schema:

        {schema}
        """
        
        spec = self.llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=state.user_request,
            response_model=ProvisioningSpec,
        )

        state.provision_spec = spec
        
        self.save_spec_output(state)

        return state

    def save_spec_output(self, state):
        output_file = (state.output_dir / "spec.json")
        output_file.write_text(state.provision_spec.model_dump_json(indent=2))

        return True
        