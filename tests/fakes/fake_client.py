from collections.abc import Sequence

from app.clients.base_client import BaseClient
from app.models.client_response import ClientResponse
from app.models.message import Message
from app.tracing.trace_context import TraceContext


class FakeClient(BaseClient):
    def __init__(
        self,
        response: ClientResponse | None = None,
        responses: list[ClientResponse] | None = None,
    ) -> None:
        if response is not None and responses is not None:
            raise ValueError("Provide either response or responses, not both.")

        if responses is not None:
            self._responses = list(responses)
        else:
            self._responses = [
                response
                or ClientResponse(
                    content="This is a fake response.",
                )
            ]

        self.call_count = 0
        self.received_messages: list[Message] = []
        self.received_message_batches: list[list[Message]] = []
        self.received_trace_contexts: list[TraceContext] = []

    def chat(
        self,
        messages: Sequence[Message],
        trace_context: TraceContext,
    ) -> ClientResponse:
        self.call_count += 1
        self.received_messages = list(messages)
        self.received_message_batches.append(
            list(messages),
        )

        self.received_trace_contexts.append(
            trace_context,
        )

        response_index = self.call_count - 1

        if response_index >= len(self._responses):
            raise RuntimeError("FakeClient has no more configured responses.")

        return self._responses[response_index]
