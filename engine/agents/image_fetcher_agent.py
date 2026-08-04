import json

from engine.llm.factory import LLMFactory
from engine.llm.openrouter import Tool
from engine.models.provision_state import ProvisionState
from engine.models.provisioning_spec import ProvisioningSpec
from engine.utils.prompt_loader import PromptLoader
from engine.tools.dockerhub_tool import DockerHubTool


class ImageFetcherAgent:

    def __init__(self):
        self.llm = LLMFactory.create()
        self.system_prompt = PromptLoader.load(
            "image_fetcher_prompt.txt"
        )

        docker = DockerHubTool()

        self.tools = [
            Tool(
                name="search_repository",
                description="Search Docker Hub repositories.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string"
                        }
                    },
                    "required": ["query"],
                },
                func=docker.search_repository,
            ),
            Tool(
                name="list_tags",
                description="List Docker tags.",
                parameters={
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string"
                        }
                    },
                    "required": ["repository"],
                },
                func=docker.list_tags,
            ),
        ]

    def enrich_spec(self, state: ProvisionState):

        schema = json.dumps(
            ProvisioningSpec.model_json_schema(),
            indent=2,
        )

        system_prompt = self.system_prompt + f"""

Return JSON conforming to:

{schema}

You have access to Docker Hub tools.

Resolve every service image.

Only modify image fields.

Prefer stable releases.

Do not use beta/rc/nightly tags unless explicitly requested.
"""

        prompt = f"""
User Request:

{state.user_request}

Current Spec:

{state.provision_spec.model_dump_json(indent=2)}
"""

        updated = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=prompt,
            response_model=ProvisioningSpec,
            tools=self.tools,
        )

        state.provision_spec = updated

        return state