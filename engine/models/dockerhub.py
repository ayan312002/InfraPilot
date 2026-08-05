from pydantic import BaseModel


class DockerImageTag(BaseModel):
    name: str
    last_updated: str | None = None
    
class DockerImageResult(BaseModel):
    repository: str
    description: str | None = None
    is_official: bool = False
    star_count: int = 0
    tags: list[DockerImageTag]


class DockerHubSearchResult(BaseModel):
    query: str
    results: list[DockerImageResult]