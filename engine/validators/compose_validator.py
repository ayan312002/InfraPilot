import subprocess

from engine.models.validation_result import ValidationResult


class ComposeValidator:

    def validate(self, compose_yaml_string: str) -> ValidationResult:
        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f", "-",  # The dash "-" tells docker to read from standard input
                "config"
            ],
            input=compose_yaml_string,  # Passes the string directly into stdin
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return ValidationResult(success=True)

        return ValidationResult(
            success=False,
            errors=[result.stderr.strip()]
        )