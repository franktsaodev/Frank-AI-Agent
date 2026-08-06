from app.session.session_expired_error import (
    SessionExpiredError,
)
from app.session.session_id import SessionId


def test_should_store_expired_session_id() -> None:
    session_id = SessionId(
        value="session-123",
    )

    error = SessionExpiredError(
        session_id=session_id,
    )

    assert error.session_id is session_id
    assert str(error) == ("Session expired: session-123")
