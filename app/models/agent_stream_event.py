from dataclasses import dataclass

from app.models.client_response import ClientResponse


@dataclass(frozen=True)
class AgentContentDelta:
    content: str

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("Agent content delta cannot be empty.")


@dataclass(frozen=True)
class AgentStreamCompleted:
    response: ClientResponse


type AgentStreamEvent = AgentContentDelta | AgentStreamCompleted
