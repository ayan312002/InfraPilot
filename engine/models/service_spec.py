from pydantic import BaseModel, Field

class ServiceSpec(BaseModel):
    name: str
    image: str | None = None
    container_name: str | None = None

    ports: list[str] = Field(default_factory=list)
    environment: dict[str, str] = Field(default_factory=dict)
    volumes: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)