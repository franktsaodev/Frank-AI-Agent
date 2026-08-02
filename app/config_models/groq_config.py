from dataclasses import dataclass


@dataclass(frozen=True)
class GroqConfig:
    api_key: str
    model: str
    temperature: float = 0.7
    max_completion_tokens: int = 1024

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise ValueError("api_key cannot be empty.")

        if not self.model.strip():
            raise ValueError("model cannot be empty.")

        if self.max_completion_tokens < 1:
            raise ValueError("max_completion_tokens must be at least 1.")
