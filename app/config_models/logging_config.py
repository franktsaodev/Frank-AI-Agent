from dataclasses import dataclass


@dataclass(frozen=True)
class LoggingConfig:
    level: str

    def __post_init__(self) -> None:
        normalized_level = self.level.upper()

        if normalized_level not in {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }:
            raise ValueError(f"Unsupported logging level: {self.level}")
