from pydantic import BaseModel
from engine.models.service_spec import ServiceSpec

class ProvisioningSpec(BaseModel):
    project_name: str
    services: list[ServiceSpec]
    # networks: list[NetworkSpec] = []
    # volumes: list[VolumeSpec] = []