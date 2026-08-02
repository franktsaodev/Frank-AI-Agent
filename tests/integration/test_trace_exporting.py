from unittest.mock import MagicMock

from app.tracing.exporter_tracer import ExporterTracer
from app.tracing.exporters.base_trace_exporter import (
    BaseTraceExporter,
)
from app.tracing.exporters.composite_trace_exporter import (
    CompositeTraceExporter,
)
from app.tracing.exporters.in_memory_trace_exporter import (
    InMemoryTraceExporter,
)
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


def test_tracer_should_export_event_to_all_composite_exporters() -> None:
    logging_exporter = MagicMock(
        spec=BaseTraceExporter,
    )

    memory_exporter = InMemoryTraceExporter()

    composite_exporter = CompositeTraceExporter(
        exporters=[
            logging_exporter,
            memory_exporter,
        ],
    )

    tracer = ExporterTracer(
        exporter=composite_exporter,
    )

    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        event_type=TraceEventType.AGENT_STARTED,
    )

    tracer.trace(event)

    logging_exporter.export.assert_called_once_with(event)

    assert memory_exporter.events == (
        event,
    )