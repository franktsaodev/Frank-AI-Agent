from collections.abc import Sequence
from typing import Protocol

from app.retrieval.retrieved_context import RetrievedContext


class CitationGuardProtocol(Protocol):
    def apply(
        self,
        response: str,
        contexts: Sequence[RetrievedContext],
    ) -> str: ...
