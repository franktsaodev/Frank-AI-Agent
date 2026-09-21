from collections.abc import Iterator, Sequence

from app.agent.agent_run_context import AgentRunContext
from app.models.agent_stream_event import AgentStreamEvent
from app.models.client_response import ClientResponse
from app.models.message import Message


class FakeStreamingAgentRunner:
    def __init__(
        self,
        event_batches: Sequence[Sequence[AgentStreamEvent]],
    ) -> None:
        self._event_batches = [list(event_batch) for event_batch in event_batches]

        self.call_count = 0
        self.received_message_batches: list[list[Message]] = []
        self.received_contexts: list[AgentRunContext | None] = []

    def run(
        self,
        messages: Sequence[Message],
        context: AgentRunContext | None = None,
    ) -> ClientResponse:
        raise AssertionError(
            "FakeStreamingAgentRunner.run() should not be called.",
        )

    def stream(
        self,
        messages: Sequence[Message],
        context: AgentRunContext | None = None,
    ) -> Iterator[AgentStreamEvent]:
        batch_index = self.call_count

        if batch_index >= len(self._event_batches):
            raise RuntimeError(
                "FakeStreamingAgentRunner has no more configured event batches.",
            )

        self.call_count += 1
        self.received_message_batches.append(
            list(messages),
        )
        self.received_contexts.append(
            context,
        )

        yield from self._event_batches[batch_index]
