from app.tracing.base_tracer import BaseTracer
from app.tracing.exporters.base_trace_exporter import BaseTraceExporter
from app.tracing.trace_event import TraceEvent


class ExporterTracer(BaseTracer):
    def __init__(
        self,
        exporter: BaseTraceExporter,
    ) -> None:
        self._exporter = exporter

    def trace(
        self,
        event: TraceEvent,
    ) -> None:
        self._exporter.export(event)
