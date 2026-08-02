import json
from pathlib import Path

from engine.models.provisioning_spec import ProvisioningSpec


class SpecLoader:

    @staticmethod
    def load(path: str) -> ProvisioningSpec:

        data = json.loads(Path(path).read_text())

        return ProvisioningSpec.model_validate(data)