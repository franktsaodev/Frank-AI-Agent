import json

from app.models.chat_stream_event import (
    ChatContentDelta,
    ChatStreamCompleted,
    ChatStreamEvent,
)


def serialize_chat_stream_event(
    event: ChatStreamEvent,
) -> str:
    if isinstance(event, ChatContentDelta):
        event_name = "content_delta"
        payload = {
            "content": event.content,
        }
    elif isinstance(event, ChatStreamCompleted):
        event_name = "completed"
        payload = {
            "response": event.response,
        }
    else:
        raise TypeError(f"Unsupported chat stream event: {type(event).__name__}")

    return _serialize_sse_event(
        event_name=event_name,
        payload=payload,
    )


def serialize_chat_stream_error(
    *,
    error: str,
    message: str,
) -> str:
    return _serialize_sse_event(
        event_name="error",
        payload={
            "error": error,
            "message": message,
        },
    )


def _serialize_sse_event(
    event_name: str,
    payload: dict[str, str],
) -> str:
    serialized_payload = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return f"event: {event_name}\ndata: {serialized_payload}\n\n"
