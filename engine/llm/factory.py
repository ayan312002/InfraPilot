import os

from engine.llm.openrouter import OpenRouterLLM


class LLMFactory:

    @staticmethod
    def create():

        provider = os.getenv("LLM_PROVIDER", "openrouter")

        if provider == "openrouter":
            return OpenRouterLLM()

        raise ValueError(f"Unknown provider: {provider}")