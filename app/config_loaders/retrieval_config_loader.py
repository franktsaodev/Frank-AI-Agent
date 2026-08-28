from app.config_loaders.environment_reader import EnvironmentReader
from app.config_models.retrieval_config import RetrievalConfig


class RetrievalConfigLoader:
    def __init__(
        self,
        environment_reader: EnvironmentReader,
    ) -> None:
        self._environment_reader = environment_reader

    def load(self) -> RetrievalConfig:
        trigger_keywords_value = self._environment_reader.get_str(
            name="RETRIEVAL_TRIGGER_KEYWORDS",
            default="documentation,manual,session,deployment,architecture",
        )

        trigger_keywords = frozenset(
            keyword.strip()
            for keyword in trigger_keywords_value.split(",")
            if keyword.strip()
        )

        return RetrievalConfig(
            enabled=self._environment_reader.get_bool(
                name="RETRIEVAL_ENABLED",
                default=False,
            ),
            knowledge_path=self._environment_reader.get_str(
                name="RETRIEVAL_KNOWLEDGE_PATH",
                default="knowledge",
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
            min_score=self._environment_reader.get_float(
                name="RETRIEVAL_MIN_SCORE",
                default=-1.0,
            ),
            embedding_model=self._environment_reader.get_str(
                name="RETRIEVAL_EMBEDDING_MODEL",
                default="sentence-transformers/all-MiniLM-L6-v2",
            ),
            trigger_keywords=trigger_keywords,
        )
