from dataclasses import dataclass


@dataclass(frozen=True)
class PromptConfig:
    prompt_name: str
    user_name: str
    language: str

    def __post_init__(self) -> None:
        if not self.prompt_name.strip():
            raise ValueError("prompt_name cannot be empty.")

        if not self.user_name.strip():
            raise ValueError("user_name cannot be empty.")

        if not self.language.strip():
            raise ValueError("language cannot be empty.")
