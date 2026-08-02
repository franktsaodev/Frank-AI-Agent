import logging
from unittest.mock import MagicMock

from app.tracing.exporters.logging_trace_exporter import (
    LoggingTraceExporter,
)
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


def test_export_should_log_trace_event() -> None:
    logger = MagicMock(spec=logging.Logger)

    exporter = LoggingTraceExporter(
        logger=logger,
    )

    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        parent_span_id="parent-span-123",
        event_type=TraceEventType.TOOL_STARTED,
        metadata={
            "tool_name": "calculator",
        },
    )

    exporter.export(event)

    logger.info.assert_called_once_with(
        "timestamp=%s trace_id=%s span_id=%s "
        "parent_span_id=%s event_type=%s metadata=%s",
        event.timestamp.isoformat(),
        "trace-123",
        "span-123",
        "parent-span-123",
        "tool_started",
        {
            "tool_name": "calculator",
        },
    )
