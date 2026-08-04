import json

from openai import OpenAI
import os

from dataclasses import dataclass
from typing import Callable

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    func: Callable


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
        tools=None,
    ):

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        tool_map = {t.name: t for t in (tools or [])}

        MAX_ITERATIONS = 10

        #
        # Tool loop
        #
        for _ in range(MAX_ITERATIONS):

            kwargs = {
                "model": self.model,
                "messages": messages,
            }

            if tools:
                kwargs["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters,
                        },
                    }
                    for tool in tools
                ]
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)

            choice = response.choices[0]
            message = choice.message

            print("finish_reason:", choice.finish_reason)
            print("tool_calls:", message.tool_calls)
            print("content:", message.content)

            #
            # Execute tools
            #
            if choice.finish_reason == "tool_calls":

                messages.append(message)

                for tool_call in message.tool_calls:

                    tool = tool_map[tool_call.function.name]

                    args = json.loads(tool_call.function.arguments)

                    result = tool.func(**args)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result),
                        }
                    )

                continue

            #
            # Model is done reasoning
            #
            messages.append(message)
            break

        else:
            raise RuntimeError("Maximum tool iterations reached.")

        #
        # No structured output requested
        #
        if response_model is None:
            return message.content

        #
        # Final formatting pass
        #
        messages.append(
            {
                "role": "user",
                "content": (
                    "Return ONLY valid JSON matching this schema. "
                    "Do not explain your reasoning. "
                    "Do not call any more tools."
                ),
            }
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": response_model.__name__,
                    "schema": response_model.model_json_schema(),
                },
            },
        )

        return response_model.model_validate_json(
            response.choices[0].message.content
        )