from abc import ABC, abstractmethod
from typing import Type

from pydantic import BaseModel


class BaseLLM(ABC):

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None = None,
    ):
        pass
    
    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str) -> str:
        pass