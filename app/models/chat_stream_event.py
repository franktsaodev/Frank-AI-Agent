from dataclasses import dataclass


@dataclass(frozen=True)
class ChatContentDelta:
    content: str

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("Chat content delta cannot be empty.")


@dataclass(frozen=True)
class ChatStreamCompleted:
    response: str

    def __post_init__(self) -> None:
        if not self.response:
            raise ValueError("Chat stream response cannot be empty.")


type ChatStreamEvent = ChatContentDelta | ChatStreamCompleted
