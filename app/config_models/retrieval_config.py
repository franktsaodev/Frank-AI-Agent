from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalConfig:
    enabled: bool
    knowledge_path: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    embedding_model: str
