import logging
from collections.abc import Sequence

from app.config_models.memory_config import MemoryConfig
from app.memory.base_memory import BaseMemory
from app.models.message import Message

logger = logging.getLogger(__name__)


class SlidingWindowMemory(BaseMemory):
    def __init__(
        self,
        config: MemoryConfig,
        initial_messages: Sequence[Message] = (),
    ) -> None:
        self._config = config
        self._messages: list[Message] = list(initial_messages)

        self._trim_to_window()

    def add_turn(
        self,
        user_message: Message,
        assistant_message: Message,
    ) -> None:
        self._messages.extend(
            [
                user_message,
                assistant_message,
            ]
        )

        self._trim_to_window()

    def get_messages(self) -> tuple[Message, ...]:
        return tuple(self._messages)

    def clear(self) -> None:
        self._messages.clear()
        logger.info("Memory cleared")

    def _trim_to_window(
        self,
    ) -> None:
        max_messages = self._config.max_history_rounds * 2

        if len(self._messages) <= max_messages:
            return

        self._messages = self._messages[-max_messages:]

        logger.debug(
            "Trimmed memory to %d messages",
            max_messages,
        )
