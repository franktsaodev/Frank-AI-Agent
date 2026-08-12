from app.config_loaders.environment_reader import EnvironmentReader
from app.config_models.retrieval_config import RetrievalConfig


class RetrievalConfigLoader:
    def __init__(
        self,
        environment_reader: EnvironmentReader,
    ) -> None:
        self._environment_reader = environment_reader

    def load(self) -> RetrievalConfig:
        return RetrievalConfig(
            enabled=self._environment_reader.get_bool(
                name="RETRIEVAL_ENABLED",
                default=False,
            ),
            knowledge_path=self._environment_reader.get_str(
                name="RETRIEVAL_KNOWLEDGE_FILE_PATH",
                default="knowledge/knowledge.txt",
            ),
            chunk_size=self._environment_reader.get_int(
                name="RETRIEVAL_CHUNK_SIZE",
                default=500,
            ),
            chunk_overlap=self._environment_reader.get_int(
                name="RETRIEVAL_CHUNK_OVERLAP",
                default=50,
            ),
            top_k=self._environment_reader.get_int(
                name="RETRIEVAL_TOP_K",
                default=5,
            ),
            embedding_model=self._environment_reader.get_str(
                name="RETRIEVAL_EMBEDDING_MODEL",
                default="sentence-transformers/all-MiniLM-L6-v2",
            ),
        )
