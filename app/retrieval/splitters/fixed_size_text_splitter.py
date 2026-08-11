from app.retrieval.document import Document


class FixedSizeTextSplitter:
    def __init__(
        self,
        *,
        chunk_size: int,
        chunk_overlap: int = 0,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def split(self, document: Document) -> list[Document]:
        step = self._chunk_size - self._chunk_overlap
        chunks: list[Document] = []

        for start in range(0, len(document.content), step):
            content = document.content[start : start + self._chunk_size]

            if not content:
                break

            chunks.append(
                Document(
                    content=content,
                    metadata={
                        **document.metadata,
                        "chunk_index": len(chunks),
                    },
                )
            )

            if start + self._chunk_size >= len(document.content):
                break

        return chunks
