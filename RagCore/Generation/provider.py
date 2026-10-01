import os
from typing import Protocol

from groq import Groq

from RagCore.Generation.generation import GenerationConfig


class GenerationProvider(Protocol):
    def generate(self,system_prompt: str,user_prompt: str) -> str:
        ...


class GroqProvider:
    def __init__(self, config: GenerationConfig | None = None) -> None:
        self.config = config or GenerationConfig()
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY"),
        )


    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        response = self.client.chat.completions.create(
            model=self.config.model,
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
            temperature=self.config.temperature,
            max_completion_tokens=self.config.max_tokens,
        )

        message = response.choices[0].message
        content = message.content

        if not isinstance(content, str) or not content.strip():
            reasoning = getattr(message, "reasoning", None)
            if isinstance(reasoning, str) and reasoning.strip():
                content = reasoning.strip()

        if not isinstance(content, str) or not content.strip():
            # Retry once in case of transient empty response
            response = self.client.chat.completions.create(
                model=self.config.model,
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
                temperature=self.config.temperature,
                max_completion_tokens=self.config.max_tokens,
            )
            message = response.choices[0].message
            content = message.content
            if not isinstance(content, str) or not content.strip():
                reasoning = getattr(message, "reasoning", None)
                if isinstance(reasoning, str) and reasoning.strip():
                    content = reasoning.strip()

        if not isinstance(content, str) or not content.strip():
            raise ValueError(
                "Generation provider returned an empty response."
            )

        return content.strip()