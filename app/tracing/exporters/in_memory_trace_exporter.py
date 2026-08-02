from app.tracing.exporters.base_trace_exporter import (
    BaseTraceExporter,
)
from app.tracing.trace_event import TraceEvent


class InMemoryTraceExporter(BaseTraceExporter):
    def __init__(self) -> None:
        self._events: list[TraceEvent] = []

    @property
    def events(self) -> tuple[TraceEvent, ...]:
        return tuple(self._events)

    def export(
        self,
        event: TraceEvent,
    ) -> None:
        self._events.append(event)
