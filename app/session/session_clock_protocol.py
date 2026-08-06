from datetime import datetime
from typing import Protocol


class SessionClockProtocol(Protocol):
    def now(
        self,
    ) -> datetime: ...
