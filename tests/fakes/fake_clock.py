from app.clock.base_clock import BaseClock


class FakeClock(BaseClock):
    def __init__(
        self,
        times: list[float],
    ) -> None:
        if not times:
            raise ValueError("FakeClock requires at least one time value.")

        self._times = list(times)
        self._index = 0

    @classmethod
    def for_duration(
        cls,
        duration_seconds: float,
        *,
        start_time: float = 0.0,
    ) -> "FakeClock":
        if duration_seconds < 0:
            raise ValueError("duration_seconds cannot be negative.")

        return cls(
            times=[
                start_time,
                start_time + duration_seconds,
            ],
        )

    def now(self) -> float:
        if self._index >= len(self._times):
            raise RuntimeError("FakeClock has no more configured time values.")

        value = self._times[self._index]
        self._index += 1

        return value
