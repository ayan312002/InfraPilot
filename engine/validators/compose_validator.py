import subprocess

from engine.models.validation_result import ValidationResult


class ComposeValidator:

    def validate(self, compose_path: str) -> ValidationResult:

        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                compose_path,
                "config"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return ValidationResult(success=True)

        return ValidationResult(
            success=False,
            errors=[result.stderr.strip()]
        )