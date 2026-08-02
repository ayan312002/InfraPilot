from pathlib import Path


class PromptLoader:

    @staticmethod
    def load(filename: str) -> str:
        prompt_path = Path(__file__).parent.parent / "prompts" / filename
        return prompt_path.read_text(encoding="utf-8")