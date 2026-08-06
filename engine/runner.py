from pathlib import Path
import uuid

from engine.graph.workflow import InfraPilotWorkflow
from engine.models.provision_state import ProvisionState
from ui.progress import PipelineProgress

class ProvisionRunner:

    def __init__(self):
        self.graph = InfraPilotWorkflow()

    def run(self, state: ProvisionState) -> ProvisionState:
        state = self.prepare_workspace(state)
        with PipelineProgress() as progress:
            self.graph.set_progress(progress)
            state = self.graph.run(state)
        return state

    def prepare_workspace(self, state: ProvisionState):
        if state.project_name is None:
            state.project_name = uuid.uuid4().hex[:6]

        state.output_dir = Path("generated") / state.project_name
        state.output_dir.mkdir(parents=True, exist_ok=True)

        (state.output_dir / "request.txt").write_text(state.user_request)

        return state