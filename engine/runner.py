from pathlib import Path
import uuid

from engine.generators.compose_generator import ComposeGenerator
from engine.validators.compose_validator import ComposeValidator


class ProvisionRunner:

    def __init__(self):
        self.generator = ComposeGenerator()
        self.validator = ComposeValidator()

    def run(self, spec):

        compose_yaml_string = self.generator.generate(spec)

        validation = self.validator.validate(compose_yaml_string)

        compose_yaml_path = self.generator.save(
            compose_yaml_string,
            f"generated/{uuid.uuid4().hex[:6]}/docker-compose.yml"
        )

        return {
            "compose_yaml_path": compose_yaml_path,
            "compose_yaml_string": compose_yaml_string,
            "validation": validation
        }