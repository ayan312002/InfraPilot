from pydantic import BaseModel, Field
from engine.models.provisioning_spec import ProvisioningSpec

class ProvisionState(BaseModel):
    user_request: str

    provision_spec: ProvisioningSpec | None = None

    compose_yaml: str | None = None

    validation_passed: bool = False
    validation_errors: list[str] = Field(default_factory=list)

    execution_logs: list[str] = Field(default_factory=list)