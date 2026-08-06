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
        self.docker_tool = DockerHubTool()
        self.tools = self._build_tools()

    def _build_tools(self):
        return [
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
                func=self.docker_tool.search_repository,
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
                func=self.docker_tool.list_tags,
            ),
        ]

    def _build_system_prompt(self):
        template = PromptLoader.load("image_fetcher/system.txt")
        schema = json.dumps(
            ProvisioningSpec.model_json_schema(),
            indent=2
        )

        return template.format(schema=schema)

    def _build_user_prompt(self, state):
        template = PromptLoader.load("image_fetcher/initial.txt")

        return template.format(
            user_request=state.user_request,
            current_spec=state.provision_spec.model_dump_json(indent=2)
        )
    
    def enrich_spec(self, state: ProvisionState):
        updated = self.llm.generate(
            system_prompt= self._build_system_prompt(),
            user_prompt= self._build_user_prompt(state),
            response_model=ProvisioningSpec,
            tools=self.tools,
        )

        state.provision_spec = updated

        return state