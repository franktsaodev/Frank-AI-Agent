from abc import ABC, abstractmethod

from app.tracing.trace_event import TraceEvent


class BaseTracer(ABC):
    @abstractmethod
    def trace(
        self,
        event: TraceEvent,
    ) -> None:
        """Record a trace event."""
