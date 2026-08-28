from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalConfig:
    enabled: bool
    knowledge_path: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_score: float
    embedding_model: str
    trigger_keywords: frozenset[str]

    def __post_init__(self) -> None:
        if not self.knowledge_path.strip():
            raise ValueError("knowledge_path cannot be empty")

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        if self.top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        if not -1.0 <= self.min_score <= 1.0:
            raise ValueError("min_score must be between -1.0 and 1.0")

        if not self.embedding_model.strip():
            raise ValueError("embedding_model cannot be empty")
