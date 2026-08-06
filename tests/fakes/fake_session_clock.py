from datetime import datetime


class FakeSessionClock:
    def __init__(
        self,
        current_time: datetime,
    ) -> None:
        self._current_time = current_time

    def now(
        self,
    ) -> datetime:
        return self._current_time

    def set(
        self,
        current_time: datetime,
    ) -> None:
        self._current_time = current_time
