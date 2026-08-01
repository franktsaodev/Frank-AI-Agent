import logging

from app.tracing.base_tracer import BaseTracer
from app.tracing.trace_event import TraceEvent


class LoggingTracer(BaseTracer):
    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)

    def trace(
        self,
        event: TraceEvent,
    ) -> None:
        self._logger.info(
            "timestamp=%s trace_id=%s span_id=%s parent_span_id=%s event_type=%s metadata=%s",
            event.timestamp.isoformat(),
            event.trace_id,
            event.span_id,
            event.parent_span_id,
            event.event_type.value,
            event.metadata,
        )
