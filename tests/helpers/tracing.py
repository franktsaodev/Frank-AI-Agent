from collections.abc import Iterable

from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


def get_events(
    events: Iterable[TraceEvent],
    event_type: TraceEventType,
) -> list[TraceEvent]:
    return [event for event in events if event.event_type == event_type]


def get_event(
    events: Iterable[TraceEvent],
    event_type: TraceEventType,
) -> TraceEvent:
    matching_events = get_events(
        events,
        event_type,
    )

    if not matching_events:
        raise AssertionError(f"Trace event not found: {event_type.value}")

    if len(matching_events) > 1:
        raise AssertionError(
            "Expected exactly one trace event "
            f"for {event_type.value}, "
            f"but found {len(matching_events)}."
        )

    return matching_events[0]


def assert_has_non_negative_duration(
    event: TraceEvent,
) -> None:
    assert "duration_ms" in event.metadata

    duration_ms = event.metadata["duration_ms"]

    assert isinstance(
        duration_ms,
        (int, float),
    )

    assert duration_ms >= 0
