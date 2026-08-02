from engine.generators.compose_generator import ComposeGenerator
from engine.models.provisioning_spec import ProvisioningSpec
from engine.models.service_spec import ServiceSpec

spec = ProvisioningSpec(
    project_name="demo",
    services=[
        ServiceSpec(
            name="postgres",
            image="postgres:16",
            ports=["5432:5432"]
        ),
        ServiceSpec(
            name="redis",
            image="redis:7",
            ports=["6379:6379"]
        )
    ]
)

generator = ComposeGenerator()

yaml_content = generator.generate_compose(spec)

print(yaml_content)

generator.save(
    yaml_content,
    "generated/docker-compose.yml"
)