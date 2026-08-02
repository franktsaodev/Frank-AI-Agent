import json
from pathlib import Path
from unittest.mock import MagicMock

from app.io.file_text_writer import FileTextWriter
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
from app.tracing.exporters.json_trace_exporter import (
    JsonTraceExporter,
)
from app.tracing.serializers.trace_event_serializer import (
    TraceEventSerializer,
)
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType
from tests.fakes.in_memory_text_writer import InMemoryTextWriter


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

    assert memory_exporter.events == (event,)


def test_tracer_should_export_trace_event_as_json() -> None:
    writer = InMemoryTextWriter()

    exporter = JsonTraceExporter(
        serializer=TraceEventSerializer(),
        writer=writer,
    )

    tracer = ExporterTracer(
        exporter=exporter,
    )

    event = TraceEvent(
        trace_id="trace-123",
        span_id="span-123",
        parent_span_id=None,
        event_type=TraceEventType.AGENT_STARTED,
        metadata={
            "message_count": 1,
        },
    )

    tracer.trace(event)

    assert len(writer.contents) == 1

    exported_data = json.loads(
        writer.contents[0],
    )

    assert exported_data["trace_id"] == "trace-123"
    assert exported_data["span_id"] == "span-123"
    assert exported_data["parent_span_id"] is None
    assert exported_data["event_type"] == "agent_started"
    assert exported_data["metadata"] == {
        "message_count": 1,
    }


def test_tracer_should_export_trace_event_to_jsonl_file(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "traces.jsonl"

    exporter = JsonTraceExporter(
        serializer=TraceEventSerializer(),
        writer=FileTextWriter(
            file_path=file_path,
        ),
    )

    tracer = ExporterTracer(
        exporter=exporter,
    )

    first_event = TraceEvent(
        trace_id="trace-123",
        span_id="agent-span",
        event_type=TraceEventType.AGENT_STARTED,
    )

    second_event = TraceEvent(
        trace_id="trace-123",
        span_id="agent-span",
        event_type=TraceEventType.AGENT_FINISHED,
        metadata={
            "duration_ms": 125.0,
        },
    )

    tracer.trace(first_event)
    tracer.trace(second_event)

    lines = file_path.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(lines) == 2

    first_data = json.loads(lines[0])
    second_data = json.loads(lines[1])

    assert first_data["event_type"] == "agent_started"
    assert second_data["event_type"] == "agent_finished"

    assert second_data["metadata"]["duration_ms"] == 125.0
