from app.io.base_text_writer import BaseTextWriter


class InMemoryTextWriter(BaseTextWriter):
    def __init__(self) -> None:
        self._contents: list[str] = []

    @property
    def contents(self) -> tuple[str, ...]:
        return tuple(self._contents)

    def write(
        self,
        content: str,
    ) -> None:
        self._contents.append(content)
