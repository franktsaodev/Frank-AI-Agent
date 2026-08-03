from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


def test_trace_event_should_store_trace_span_and_metadata() -> None:
    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        parent_span_id="parent-span-123",
        event_type=TraceEventType.AGENT_STARTED,
        metadata={
            "message_count": 1,
        },
    )

    assert event.trace_id == "trace-123"
    assert event.span_id == "span-123"
    assert event.parent_span_id == "parent-span-123"
    assert event.event_type == TraceEventType.AGENT_STARTED
    assert event.metadata == {
        "message_count": 1,
    }


def test_trace_event_should_use_empty_metadata_by_default() -> None:
    event = TraceEvent(
        trace_id="test-trace-id",
        span_id="test-span-id",
        event_type=TraceEventType.AGENT_STARTED,
    )

    assert event.metadata == {}


def test_trace_event_should_be_immutable() -> None:
    event = TraceEvent(
        trace_id="test-trace-id",
        span_id="span-123",
        event_type=TraceEventType.AGENT_STARTED,
    )

    with pytest.raises(FrozenInstanceError):
        event.event_type = TraceEventType.AGENT_FINISHED  # pyright: ignore[reportAttributeAccessIssue]


def test_trace_event_should_allow_no_parent_span() -> None:
    event = TraceEvent(
        trace_id="trace-123",
        span_id="agent-span",
        event_type=TraceEventType.AGENT_STARTED,
    )

    assert event.parent_span_id is None


def test_trace_event_should_store_timestamp() -> None:
    timestamp = datetime(
        2026,
        8,
        1,
        9,
        30,
        tzinfo=UTC,
    )

    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        event_type=TraceEventType.AGENT_STARTED,
        timestamp=timestamp,
    )

    assert event.timestamp == timestamp


def test_trace_event_should_create_timestamp_by_default() -> None:
    before = datetime.now(UTC)

    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        event_type=TraceEventType.AGENT_STARTED,
    )

    after = datetime.now(UTC)

    assert before <= event.timestamp <= after
