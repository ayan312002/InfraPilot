import json
import os

from openai import OpenAI


class GeminiLLM:

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash",
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

            messages.append(message)
            break

        else:
            raise RuntimeError("Maximum tool iterations reached.")

        if response_model is None:
            return message.content

        messages.append(
            {
                "role": "user",
                "content": (
                    "Return ONLY valid JSON matching the requested schema. "
                    "Do not explain anything. "
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