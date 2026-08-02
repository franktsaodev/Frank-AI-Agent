from unittest.mock import MagicMock

from app.tracing.exporter_tracer import ExporterTracer
from app.tracing.exporters.base_trace_exporter import BaseTraceExporter
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


def test_trace_should_export_event() -> None:
    exporter = MagicMock(
        spec=BaseTraceExporter,
    )

    tracer = ExporterTracer(
        exporter=exporter,
    )

    event = TraceEvent(
        trace_id="test-trace-id",
        span_id="test-span-id",
        parent_span_id="parent-span-id",
        event_type=TraceEventType.TOOL_STARTED,
        metadata={
            "tool_name": "calculator",
        },
    )

    tracer.trace(event)

    exporter.export.assert_called_once_with(event)
