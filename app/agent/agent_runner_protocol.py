from collections.abc import Sequence
from typing import Protocol

from app.models.client_response import ClientResponse
from app.models.message import Message


class AgentRunnerProtocol(Protocol):
    def run(
        self,
        messages: Sequence[Message],
    ) -> ClientResponse: ...
