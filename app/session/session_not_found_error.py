from app.session.session_id import SessionId


class SessionNotFoundError(Exception):
    def __init__(
        self,
        session_id: SessionId,
    ) -> None:
        self.session_id = session_id

        super().__init__(f"Session not found: {session_id.value}")
