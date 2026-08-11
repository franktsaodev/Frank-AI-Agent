from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("content cannot be empty")
