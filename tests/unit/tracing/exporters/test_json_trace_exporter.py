from unittest.mock import MagicMock

from app.io.base_text_writer import BaseTextWriter
from app.tracing.exporters.json_trace_exporter import (
    JsonTraceExporter,
)
from app.tracing.serializers.trace_event_serializer import (
    TraceEventSerializer,
)
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


def test_export_should_serialize_and_write_event() -> None:
    serializer = MagicMock(
        spec=TraceEventSerializer,
    )

    writer = MagicMock(
        spec=BaseTextWriter,
    )

    exporter = JsonTraceExporter(
        serializer=serializer,
        writer=writer,
    )

    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        event_type=TraceEventType.AGENT_STARTED,
    )

    serializer.to_json.return_value = '{"trace_id":"trace-123"}'

    exporter.export(event)

    serializer.to_json.assert_called_once_with(event)

    writer.write.assert_called_once_with(
        '{"trace_id":"trace-123"}',
    )
