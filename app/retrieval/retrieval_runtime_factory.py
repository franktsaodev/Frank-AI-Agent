from dataclasses import dataclass
from pathlib import Path

from app.config_models.retrieval_config import RetrievalConfig
from app.retrieval.embeddings.sentence_transformer_embedding_provider import (
    SentenceTransformerEmbeddingProvider,
)
from app.retrieval.indexing.knowledge_indexer import KnowledgeIndexer
from app.retrieval.loaders.directory_document_loader import DirectoryDocumentLoader
from app.retrieval.loaders.text_file_loader import TextFileLoader
from app.retrieval.policies.always_retrieve_policy import AlwaysRetrievePolicy
from app.retrieval.policies.never_retrieve_policy import NeverRetrievePolicy
from app.retrieval.policies.retrieval_policy import RetrievalPolicy
from app.retrieval.retrievers.no_op_retriever import NoOpRetriever
from app.retrieval.retrievers.retriever import Retriever
from app.retrieval.retrievers.vector_store_retriever import (
    VectorStoreRetriever,
)
from app.retrieval.splitters.fixed_size_text_splitter import (
    FixedSizeTextSplitter,
)
from app.retrieval.vector_stores.in_memory_vector_store import (
    InMemoryVectorStore,
)


@dataclass(frozen=True)
class RetrievalRuntime:
    retriever: Retriever
    retrieval_policy: RetrievalPolicy


class RetrievalRuntimeFactory:
    def create(
        self,
        config: RetrievalConfig,
    ) -> RetrievalRuntime:
        if not config.enabled:
            return RetrievalRuntime(
                retriever=NoOpRetriever(),
                retrieval_policy=NeverRetrievePolicy(),
            )

        knowledge_path = Path(config.knowledge_path)

        if not knowledge_path.exists():
            raise RuntimeError(
                f"Retrieval knowledge path does not exist: {knowledge_path}"
            )

        embedding_provider = SentenceTransformerEmbeddingProvider(
            model_name=config.embedding_model,
        )

        vector_store = InMemoryVectorStore()

        indexer = KnowledgeIndexer(
            splitter=FixedSizeTextSplitter(
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap,
            ),
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )

        if knowledge_path.is_dir():
            loader = DirectoryDocumentLoader(knowledge_path)
        elif knowledge_path.is_file():
            loader = TextFileLoader(knowledge_path)
        else:
            raise RuntimeError(
                f"Unsupported retrieval knowledge path: {knowledge_path}"
            )

        indexer.index(loader)

        retriever = VectorStoreRetriever(
            embedding_provider=embedding_provider,
            vector_store=vector_store,
            default_limit=config.top_k,
        )

        return RetrievalRuntime(
            retriever=retriever,
            retrieval_policy=AlwaysRetrievePolicy(),
        )
