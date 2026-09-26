from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from redis import Redis
from redis.exceptions import WatchError

from app.agent.chat_agent_state import ChatAgentState
from app.session.redis_session_repository import (
    RedisSessionRepository,
)
from app.session.session_conflict_error import SessionConflictError
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


def test_get_and_refresh_should_retry_with_latest_session_after_conflict() -> None:
    redis_client = MagicMock(spec=Redis)
    codec = MagicMock(spec=StoredSessionCodec)

    older_session = create_stored_session()
    newer_session = replace(
        older_session,
        agent_state=ChatAgentState(
            messages=(),
            facts={"user_name": "Updated Frank"},
        ),
    )
    refreshed_at = older_session.last_activity_at + timedelta(minutes=1)

    first_pipeline = MagicMock()
    first_pipeline.__enter__.return_value = first_pipeline
    first_pipeline.get.return_value = "older"
    first_pipeline.execute.side_effect = WatchError()

    second_pipeline = MagicMock()
    second_pipeline.__enter__.return_value = second_pipeline
    second_pipeline.get.return_value = "newer"
    second_pipeline.execute.return_value = [True]

    redis_client.pipeline.side_effect = [
        first_pipeline,
        second_pipeline,
    ]
    codec.decode.side_effect = [
        older_session,
        newer_session,
    ]
    codec.encode.side_effect = [
        "older-refreshed",
        "newer-refreshed",
    ]

    repository = RedisSessionRepository(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )

    result = repository.get_and_refresh(
        older_session.session_id,
        last_activity_at=refreshed_at,
        ttl_seconds=3600,
    )

    assert result == replace(
        newer_session,
        last_activity_at=refreshed_at,
    )
    assert redis_client.pipeline.call_count == 2
    first_pipeline.execute.assert_called_once_with()
    second_pipeline.execute.assert_called_once_with()
    second_pipeline.set.assert_called_once_with(
        name="frank-ai-agent:sessions:session-123",
        value="newer-refreshed",
        ex=3600,
    )
    codec.encode.assert_any_call(result)


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


def test_save_if_revision_should_reject_stale_session() -> None:
    redis_client = MagicMock(spec=Redis)
    codec = MagicMock(spec=StoredSessionCodec)

    current_session = replace(
        create_stored_session(),
        revision=4,
    )
    stale_update = replace(
        current_session,
        agent_state=ChatAgentState(
            messages=(),
            facts={"user_name": "Stale update"},
        ),
    )

    pipeline = MagicMock()
    pipeline.__enter__.return_value = pipeline
    pipeline.get.return_value = "current-session"

    redis_client.pipeline.return_value = pipeline
    codec.decode.return_value = current_session

    repository = RedisSessionRepository(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )

    with pytest.raises(SessionConflictError) as exception_info:
        repository.save_if_revision(
            stale_update,
            expected_revision=3,
            ttl_seconds=3600,
        )

    assert exception_info.value.session_id == stale_update.session_id
    pipeline.watch.assert_called_once_with(
        "frank-ai-agent:sessions:session-123",
    )
    pipeline.multi.assert_not_called()
    pipeline.set.assert_not_called()


def test_save_if_revision_should_write_next_revision_with_ttl() -> None:
    redis_client = MagicMock(spec=Redis)
    codec = MagicMock(spec=StoredSessionCodec)

    current_session = replace(create_stored_session(), revision=3)
    updated_session = replace(current_session, revision=4)

    pipeline = MagicMock()
    pipeline.__enter__.return_value = pipeline
    pipeline.get.return_value = "current-session"
    pipeline.execute.return_value = [True]

    redis_client.pipeline.return_value = pipeline
    codec.decode.return_value = current_session
    codec.encode.return_value = "updated-session"

    repository = RedisSessionRepository(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )

    repository.save_if_revision(
        updated_session,
        expected_revision=3,
        ttl_seconds=3600,
    )

    pipeline.watch.assert_called_once_with(
        "frank-ai-agent:sessions:session-123",
    )
    pipeline.multi.assert_called_once_with()
    pipeline.set.assert_called_once_with(
        name="frank-ai-agent:sessions:session-123",
        value="updated-session",
        ex=3600,
    )
    pipeline.execute.assert_called_once_with()
    codec.encode.assert_called_once_with(updated_session)


def test_save_if_revision_should_reject_update_after_watch_conflict() -> None:
    redis_client = MagicMock(spec=Redis)
    codec = MagicMock(spec=StoredSessionCodec)

    original_session = replace(create_stored_session(), revision=3)
    candidate = replace(original_session, revision=4)
    winning_session = replace(
        original_session,
        revision=4,
        agent_state=ChatAgentState(
            messages=(),
            facts={"user_name": "Winning request"},
        ),
    )

    first_pipeline = MagicMock()
    first_pipeline.__enter__.return_value = first_pipeline
    first_pipeline.get.return_value = "original-session"
    first_pipeline.execute.side_effect = WatchError()

    second_pipeline = MagicMock()
    second_pipeline.__enter__.return_value = second_pipeline
    second_pipeline.get.return_value = "winning-session"

    redis_client.pipeline.side_effect = [
        first_pipeline,
        second_pipeline,
    ]
    codec.decode.side_effect = [
        original_session,
        winning_session,
    ]
    codec.encode.return_value = "candidate-session"

    repository = RedisSessionRepository(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )

    with pytest.raises(SessionConflictError):
        repository.save_if_revision(
            candidate,
            expected_revision=3,
            ttl_seconds=3600,
        )

    assert redis_client.pipeline.call_count == 2
    first_pipeline.execute.assert_called_once_with()
    second_pipeline.watch.assert_called_once_with(
        "frank-ai-agent:sessions:session-123",
    )
    second_pipeline.multi.assert_not_called()
    second_pipeline.set.assert_not_called()


def test_get_and_refresh_should_report_conflict_after_retry_limit() -> None:
    redis_client = MagicMock(spec=Redis)
    codec = MagicMock(spec=StoredSessionCodec)
    stored_session = create_stored_session()

    pipeline = MagicMock()
    pipeline.__enter__.return_value = pipeline
    pipeline.get.return_value = "stored-session"
    pipeline.execute.side_effect = WatchError()

    redis_client.pipeline.return_value = pipeline
    codec.decode.return_value = stored_session
    codec.encode.return_value = "refreshed-session"

    repository = RedisSessionRepository(
        redis_client=redis_client,
        codec=codec,
        key_prefix="frank-ai-agent:sessions",
    )

    with pytest.raises(SessionConflictError) as exception_info:
        repository.get_and_refresh(
            stored_session.session_id,
            last_activity_at=stored_session.last_activity_at,
            ttl_seconds=3600,
        )

    assert exception_info.value.session_id == stored_session.session_id
    assert pipeline.execute.call_count == 5
