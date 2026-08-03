

import subprocess

from engine.models.execution_result import ExecutionResult
from engine.models.provision_state import ProvisionState
from engine.models.validation_result import ValidationResult


class ExecutorAgent:
    def execute(self, state: ProvisionState) -> ProvisionState:
        print("Mocking Execution pipeline...")
        # result = subprocess.run(
        #     [
        #         "docker",
        #         "compose",
        #         "-f",
        #         state.generated_config_path,
        #         "config"
        #     ],
        #     capture_output=True,
        #     text=True
        # )

        # if result.returncode == 0:
        #     state.execution_result = ExecutionResult(success=True)
            
        # else:
        #     state.execution_result = ExecutionResult(
        #         success=False,
        #         errors=[result.stderr.strip()]
        #     )
        print("Execution completed.")

        state.execution_result = ExecutionResult(
                success=False,
                errors=[]
        )
        return state
