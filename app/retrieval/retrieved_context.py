from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedContext:
    content: str
    source: str | None = None
