from app.io.base_text_writer import BaseTextWriter
from app.tracing.exporters.base_trace_exporter import (
    BaseTraceExporter,
)
from app.tracing.serializers.trace_event_serializer import (
    TraceEventSerializer,
)
from app.tracing.trace_event import TraceEvent


class JsonTraceExporter(BaseTraceExporter):
    def __init__(
        self,
        serializer: TraceEventSerializer,
        writer: BaseTextWriter,
    ) -> None:
        self._serializer = serializer
        self._writer = writer

    def export(
        self,
        event: TraceEvent,
    ) -> None:
        serialized_event = self._serializer.to_json(event)

        self._writer.write(
            serialized_event,
        )
