from dataclasses import dataclass


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        if self.initial_delay_seconds < 0:
            raise ValueError("initial_delay_seconds cannot be negative.")

        if self.backoff_multiplier < 1:
            raise ValueError("backoff_multiplier must be at least 1.")
