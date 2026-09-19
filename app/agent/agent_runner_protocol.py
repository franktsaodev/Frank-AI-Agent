from collections.abc import Iterator, Sequence
from typing import Protocol

from app.agent.agent_run_context import AgentRunContext
from app.models.agent_stream_event import AgentStreamEvent
from app.models.client_response import ClientResponse
from app.models.message import Message


class AgentRunnerProtocol(Protocol):
    def run(
        self,
        messages: Sequence[Message],
        context: AgentRunContext | None = None,
    ) -> ClientResponse: ...

    def stream(
        self,
        messages: Sequence[Message],
        context: AgentRunContext | None = None,
    ) -> Iterator[AgentStreamEvent]: ...
