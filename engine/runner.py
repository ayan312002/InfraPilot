from pathlib import Path
import uuid

from engine.graph.workflow import InfraPilotWorkflow
from engine.models.provision_state import ProvisionState

class ProvisionRunner:

    def __init__(self):
        self.graph = InfraPilotWorkflow()

    def run(self, state: ProvisionState) -> ProvisionState:
        state = self.prepare_workspace(state)
        return self.graph.run(state)

    def prepare_workspace(self, state: ProvisionState):
        if state.project_name is None:
            state.project_name = uuid.uuid4().hex[:6]

        state.output_dir = Path("generated") / state.project_name
        state.output_dir.mkdir(parents=True, exist_ok=True)

        (state.output_dir / "request.txt").write_text(state.user_request)

        return state