from app.api.chat_stream_serializer import (
    serialize_chat_stream_error,
    serialize_chat_stream_event,
)
from app.models.chat_stream_event import (
    ChatContentDelta,
    ChatStreamCompleted,
)


def test_should_serialize_content_delta_as_sse() -> None:
    result = serialize_chat_stream_event(
        ChatContentDelta(
            content="你好\nFrank",
        )
    )

    assert result == ('event: content_delta\ndata: {"content":"你好\\nFrank"}\n\n')


def test_should_serialize_completed_event_as_sse() -> None:
    result = serialize_chat_stream_event(
        ChatStreamCompleted(
            response="完成",
        )
    )

    assert result == ('event: completed\ndata: {"response":"完成"}\n\n')


def test_should_serialize_error_as_sse() -> None:
    result = serialize_chat_stream_error(
        error="client_timeout",
        message="The AI service took too long to respond.",
    )

    assert result == (
        "event: error\n"
        'data: {"error":"client_timeout",'
        '"message":"The AI service took too long to respond."}\n\n'
    )
