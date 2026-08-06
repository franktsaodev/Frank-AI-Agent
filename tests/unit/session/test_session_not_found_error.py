from app.session.session_id import SessionId
from app.session.session_not_found_error import (
    SessionNotFoundError,
)


def test_should_store_missing_session_id() -> None:
    session_id = SessionId(
        value="session-123",
    )

    error = SessionNotFoundError(
        session_id=session_id,
    )

    assert error.session_id is session_id
    assert str(error) == ("Session not found: session-123")
