from abc import ABC, abstractmethod

from app.models.message import Message


class BaseMemory(ABC):
    @abstractmethod
    def add_turn(self, user_message: Message, assistant_message: Message) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_messages(self) -> list[Message]:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError
