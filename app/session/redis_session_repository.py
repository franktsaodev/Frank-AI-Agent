from redis import Redis

from app.session.session_id import SessionId
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
