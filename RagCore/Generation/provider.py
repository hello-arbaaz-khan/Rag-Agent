import os
from typing import Protocol

from groq import Groq

from RagCore.Generation.generation import (
    GenerationConfig,
)


class GenerationProvider(Protocol):
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        ...


class GroqProvider:

    def __init__(
        self,
        config: GenerationConfig | None = None,
    ) -> None:
        self.config = (
            config
            or GenerationConfig()
        )

        self.client = Groq(
            api_key=os.getenv(
                "GROQ_API_KEY"
            ),
        )

    def _request(
        self,
        system_prompt: str,
        user_prompt: str,
    ):
        return (
            self.client.chat.completions.create(
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
                max_completion_tokens=(
                    self.config.max_tokens
                ),
            )
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        response = self._request(
            system_prompt,
            user_prompt,
        )

        message = response.choices[0].message

        content = message.content

        if (
            isinstance(content, str)
            and content.strip()
        ):
            return content.strip()

        # Never expose provider reasoning
        # as the user-facing answer.
        #
        # Retry once if the provider returned
        # an empty final content field.
        response = self._request(
            system_prompt,
            user_prompt,
        )

        message = response.choices[0].message

        content = message.content

        if (
            not isinstance(content, str)
            or not content.strip()
        ):
            raise ValueError(
                "Generation provider returned "
                "an empty final response."
            )

        return content.strip()