from app.retrieval.document import Document


class RecursiveTextSplitter:
    _SEPARATORS = (
        "\n\n",
        "\n",
        " ",
        "",
    )

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

    def split(
        self,
        document: Document,
    ) -> list[Document]:
        units = self._split_recursively(
            content=document.content.strip(),
            separators=self._SEPARATORS,
        )

        contents = self._merge_units(units)

        return [
            Document(
                content=content,
                metadata={
                    **document.metadata,
                    "chunk_index": chunk_index,
                },
            )
            for chunk_index, content in enumerate(contents)
        ]

    def _split_recursively(
        self,
        *,
        content: str,
        separators: tuple[str, ...],
    ) -> list[str]:
        if len(content) <= self._chunk_size:
            return [content]

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            return list(content)

        parts = self._split_with_separator(
            content=content,
            separator=separator,
        )

        units: list[str] = []

        for part in parts:
            if len(part) <= self._chunk_size:
                units.append(part)
            else:
                units.extend(
                    self._split_recursively(
                        content=part,
                        separators=remaining_separators,
                    )
                )

        return units

    @staticmethod
    def _split_with_separator(
        *,
        content: str,
        separator: str,
    ) -> list[str]:
        parts = content.split(separator)

        if len(parts) == 1:
            return [content]

        units = [parts[0]]

        units.extend(f"{separator}{part}" for part in parts[1:])

        return [unit for unit in units if unit]

    def _merge_units(
        self,
        units: list[str],
    ) -> list[str]:
        chunks: list[str] = []
        current_units: list[str] = []
        current_length = 0

        for unit in units:
            if current_units and current_length + len(unit) > self._chunk_size:
                self._append_chunk(
                    chunks=chunks,
                    units=current_units,
                )

                current_units, current_length = self._create_overlap(
                    current_units,
                )

                while current_units and current_length + len(unit) > self._chunk_size:
                    removed_unit = current_units.pop(0)
                    current_length -= len(removed_unit)

            current_units.append(unit)
            current_length += len(unit)

        self._append_chunk(
            chunks=chunks,
            units=current_units,
        )

        return chunks

    def _create_overlap(
        self,
        units: list[str],
    ) -> tuple[list[str], int]:
        if self._chunk_overlap == 0:
            return [], 0

        overlap_units: list[str] = []
        overlap_length = 0

        for unit in reversed(units):
            if overlap_length + len(unit) > self._chunk_overlap:
                break

            overlap_units.insert(0, unit)
            overlap_length += len(unit)

        return overlap_units, overlap_length

    @staticmethod
    def _append_chunk(
        *,
        chunks: list[str],
        units: list[str],
    ) -> None:
        content = "".join(units).strip()

        if content:
            chunks.append(content)
