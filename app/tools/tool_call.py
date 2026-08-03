from dataclasses import dataclass

from app.types.json_types import JsonObject


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: JsonObject

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Tool name cannot be empty")

        object.__setattr__(
            self,
            "arguments",
            dict(self.arguments),
        )
