from pathlib import Path

from app.io.base_text_writer import BaseTextWriter


class FileTextWriter(BaseTextWriter):
    def __init__(
        self,
        file_path: str | Path,
    ) -> None:
        self._file_path = Path(file_path)

    def write(
        self,
        content: str,
    ) -> None:
        self._file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self._file_path.open(
            mode="a",
            encoding="utf-8",
        ) as file:
            file.write(content)
            file.write("\n")
