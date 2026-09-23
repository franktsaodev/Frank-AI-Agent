from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from redis import Redis

from app.agent.chat_agent_state import ChatAgentState
from app.session.redis_session_repository import (
    RedisSessionRepository,
)
from app.session.session_id import SessionId
from app.session.stored_session import StoredSession
from app.session.stored_session_codec import StoredSessionCodec


def create_stored_session() -> StoredSession:
    return StoredSession(
        session_id=SessionId(
            value="session-123",
        ),
        created_at=datetime(
            2026,
            9,
            23,
            10,
            0,
            tzinfo=UTC,
        ),
        last_activity_at=datetime(
            2026,
            9,
            23,
            10,
            30,
            tzinfo=UTC,
        ),
        agent_state=ChatAgentState(
            messages=(),
            facts={
                "user_name": "Frank",
            },
        ),
    )


def test_save_should_store_encoded_session_with_ttl() -> None:
    redis_client = MagicMock(
        spec=Redis,
    )
    codec = MagicMock(
        spec=StoredSessionCodec,
    )
    stored_session = create_stored_session()
    encoded_session = '{"schema_version":1}'

    codec.encode.return_value = encoded_session

    repository = RedisSessionRepository(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )

    repository.save(
        stored_session,
        ttl_seconds=3600,
    )

    codec.encode.assert_called_once_with(
        stored_session,
    )
    redis_client.set.assert_called_once_with(
        name="frank-ai-agent:sessions:session-123",
        value=encoded_session,
        ex=3600,
    )


def test_get_should_decode_stored_session() -> None:
    redis_client = MagicMock(
        spec=Redis,
    )
    codec = MagicMock(
        spec=StoredSessionCodec,
    )
    expected_session = create_stored_session()
    encoded_session = '{"schema_version":1}'

    redis_client.get.return_value = encoded_session
    codec.decode.return_value = expected_session

    repository = RedisSessionRepository(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )

    result = repository.get(
        SessionId(
            value="session-123",
        )
    )

    assert result is expected_session
    redis_client.get.assert_called_once_with(
        "frank-ai-agent:sessions:session-123",
    )
    codec.decode.assert_called_once_with(
        encoded_session,
    )


def test_get_should_decode_byte_payload_as_utf8() -> None:
    redis_client = MagicMock(
        spec=Redis,
    )
    codec = MagicMock(
        spec=StoredSessionCodec,
    )
    expected_session = create_stored_session()
    encoded_session = '{"message":"你好"}'

    redis_client.get.return_value = encoded_session.encode(
        "utf-8",
    )
    codec.decode.return_value = expected_session

    repository = RedisSessionRepository(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )

    result = repository.get(
        SessionId(
            value="session-123",
        )
    )

    assert result is expected_session
    codec.decode.assert_called_once_with(
        encoded_session,
    )


def test_get_should_return_none_when_session_does_not_exist() -> None:
    redis_client = MagicMock(
        spec=Redis,
    )
    codec = MagicMock(
        spec=StoredSessionCodec,
    )

    redis_client.get.return_value = None

    repository = RedisSessionRepository(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )

    result = repository.get(
        SessionId(
            value="missing-session",
        )
    )

    assert result is None
    redis_client.get.assert_called_once_with(
        "frank-ai-agent:sessions:missing-session",
    )
    codec.decode.assert_not_called()


@pytest.mark.parametrize(
    ("redis_result", "expected_result"),
    [
        (0, False),
        (1, True),
    ],
)
def test_exists_should_return_whether_session_exists(
    redis_result: int,
    expected_result: bool,
) -> None:
    redis_client = MagicMock(
        spec=Redis,
    )
    codec = MagicMock(
        spec=StoredSessionCodec,
    )

    redis_client.exists.return_value = redis_result

    repository = RedisSessionRepository(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )

    result = repository.exists(
        SessionId(
            value="session-123",
        )
    )

    assert result is expected_result
    redis_client.exists.assert_called_once_with(
        "frank-ai-agent:sessions:session-123",
    )


@pytest.mark.parametrize(
    ("redis_result", "expected_result"),
    [
        (0, False),
        (1, True),
    ],
)
def test_delete_should_return_whether_session_was_deleted(
    redis_result: int,
    expected_result: bool,
) -> None:
    redis_client = MagicMock(
        spec=Redis,
    )
    codec = MagicMock(
        spec=StoredSessionCodec,
    )

    redis_client.delete.return_value = redis_result

    repository = RedisSessionRepository(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )

    result = repository.delete(
        SessionId(
            value="session-123",
        )
    )

    assert result is expected_result
    redis_client.delete.assert_called_once_with(
        "frank-ai-agent:sessions:session-123",
    )
