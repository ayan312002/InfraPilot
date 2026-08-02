from pydantic import BaseModel
from engine.models.service_spec import ServiceSpec

class ProvisioningSpec(BaseModel):
    services: list[ServiceSpec]
    # networks: list[NetworkSpec] = []
    # volumes: list[VolumeSpec] = []