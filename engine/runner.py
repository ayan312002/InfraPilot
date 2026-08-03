from pathlib import Path
import uuid

from engine.generators.compose_generator import ComposeGenerator
from engine.models.provision_state import ProvisionState
from engine.validators.compose_validator import ComposeValidator


class ProvisionRunner:

    def __init__(self):
        self.generator = ComposeGenerator()
        self.validator = ComposeValidator()

    def run(self, state: ProvisionState) -> ProvisionState:

        if state.project_name is None:
            state.project_name = uuid.uuid4().hex[:6]

        state.output_dir = Path("generated") / state.project_name
        state.output_dir.mkdir(parents=True, exist_ok=True)

        state.generated_config = self.generator.generate(
            state.provision_spec
        )

        state.generated_config_path = self.generator.save(
            state.generated_config,
            state.output_dir / "docker-compose.yml"
        )

        state.validation_result = self.validator.validate(
            state.generated_config_path
        )

        (state.output_dir / "request.txt").write_text(
            state.user_request
        )

        (state.output_dir / "spec.json").write_text(
            state.provision_spec.model_dump_json(indent=2)
        )

        (state.output_dir / "validation.json").write_text(
            state.validation_result.model_dump_json(indent=2)
        )
        return state