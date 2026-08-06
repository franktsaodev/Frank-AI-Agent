import pytest

from app.session.session_id import (
    SessionId,
)


def test_should_store_session_identifier() -> None:
    session = SessionId(
        value="abc123",
    )

    assert session.value == "abc123"


def test_should_reject_blank_identifier() -> None:
    with pytest.raises(
        ValueError,
        match="Session ID must not be blank",
    ):
        SessionId(
            value="   ",
        )
