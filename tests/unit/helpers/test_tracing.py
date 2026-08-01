import pytest

from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType
from tests.helpers.tracing import (
    assert_has_non_negative_duration,
    get_event,
)


def create_event(
    event_type: TraceEventType,
    metadata: dict | None = None,
) -> TraceEvent:
    return TraceEvent(
        trace_id="trace-1",
        span_id="span-1",
        event_type=event_type,
        metadata=metadata or {},
    )


def test_get_event_should_return_matching_event() -> None:
    expected_event = create_event(
        TraceEventType.AGENT_FINISHED,
    )

    events = [
        create_event(
            TraceEventType.AGENT_STARTED,
        ),
        expected_event,
    ]

    result = get_event(
        events,
        TraceEventType.AGENT_FINISHED,
    )

    assert result is expected_event


def test_get_event_should_raise_when_event_is_missing() -> None:
    with pytest.raises(
        AssertionError,
        match="Trace event not found: agent_finished",
    ):
        get_event(
            [],
            TraceEventType.AGENT_FINISHED,
        )


def test_get_event_should_raise_when_multiple_events_match() -> None:
    events = [
        create_event(
            TraceEventType.LLM_FINISHED,
        ),
        create_event(
            TraceEventType.LLM_FINISHED,
        ),
    ]

    with pytest.raises(
        AssertionError,
        match="Expected exactly one trace event",
    ):
        get_event(
            events,
            TraceEventType.LLM_FINISHED,
        )


def test_assert_has_non_negative_duration_should_accept_valid_duration() -> None:
    event = create_event(
        TraceEventType.AGENT_FINISHED,
        metadata={
            "duration_ms": 125.0,
        },
    )

    assert_has_non_negative_duration(event)
