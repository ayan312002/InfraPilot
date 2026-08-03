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

        self.save_validation_output(state)
        return state

    def save_validation_output(self, state):
        output_file = (state.output_dir / "validation.json")

        output_file.write_text(state.validation_result.model_dump_json(indent=2))

        return True