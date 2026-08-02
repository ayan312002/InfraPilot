from pydantic import BaseModel, Field
from engine.models.provisioning_spec import ProvisioningSpec
from engine.models.validation_result import ValidationResult

class ProvisionState(BaseModel):
    user_request: str

    provision_spec: ProvisioningSpec | None = None

    compose_yaml: str | None = None

    validation_result: bool = ValidationResult

    execution_logs: list[str] = Field(default_factory=list)