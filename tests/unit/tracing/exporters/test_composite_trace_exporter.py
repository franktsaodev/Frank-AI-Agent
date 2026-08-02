from unittest.mock import MagicMock

import pytest

from app.tracing.exporters.base_trace_exporter import (
    BaseTraceExporter,
)
from app.tracing.exporters.composite_trace_exporter import (
    CompositeTraceExporter,
)
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


def test_export_should_forward_event_to_all_exporters() -> None:
    first_exporter = MagicMock(
        spec=BaseTraceExporter,
    )

    second_exporter = MagicMock(
        spec=BaseTraceExporter,
    )

    composite = CompositeTraceExporter(
        exporters=[
            first_exporter,
            second_exporter,
        ],
    )

    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        event_type=TraceEventType.AGENT_STARTED,
    )

    composite.export(event)

    first_exporter.export.assert_called_once_with(event)
    second_exporter.export.assert_called_once_with(event)


def test_init_should_reject_empty_exporters() -> None:
    with pytest.raises(
        ValueError,
        match="requires at least one exporter",
    ):
        CompositeTraceExporter(
            exporters=[],
        )
