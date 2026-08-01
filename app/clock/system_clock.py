import time

from app.clock.base_clock import BaseClock


class SystemClock(BaseClock):
    def now(self) -> float:
        return time.perf_counter()
