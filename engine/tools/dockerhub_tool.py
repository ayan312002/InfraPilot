from dataclasses import dataclass
import requests

from engine.models.dockerhub import DockerHubSearchResult, DockerImageResult, DockerImageTag


import requests


class DockerHubTool:

    BASE_URL = "https://hub.docker.com/v2"

    MAX_REPOSITORIES = 5
    MAX_TAGS = 100

    @staticmethod
    def _is_useful_tag(tag: str) -> bool:
        tag = tag.lower()

        ignored = (
            "sha",
            "rc",
            "beta",
            "alpha",
            "dev",
            "nightly",
            "test",
        )

        return not any(x in tag for x in ignored)

    def search_repository(self, query: str) -> list[dict]:
        """
        Search Docker Hub repositories.
        Returns lightweight repository information.
        """

        response = requests.get(
            f"{self.BASE_URL}/search/repositories",
            params={
                "query": query,
                "page_size": self.MAX_REPOSITORIES,
            },
            timeout=10,
        )

        response.raise_for_status()
        repositories = []

        for repo in response.json()["results"]:

            repo_name = repo["repo_name"]

            # Docker Hub search returns "postgres" for official images.
            # Normalize to the canonical repository path.
            if repo.get("repo_owner") == "library" and "/" not in repo_name:
                repo_name = f"library/{repo_name}"

            repositories.append(
                {
                    "repository": repo_name,
                    "description": repo.get("short_description"),
                    "is_official": repo.get("repo_owner") == "library",
                    "star_count": repo.get("star_count", 0),
                    "pull_count": repo.get("pull_count", 0),
                }
            )

        return repositories

    def list_tags(self, repository: str) -> list[dict]:
        """
        Returns the newest useful tags for a repository.
        """

        # Handle official Docker images
        if "/" not in repository:
            repository = f"library/{repository}"

        response = requests.get(
            f"{self.BASE_URL}/repositories/{repository}/tags",
            params={
                "page_size": self.MAX_TAGS,
            },
            timeout=10,
        )

        response.raise_for_status()

        tags = []

        for tag in response.json()["results"]:

            if not self._is_useful_tag(tag["name"]):
                continue

            tags.append(
                {
                    "name": tag["name"],
                    "last_updated": tag.get("last_updated"),
                }
            )

        tags.sort(
            key=lambda t: t["last_updated"] or "",
            reverse=True,
        )

        return tags