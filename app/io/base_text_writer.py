from abc import ABC, abstractmethod


class BaseTextWriter(ABC):
    @abstractmethod
    def write(
        self,
        content: str,
    ) -> None:
        raise NotImplementedError
