from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TracingConfig:
    enable_logging: bool = True
    json_file_path: Path | None = None

    def __post_init__(self) -> None:
        if not self.enable_logging and self.json_file_path is None:
            raise ValueError("At least one trace exporter must be enabled.")
