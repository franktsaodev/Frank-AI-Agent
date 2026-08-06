from app.session.session_id import SessionId


class SessionExpiredError(Exception):
    def __init__(
        self,
        session_id: SessionId,
    ) -> None:
        self.session_id = session_id

        super().__init__(f"Session expired: {session_id.value}")
