import json
from datetime import datetime

from app.tracing.serializers.trace_event_serializer import (
    TraceEventSerializer,
)
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


def test_to_dict_should_serialize_trace_event(
    session_timestamp: datetime,
) -> None:
    serializer = TraceEventSerializer()

    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        parent_span_id="parent-span-123",
        event_type=TraceEventType.TOOL_FINISHED,
        timestamp=session_timestamp,
        metadata={
            "tool_name": "calculator",
            "duration_ms": 125.5,
        },
    )

    result = serializer.to_dict(event)

    assert result == {
        "timestamp": session_timestamp.isoformat(),
        "trace_id": "trace-123",
        "span_id": "span-123",
        "parent_span_id": "parent-span-123",
        "event_type": "tool_finished",
        "metadata": {
            "tool_name": "calculator",
            "duration_ms": 125.5,
        },
    }


def test_to_dict_should_preserve_none_parent_span_id() -> None:
    serializer = TraceEventSerializer()

    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        parent_span_id=None,
        event_type=TraceEventType.AGENT_STARTED,
    )

    result = serializer.to_dict(event)

    assert result["parent_span_id"] is None


def test_to_json_should_return_valid_json() -> None:
    serializer = TraceEventSerializer()

    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        event_type=TraceEventType.AGENT_STARTED,
        metadata={
            "message": "你好，Frank",
        },
    )

    result = serializer.to_json(event)

    parsed_result = json.loads(result)

    assert parsed_result["trace_id"] == "trace-123"
    assert parsed_result["event_type"] == "agent_started"
    assert parsed_result["metadata"] == {
        "message": "你好，Frank",
    }

    assert "\\u4f60" not in result
