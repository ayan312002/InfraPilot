from pathlib import Path

from engine.agents.requirement_agent import RequirementAgent
from engine.generators.compose_generator import ComposeGenerator
from engine.models.provisioning_spec import ProvisioningSpec
from engine.models.service_spec import ServiceSpec

from engine.runner import ProvisionRunner
from engine.utils.spec_loader import SpecLoader

import json


def main():
    request = input("Describe your infrastructure:\n> ")

    agent = RequirementAgent()

    spec = agent.generate_spec(request)

    print("\nGenerated ProvisioningSpec\n")
    print(spec.model_dump_json(indent=2))

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