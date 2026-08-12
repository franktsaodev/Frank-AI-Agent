from app.retrieval.embeddings.embedding_provider import EmbeddingProvider
from app.retrieval.loaders.document_loader import DocumentLoader
from app.retrieval.splitters.text_splitter import TextSplitter
from app.retrieval.vector_stores.vector_store import VectorStore


class KnowledgeIndexer:
    def __init__(
        self,
        *,
        splitter: TextSplitter,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._splitter = splitter
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def index(
        self,
        loader: DocumentLoader,
    ) -> None:
        documents = loader.load()

        chunks = [
            chunk for document in documents for chunk in self._splitter.split(document)
        ]

        if not chunks:
            return

        embeddings = self._embedding_provider.embed([chunk.content for chunk in chunks])

        self._vector_store.add(
            chunks,
            embeddings,
        )
