from dataclasses import dataclass


@dataclass(
    frozen=True,
)
class SessionId:
    value: str

    def __post_init__(
        self,
    ) -> None:
        if not self.value.strip():
            raise ValueError("Session ID must not be blank.")
