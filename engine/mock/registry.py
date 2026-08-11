import json
from pathlib import Path

from engine.models.provision_state import ProvisionState


class MockRegistry:
    """Registry of pre-saved pipeline results for example prompts.

    Each JSON file in ``data/`` is keyed by example_id and contains a
    serialized :class:`ProvisionState` representing a complete, happy-path
    pipeline run.  The service layer intercepts requests that carry a known
    ``example_id`` and replays the recorded state instead of invoking the
    real LLM / Docker / execution stack.
    """

    _data_dir = Path(__file__).parent / "data"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def available_mocks(cls) -> list[str]:
        """Return a sorted list of available mock example IDs."""
        return sorted(f.stem for f in cls._data_dir.glob("*.json"))

    @classmethod
    def has_mock(cls, example_id: str) -> bool:
        """Check whether a mock exists for *example_id*."""
        return example_id in cls.available_mocks()

    @classmethod
    def get_mock(cls, example_id: str) -> ProvisionState | None:
        """Load and return the :class:`ProvisionState` for *example_id*.

        Returns ``None`` when no mock is registered for the given ID.
        """
        if not cls.has_mock(example_id):
            return None

        path = cls._data_dir / f"{example_id}.json"
        data = json.loads(path.read_text())
        return ProvisionState.model_validate(data)
