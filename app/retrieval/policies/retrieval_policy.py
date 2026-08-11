from typing import Protocol


class RetrievalPolicy(Protocol):
    def should_retrieve(self, query: str) -> bool: ...
