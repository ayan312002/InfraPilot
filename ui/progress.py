from contextlib import contextmanager

from rich.progress import Progress, SpinnerColumn, TextColumn

class PipelineProgress:
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            transient=True,
        )

    def __enter__(self):
        self.progress.__enter__()
        self.task = self.progress.add_task("Starting...", total=None)
        return self

    def __exit__(self, *args):
        self.progress.__exit__(*args)

    @contextmanager
    def suspend(self):
        self.progress.stop()
        try:
            yield
        finally:
            self.progress.start()
            
    def pause(self):
        self.progress.stop()

    def resume(self):
        self.progress.start()
        
    def step(self, name: str):
        self.progress.update(
            self.task,
            description=name,
            refresh=True,
        )