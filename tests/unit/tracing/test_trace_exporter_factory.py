from pathlib import Path

from app.config_models.tracing_config import TracingConfig
from app.tracing.exporters.composite_trace_exporter import (
    CompositeTraceExporter,
)
from app.tracing.exporters.json_trace_exporter import (
    JsonTraceExporter,
)
from app.tracing.exporters.logging_trace_exporter import (
    LoggingTraceExporter,
)
from app.tracing.trace_exporter_factory import TraceExporterFactory


def test_create_should_return_logging_exporter() -> None:
    factory = TraceExporterFactory()

    exporter = factory.create(
        TracingConfig(),
    )

    assert isinstance(
        exporter,
        LoggingTraceExporter,
    )


def test_create_should_return_json_exporter_when_logging_disabled() -> None:
    factory = TraceExporterFactory()

    exporter = factory.create(
        TracingConfig(
            enable_logging=False,
            json_file_path=Path("logs/traces.jsonl"),
        ),
    )

    assert isinstance(
        exporter,
        JsonTraceExporter,
    )


def test_create_should_return_composite_exporter_when_both_enabled() -> None:
    factory = TraceExporterFactory()

    exporter = factory.create(
        TracingConfig(
            enable_logging=True,
            json_file_path=Path("logs/traces.jsonl"),
        ),
    )

    assert isinstance(
        exporter,
        CompositeTraceExporter,
    )
