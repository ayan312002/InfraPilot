import subprocess

from engine.models.provision_state import ProvisionState
from engine.models.validation_result import ValidationResult


class ComposeValidator:

    def validate(self, state: ProvisionState) -> ProvisionState:

        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                state.generated_config_path,
                "config"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            state.validation_result = ValidationResult(success=True)
            
        else:
            state.validation_result = ValidationResult(
                success=False,
                errors=[result.stderr.strip()]
            )
            
        return state
