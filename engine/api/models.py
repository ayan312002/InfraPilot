from pydantic import BaseModel, Field

from engine.models.provisioning_spec import ProvisioningSpec
from engine.models.validation_result import ValidationResult
from engine.models.execution_result import ExecutionResult
from engine.models.service_spec import ServiceSpec


class ProvisionRequest(BaseModel):
    user_request: str
    project_name: str | None = None
    example_id: str | None = None


class ApproveRequest(BaseModel):
    approved: bool
    feedback: str | None = None


class ProvisionResponse(BaseModel):
    session_id: str
    status: str
    project_name: str | None = None
    provision_spec: ProvisioningSpec | None = None
    generated_config: str | None = None
    validation_result: ValidationResult | None = None
    error: str | None = None


class FinalResponse(BaseModel):
    session_id: str
    status: str
    project_name: str | None = None
    approved: bool | None = None
    provision_spec: ProvisioningSpec | None = None
    generated_config: str | None = None
    validation_result: ValidationResult | None = None
    execution_result: ExecutionResult | None = None
    error: str | None = None


class SessionState(BaseModel):
    session_id: str
    status: str
    project_name: str | None = None
    provision_spec: ProvisioningSpec | None = None
    generated_config: str | None = None
    validation_result: ValidationResult | None = None
    approved: bool | None = None
    execution_result: ExecutionResult | None = None
    error: str | None = None
