from app.clients.base_client import BaseClient
from app.models.client_response import ClientResponse
from app.models.message import Message


class FakeClient(BaseClient):
    def __init__(
        self,
        response: str = "This is a fake response.",
    ) -> None:
        self.response = response
        self.received_messages: list[Message] = []
        self.call_count = 0

    def chat(
        self,
        messages: list[Message],
    ) -> str:
        self.received_messages = list(messages)
        self.call_count += 1

        return ClientResponse(
            content=self.response,
        )
