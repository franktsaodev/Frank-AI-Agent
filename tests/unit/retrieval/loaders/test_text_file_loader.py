from pathlib import Path

import pytest

from app.retrieval.loaders.text_file_loader import TextFileLoader


def test_should_load_text_file(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("Hello RAG", encoding="utf-8")

    loader = TextFileLoader(path)

    documents = loader.load()

    assert len(documents) == 1
    assert documents[0].content == "Hello RAG"
    assert documents[0].metadata["source"] == str(path)


def test_should_load_utf8_content(tmp_path: Path) -> None:
    path = tmp_path / "sample.txt"
    path.write_text("這是一份測試文件", encoding="utf-8")

    documents = TextFileLoader(path).load()

    assert documents[0].content == "這是一份測試文件"


def test_should_reject_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.txt"
    path.write_text("   ", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="content cannot be empty",
    ):
        TextFileLoader(path).load()
