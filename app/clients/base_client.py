from abc import ABC, abstractmethod

from app.models.client_response import ClientResponse
from app.models.message import Message


class BaseClient(ABC):
    @abstractmethod
    def chat(self, messages: list[Message]) -> ClientResponse:
        """Generate an assistant response from conversation messages."""
        raise NotImplementedError
