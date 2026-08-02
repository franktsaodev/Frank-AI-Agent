from dataclasses import dataclass


@dataclass(frozen=True)
class PromptConfig:
    prompt_name: str
    user_name: str
    language: str
