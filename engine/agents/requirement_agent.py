import json

from openai import OpenAI

from engine.llm.factory import LLMFactory
from engine.models.provisioning_spec import ProvisioningSpec
from engine.utils.prompt_loader import PromptLoader


class RequirementAgent:

    def __init__(self):
        self.llm = LLMFactory.create()
        self.system_prompt = PromptLoader.load("requirement_prompt.txt")

    def generate_spec(self, request: str) -> ProvisioningSpec:

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
            user_prompt=request,
            response_model=ProvisioningSpec,
        )
        return spec