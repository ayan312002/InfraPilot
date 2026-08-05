from engine.models.provision_state import ProvisionState
from engine.runner import ProvisionRunner

def print_banner():
    print("=" * 60)
    print("InfraPilot")
    print("Natural Language Infrastructure Provisioning")
    print("=" * 60)

def print_summary(state):
    print("\n" + "=" * 60)
    print("Provisioning Summary")
    print("=" * 60)

    print(f"Project:      {state.project_name}")
    print(f"Compose File: {state.generated_config_path}")
    print(f"Validation:   {'✓ Passed' if state.validation_result.success else '✗ Failed'}")
    print(f"Approved:     {'Yes' if state.approved else 'No'}")

def main():
    print_banner()

    request = input("\nDescribe your infrastructure:\n> ")

    state = ProvisionState(user_request=request)

    runner = ProvisionRunner()
    state = runner.run(state)

    print_summary(state)

    if state.validation_result and state.validation_result.errors:
        print("\nValidation Errors:")
        for error in state.validation_result.errors:
            print(f"  • {error}")

    if state.execution_result and state.execution_result.errors:
        print("\nExecution Logs:")
        for error in state.execution_result.errors:
            print(f"  • {error}")

    print("Done.")


if __name__ == "__main__":
    main()