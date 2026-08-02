from collections.abc import Iterable

from app.tracing.exporters.base_trace_exporter import (
    BaseTraceExporter,
)
from app.tracing.trace_event import TraceEvent


class CompositeTraceExporter(BaseTraceExporter):
    def __init__(
        self,
        exporters: Iterable[BaseTraceExporter],
    ) -> None:
        self._exporters = tuple(exporters)

        if not self._exporters:
            raise ValueError("CompositeTraceExporter requires at least one exporter.")

    def export(
        self,
        event: TraceEvent,
    ) -> None:
        for exporter in self._exporters:
            exporter.export(event)
