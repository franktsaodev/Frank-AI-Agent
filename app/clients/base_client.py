from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence

from app.models.client_response import ClientResponse
from app.models.client_stream_event import (
    ClientStreamCompleted,
    ClientStreamEvent,
)
from app.models.message import Message
from app.tracing.trace_context import TraceContext


class BaseClient(ABC):
    @abstractmethod
    def chat(
        self,
        messages: Sequence[Message],
        trace_context: TraceContext,
    ) -> ClientResponse:
        """Generate an assistant response from conversation messages."""
        raise NotImplementedError

    def stream_chat(
        self,
        messages: Sequence[Message],
        trace_context: TraceContext,
    ) -> Iterator[ClientStreamEvent]:
        """Generate stream events with a synchronous fallback."""
        yield ClientStreamCompleted(
            response=self.chat(
                messages=messages,
                trace_context=trace_context,
            )
        )
