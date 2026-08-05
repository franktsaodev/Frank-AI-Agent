from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeInfo:
    service_name: str
    version: str
