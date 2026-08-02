from pathlib import Path

from engine.generators.compose_generator import ComposeGenerator
from engine.models.provisioning_spec import ProvisioningSpec
from engine.models.service_spec import ServiceSpec

from engine.runner import ProvisionRunner
from engine.utils.spec_loader import SpecLoader

import json


def main():
    spec = SpecLoader.load("examples/postgres_redis.json")

    runner = ProvisionRunner()

    result = runner.run(spec)

    print()

    print("Compose Path :", result["compose_yaml_path"])
    print("Valid        :", result["validation"].success)

    if result["validation"].errors:
        print()
        print("Errors:")
        for error in result["validation"].errors:
            print(error)

if __name__ == "__main__":
    main()