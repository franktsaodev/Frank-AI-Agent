from collections.abc import Iterator, Sequence

from app.clients.base_client import BaseClient
from app.models.client_response import ClientResponse
from app.models.client_stream_event import ClientStreamEvent
from app.models.message import Message
from app.tracing.trace_context import TraceContext


class FakeStreamingClient(BaseClient):
    def __init__(
        self,
        event_batches: Sequence[Sequence[ClientStreamEvent]],
    ) -> None:
        self._event_batches = [list(event_batch) for event_batch in event_batches]

        self.call_count = 0
        self.received_message_batches: list[list[Message]] = []
        self.received_trace_contexts: list[TraceContext] = []

    def chat(
        self,
        messages: Sequence[Message],
        trace_context: TraceContext,
    ) -> ClientResponse:
        raise AssertionError(
            "FakeStreamingClient.chat() should not be called.",
        )

    def stream_chat(
        self,
        messages: Sequence[Message],
        trace_context: TraceContext,
    ) -> Iterator[ClientStreamEvent]:
        batch_index = self.call_count

        if batch_index >= len(self._event_batches):
            raise RuntimeError(
                "FakeStreamingClient has no more configured event batches.",
            )

        self.call_count += 1
        self.received_message_batches.append(
            list(messages),
        )
        self.received_trace_contexts.append(
            trace_context,
        )

        yield from self._event_batches[batch_index]
