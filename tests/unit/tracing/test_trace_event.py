import pytest

from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


def test_trace_event_should_store_trace_id_type_and_metadata() -> None:
    event = TraceEvent(
        trace_id="test-trace-id",
        event_type=TraceEventType.LLM_STARTED,
        metadata={
            "iteration": 1,
        },
    )

    assert event.trace_id == "test-trace-id"
    assert event.event_type is TraceEventType.LLM_STARTED
    assert event.metadata == {
        "iteration": 1,
    }


def test_trace_event_should_use_empty_metadata_by_default() -> None:
    event = TraceEvent(
        trace_id="test-trace-id",
        event_type=TraceEventType.AGENT_STARTED,
    )

    assert event.metadata == {}


def test_trace_event_should_be_immutable() -> None:
    event = TraceEvent(
        trace_id="test-trace-id",
        event_type=TraceEventType.AGENT_STARTED,
    )

    with pytest.raises(AttributeError):
        event.event_type = TraceEventType.AGENT_FINISHED
