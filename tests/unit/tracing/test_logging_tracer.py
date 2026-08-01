import logging

from app.tracing.logging_tracer import LoggingTracer
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


def test_trace_should_log_event(
    caplog,
) -> None:
    tracer = LoggingTracer()

    event = TraceEvent(
        trace_id="test-trace-id",
        span_id="test-span-id",
        parent_span_id="parent-span-id",
        event_type=TraceEventType.TOOL_STARTED,
        metadata={
            "tool_name": "calculator",
        },
    )

    with caplog.at_level(logging.INFO):
        tracer.trace(event)

    assert "test-trace-id" in caplog.text
    assert "test-span-id" in caplog.text
    assert "parent-span-id" in caplog.text
    assert "tool_started" in caplog.text
    assert "calculator" in caplog.text