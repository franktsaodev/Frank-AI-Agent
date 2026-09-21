from dataclasses import FrozenInstanceError

import pytest

from app.models.chat_stream_event import (
    ChatContentDelta,
    ChatStreamCompleted,
)


def test_content_delta_stores_content() -> None:
    event = ChatContentDelta(
        content="你好",
    )

    assert event.content == "你好"


def test_content_delta_rejects_empty_content() -> None:
    with pytest.raises(
        ValueError,
        match="Chat content delta cannot be empty",
    ):
        ChatContentDelta(
            content="",
        )


def test_content_delta_is_frozen() -> None:
    event = ChatContentDelta(
        content="你好",
    )

    with pytest.raises(FrozenInstanceError):
        event.content = "更新"  # pyright: ignore[reportAttributeAccessIssue]


def test_completed_event_stores_response() -> None:
    event = ChatStreamCompleted(
        response="完成",
    )

    assert event.response == "完成"


def test_completed_event_rejects_empty_response() -> None:
    with pytest.raises(
        ValueError,
        match="Chat stream response cannot be empty",
    ):
        ChatStreamCompleted(
            response="",
        )


def test_completed_event_is_frozen() -> None:
    event = ChatStreamCompleted(
        response="完成",
    )

    with pytest.raises(FrozenInstanceError):
        event.response = "更新"  # pyright: ignore[reportAttributeAccessIssue]
