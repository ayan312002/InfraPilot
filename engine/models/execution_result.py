from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    success: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    container_id: str | None = None