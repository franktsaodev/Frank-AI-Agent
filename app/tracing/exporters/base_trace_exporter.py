from abc import ABC, abstractmethod

from app.tracing.trace_event import TraceEvent


class BaseTraceExporter(ABC):
    @abstractmethod
    def export(
        self,
        event: TraceEvent,
    ) -> None:
        raise NotImplementedError
