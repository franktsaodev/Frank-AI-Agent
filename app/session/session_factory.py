import uuid

from app.session.session_id import (
    SessionId,
)


class SessionFactory:
    def create(
        self,
    ) -> SessionId:
        return SessionId(
            value=uuid.uuid4().hex,
        )
