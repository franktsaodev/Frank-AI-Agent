from dataclasses import dataclass


@dataclass(frozen=True)
class CorsConfig:
    allowed_origins: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.allowed_origins:
            raise ValueError("allowed_origins cannot be empty")

        if any(
            not origin.strip() or origin != origin.strip()
            for origin in self.allowed_origins
        ):
            raise ValueError("allowed_origins must contain non-blank, trimmed origins")
