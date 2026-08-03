from enum import Enum

from pydantic import BaseModel, Field
from pathlib import Path

from engine.models.execution_result import ExecutionResult
from engine.models.provisioning_spec import ProvisioningSpec
from engine.models.validation_result import ValidationResult

class ProvisionStatus(str, Enum):
    GENERATED = "generated"
    VALIDATED = "validated"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"

class ProvisionState(BaseModel):
    user_request: str
    
    project_name: str | None = None

    provision_spec: ProvisioningSpec | None = None

    output_dir: Path | None = None

    generated_config: str | None = None

    generated_config_path: Path | None = None

    validation_result: ValidationResult | None = None

    approved: bool | None = None

    status: str = ProvisionStatus.GENERATED

    execution_result: ExecutionResult | None = None