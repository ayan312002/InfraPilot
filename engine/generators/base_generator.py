from abc import ABC, abstractmethod

from engine.models.provisioning_spec import ProvisioningSpec

class BaseGenerator(ABC):

    @abstractmethod
    def generate(self, spec: ProvisioningSpec):
        """Generated infra config."""
        pass