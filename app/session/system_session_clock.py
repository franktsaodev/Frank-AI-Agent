from datetime import UTC, datetime


class SystemSessionClock:
    def now(
        self,
    ) -> datetime:
        return datetime.now(
            UTC,
        )
