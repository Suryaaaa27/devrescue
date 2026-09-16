import json
import os

from openai import OpenAI


class OpenAICompatibleClient:
    """
    Client for any OpenAI-compatible API.

    This includes:
    - Gemini Web2API
    - OpenAI
    - other OpenAI-compatible gateways
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
    ):
        self.model = model

        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> dict:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        output = response.choices[0].message.content

        if not output:
            raise ValueError(
                "LLM returned an empty response."
            )

        try:
            return json.loads(output)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "LLM returned invalid JSON."
                f"Raw LLM output:\n{output}"
            ) from exc