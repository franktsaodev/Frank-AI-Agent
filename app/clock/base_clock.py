from abc import ABC, abstractmethod


class BaseClock(ABC):
    @abstractmethod
    def now(self) -> float:
        """Return a monotonic time value in seconds."""
        raise NotImplementedError
