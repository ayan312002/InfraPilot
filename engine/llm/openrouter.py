import json

from openai import OpenAI
import os


class OpenRouterLLM:

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

        self.model = os.getenv(
            "OPENROUTER_MODEL",
            "nvidia/nemotron-3-super-120b-a12b:free",
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model=None,
    ):

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        data = json.loads(content)

        return response_model.model_validate(data)