from engine.models.provision_state import ProvisionState


from rich.console import Console
from rich.syntax import Syntax

class ApprovalManager:

    def review(self, state: ProvisionState) -> ProvisionState:

        print("\n========== Review ==========\n")
        console = Console()

        syntax = Syntax(state.generated_config, "yaml", theme="monokai", line_numbers=True)
        console.print(syntax)

        print(f"\nGenerated file: {state.generated_config_path}")
        print(f"Validation: {state.validation_result.success}")

        answer = input("\nProceed? (y/n): ")

        state.approved = answer.lower() == "y"

        return state