from pathlib import Path

from app.io.file_text_writer import FileTextWriter


def test_write_should_append_content_to_file(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "traces.jsonl"

    writer = FileTextWriter(
        file_path=file_path,
    )

    writer.write('{"event":"first"}')
    writer.write('{"event":"second"}')

    assert file_path.read_text(
        encoding="utf-8",
    ) == ('{"event":"first"}\n{"event":"second"}\n')


def test_write_should_create_parent_directories(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "logs" / "tracing" / "traces.jsonl"

    writer = FileTextWriter(
        file_path=file_path,
    )

    writer.write('{"event":"test"}')

    assert file_path.exists()

    assert (
        file_path.read_text(
            encoding="utf-8",
        )
        == '{"event":"test"}\n'
    )


def test_write_should_preserve_unicode_content(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "traces.jsonl"

    writer = FileTextWriter(
        file_path=file_path,
    )

    writer.write(
        '{"message":"你好，Frank"}',
    )

    assert (
        file_path.read_text(
            encoding="utf-8",
        )
        == '{"message":"你好，Frank"}\n'
    )
