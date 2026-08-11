from dataclasses import dataclass

from app.retrieval.document import Document


@dataclass(frozen=True)
class SearchResult:
    document: Document
    score: float
