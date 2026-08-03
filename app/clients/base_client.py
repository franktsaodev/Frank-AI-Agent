from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.models.client_response import ClientResponse
from app.models.message import Message
from app.tracing.trace_context import TraceContext


class BaseClient(ABC):
    @abstractmethod
    def chat(
        self,
        messages: Sequence[Message],
        trace_context: TraceContext,
    ) -> ClientResponse:
        """Generate an assistant response from conversation messages."""
        raise NotImplementedError
