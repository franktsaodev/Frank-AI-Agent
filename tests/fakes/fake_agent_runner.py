from collections.abc import Sequence

from app.models.client_response import ClientResponse
from app.models.message import Message


class FakeAgentRunner:
    def __init__(
        self,
        response: ClientResponse,
    ) -> None:
        self.response = response
        self.received_message_batches: list[list[Message]] = []

    def run(
        self,
        messages: Sequence[Message],
    ) -> ClientResponse:
        self.received_message_batches.append(list(messages))

        return self.response
