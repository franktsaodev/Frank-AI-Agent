from app.tracing.exporters.in_memory_trace_exporter import (
    InMemoryTraceExporter,
)
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


def test_export_should_store_event() -> None:
    exporter = InMemoryTraceExporter()

    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        event_type=TraceEventType.AGENT_STARTED,
    )

    exporter.export(event)

    assert exporter.events == (event,)


def test_export_should_preserve_event_order() -> None:
    exporter = InMemoryTraceExporter()

    first_event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        event_type=TraceEventType.AGENT_STARTED,
    )

    second_event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        event_type=TraceEventType.AGENT_FINISHED,
    )

    exporter.export(first_event)
    exporter.export(second_event)

    assert exporter.events == (
        first_event,
        second_event,
    )
