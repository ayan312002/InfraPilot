from pathlib import Path

from engine.agents.requirement_agent import RequirementAgent
from engine.generators.compose_generator import ComposeGenerator
from engine.models.provision_state import ProvisionState
from engine.models.provisioning_spec import ProvisioningSpec
from engine.models.service_spec import ServiceSpec

from engine.runner import ProvisionRunner
from engine.utils.spec_loader import SpecLoader

import json


def main():
    request = input("Describe your infrastructure:\n> ")

    agent = RequirementAgent()

    state = ProvisionState(
        user_request=request
    )
    
    state.provision_spec = agent.generate_spec(request)

    print("\nGenerated ProvisioningSpec\n")
    print(state.provision_spec.model_dump_json(indent=2))

    
    runner = ProvisionRunner()

    result = runner.run(state)

    print()

    print("Compose Path :", state.generated_config_path)
    print("Valid        :", state.validation_result.success)

    if state.validation_result.errors:
        print("\nErrors:")
        for error in state.validation_result.errors:
            print(error)

if __name__ == "__main__":
    main()