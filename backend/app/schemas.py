from pydantic import BaseModel, Field, field_validator

TAG_PATTERN = r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$"


class EntryCreate(BaseModel):
    text: str = Field(..., description="Raw text submitted by the user")


class AIResult(BaseModel):
    """Normalised shape of what we expect back from the LLM."""

    summary: str
    tags: list[str]

    @field_validator("summary")
    @classmethod
    def summary_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("summary must not be empty")
        return value.strip()

    @field_validator("tags")
    @classmethod
    def exactly_three_valid_tags(cls, value: list[str]) -> list[str]:
        cleaned = [tag.strip() for tag in value]
        if any(not tag for tag in cleaned):
            raise ValueError("tags must not contain empty strings")
        if len(cleaned) != 3:
            raise ValueError(f"expected exactly 3 tags, got {len(cleaned)}")
        return cleaned


class EntryOut(BaseModel):
    id: int
    original_text: str
    summary: str
    tags: list[str]
    created_at: str
