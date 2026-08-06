from dataclasses import dataclass


@dataclass(frozen=True)
class SessionConfig:
    ttl_seconds: int
    cleanup_interval_seconds: int

    def __post_init__(self) -> None:
        if self.ttl_seconds < 1:
            raise ValueError("ttl_seconds must be at least 1.")

        if self.cleanup_interval_seconds < 1:
            raise ValueError("cleanup_interval_seconds must be at least 1.")
