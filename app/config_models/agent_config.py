from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    max_iterations: int = 10

    def __post_init__(self) -> None:
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1.")
