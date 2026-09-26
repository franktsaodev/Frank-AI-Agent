from dataclasses import replace
from datetime import datetime

from redis import Redis
from redis.exceptions import WatchError

from app.session.session_conflict_error import SessionConflictError
from app.session.session_id import SessionId
from app.session.session_not_found_error import SessionNotFoundError
from app.session.stored_session import StoredSession
from app.session.stored_session_codec import StoredSessionCodec


class RedisSessionRepository:
    def __init__(
        self,
        *,
        redis_client: Redis,
        codec: StoredSessionCodec,
        key_prefix: str,
    ) -> None:
        self._redis_client = redis_client
        self._codec = codec
        self._key_prefix = key_prefix

    def save(
        self,
        session: StoredSession,
        *,
        ttl_seconds: int,
    ) -> None:
        encoded_session = self._codec.encode(
            session,
        )

        self._redis_client.set(
            name=self._build_key(
                session.session_id,
            ),
            value=encoded_session,
            ex=ttl_seconds,
        )

    def save_if_revision(
        self,
        session: StoredSession,
        *,
        expected_revision: int,
        ttl_seconds: int,
    ) -> None:
        if session.revision != expected_revision + 1:
            raise ValueError("New session revision must increment by one.")

        key = self._build_key(session.session_id)

        for _ in range(5):
            with self._redis_client.pipeline() as pipeline:
                try:
                    pipeline.watch(key)
                    encoded_session = pipeline.get(key)

                    if encoded_session is None:
                        raise SessionNotFoundError(
                            session_id=session.session_id,
                        )

                    if isinstance(encoded_session, bytes):
                        encoded_session = encoded_session.decode("utf-8")

                    current_session = self._codec.decode(encoded_session)

                    if current_session.revision != expected_revision:
                        raise SessionConflictError(
                            session_id=session.session_id,
                        )

                    pipeline.multi()
                    pipeline.set(
                        name=key,
                        value=self._codec.encode(session),
                        ex=ttl_seconds,
                    )
                    pipeline.execute()
                    return
                except WatchError:
                    continue

        raise SessionConflictError(
            session_id=session.session_id,
        )

    def get(
        self,
        session_id: SessionId,
    ) -> StoredSession | None:
        encoded_session = self._redis_client.get(
            self._build_key(
                session_id,
            )
        )

        if encoded_session is None:
            return None

        if isinstance(encoded_session, bytes):
            encoded_session = encoded_session.decode(
                "utf-8",
            )

        return self._codec.decode(
            encoded_session,
        )

    def get_and_refresh(
        self,
        session_id: SessionId,
        *,
        last_activity_at: datetime,
        ttl_seconds: int,
    ) -> StoredSession | None:
        key = self._build_key(session_id)

        for _ in range(5):
            with self._redis_client.pipeline() as pipeline:
                try:
                    pipeline.watch(key)
                    encoded_session = pipeline.get(key)

                    if encoded_session is None:
                        return None

                    if isinstance(encoded_session, bytes):
                        encoded_session = encoded_session.decode("utf-8")

                    stored_session = self._codec.decode(encoded_session)
                    refreshed_session = replace(
                        stored_session,
                        last_activity_at=max(
                            stored_session.last_activity_at,
                            last_activity_at,
                        ),
                    )

                    pipeline.multi()
                    pipeline.set(
                        name=key,
                        value=self._codec.encode(refreshed_session),
                        ex=ttl_seconds,
                    )
                    pipeline.execute()

                    return refreshed_session
                except WatchError:
                    continue

        raise SessionConflictError(
            session_id=session_id,
        )

    def exists(
        self,
        session_id: SessionId,
    ) -> bool:
        return bool(
            self._redis_client.exists(
                self._build_key(
                    session_id,
                )
            )
        )

    def delete(
        self,
        session_id: SessionId,
    ) -> bool:
        return bool(
            self._redis_client.delete(
                self._build_key(
                    session_id,
                )
            )
        )

    def _build_key(
        self,
        session_id: SessionId,
    ) -> str:
        return f"{self._key_prefix}:{session_id.value}"
