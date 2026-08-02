from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    success: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)