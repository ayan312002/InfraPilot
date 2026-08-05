import os

from engine.llm.gemini import GeminiLLM
from engine.llm.openrouter import OpenRouterLLM


class LLMFactory:

    @staticmethod
    def create():

        provider = os.getenv("LLM_PROVIDER", "openrouter")

        if provider == "openrouter":
            return OpenRouterLLM()

        if provider == "gemini":
            return GeminiLLM()

        raise ValueError(f"Unknown provider: {provider}")