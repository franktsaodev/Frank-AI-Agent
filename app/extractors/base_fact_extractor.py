from abc import ABC, abstractmethod


class BaseFactExtractor(ABC):
    @abstractmethod
    def extract(
        self,
        user_message: str,
    ) -> dict[str, str]:
        """Extract user facts from a message."""
        raise NotImplementedError
