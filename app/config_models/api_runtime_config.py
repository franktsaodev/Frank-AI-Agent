from dataclasses import dataclass


@dataclass(frozen=True)
class ApiRuntimeConfig:
    service_name: str
    version: str

    def __post_init__(self) -> None:
        if not self.service_name.strip():
            raise ValueError("service_name must not be blank.")

        if not self.version.strip():
            raise ValueError("version must not be blank.")
