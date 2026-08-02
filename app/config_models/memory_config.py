from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryConfig:
    max_history_rounds: int

    def __post_init__(self) -> None:
        if self.max_history_rounds < 1:
            raise ValueError("max_history_rounds must be at least 1.")
