from collections.abc import Sequence

from app.agent.agent_run_context import AgentRunContext
from app.models.client_response import ClientResponse
from app.models.message import Message


class FakeAgentRunner:
    def __init__(
        self,
        response: ClientResponse,
    ) -> None:
        self._response = response
        self.received_message_batches: list[list[Message]] = []
        self.received_contexts: list[AgentRunContext | None] = []

    def run(
        self,
        messages: Sequence[Message],
        context: AgentRunContext | None = None,
    ) -> ClientResponse:
        self.received_message_batches.append(
            list(messages),
        )
        self.received_contexts.append(
            context,
        )

        return self._response
