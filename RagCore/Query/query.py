from pydantic import BaseModel, Field

class Query(BaseModel):
    text: str = Field(min_length=1)

    def normalize_text(self) -> str:
        return self.text.strip()