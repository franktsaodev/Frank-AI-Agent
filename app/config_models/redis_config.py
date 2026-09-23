from dataclasses import dataclass


@dataclass(frozen=True)
class RedisConfig:
    url: str
    session_key_prefix: str

    def __post_init__(self) -> None:
        if not self.url.strip():
            raise ValueError("url cannot be empty.")

        if not self.session_key_prefix.strip():
            raise ValueError("session_key_prefix cannot be empty.")
