from pydantic import BaseModel, Field, field_validator


class EvaluationSample(BaseModel):
    query: str = Field(min_length=1)
    relevant_chunk_ids: list[str] = Field(min_length=1)
    reference_answer: str | None = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Evaluation query cannot be empty."
            )

        return value

    @field_validator("relevant_chunk_ids")
    @classmethod
    def validate_relevant_chunk_ids(
        cls,
        value: list[str],
    ) -> list[str]:
        if not value:
            raise ValueError(
                "Evaluation sample must contain relevant chunk IDs."
            )

        cleaned_ids = []
        seen_ids = set()

        for chunk_id in value:
            if not isinstance(chunk_id, str):
                raise ValueError(
                    "Relevant chunk IDs must be strings."
                )

            chunk_id = chunk_id.strip()

            if not chunk_id:
                raise ValueError(
                    "Relevant chunk IDs cannot be empty."
                )

            if chunk_id not in seen_ids:
                cleaned_ids.append(chunk_id)
                seen_ids.add(chunk_id)

        if not cleaned_ids:
            raise ValueError(
                "Evaluation sample must contain relevant chunk IDs."
            )

        return cleaned_ids

    @field_validator("reference_answer")
    @classmethod
    def validate_reference_answer(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class EvaluationDataset(BaseModel):
    samples: list[EvaluationSample] = Field(
        default_factory=list,
    )

    def validate_non_empty(self) -> None:
        if not self.samples:
            raise ValueError(
                "Evaluation dataset cannot be empty."
            )