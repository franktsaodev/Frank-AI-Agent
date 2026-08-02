import logging

from app.tracing.exporters.base_trace_exporter import (
    BaseTraceExporter,
)
from app.tracing.trace_event import TraceEvent


class LoggingTraceExporter(BaseTraceExporter):
    def __init__(
        self,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def export(
        self,
        event: TraceEvent,
    ) -> None:
        self._logger.info(
            "timestamp=%s trace_id=%s span_id=%s "
            "parent_span_id=%s event_type=%s metadata=%s",
            event.timestamp.isoformat(),
            event.trace_id,
            event.span_id,
            event.parent_span_id,
            event.event_type.value,
            event.metadata,
        )
