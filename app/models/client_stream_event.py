from dataclasses import dataclass

from app.models.client_response import ClientResponse


@dataclass(frozen=True)
class ClientContentDelta:
    content: str

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("Stream content delta cannot be empty.")


@dataclass(frozen=True)
class ClientStreamCompleted:
    response: ClientResponse


type ClientStreamEvent = ClientContentDelta | ClientStreamCompleted
