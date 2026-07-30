import logging

from app.tracing.base_tracer import BaseTracer
from app.tracing.trace_event import TraceEvent

logger = logging.getLogger(__name__)


class LoggingTracer(BaseTracer):
    def trace(
        self,
        event: TraceEvent,
    ) -> None:
        logger.info(
            "Trace event=%s metadata=%s",
            event.event_type.value,
            event.metadata,
        )
