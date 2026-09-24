import logging
from collections.abc import Callable, Iterable, Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.api.chat_stream_serializer import (
    serialize_chat_stream_error,
    serialize_chat_stream_event,
)
from app.api.models import (
    ChatRequest,
    ChatResponse,
    ClearSessionHistoryResponse,
    CreateSessionResponse,
    DeleteSessionResponse,
    HistoryMessageResponse,
    SessionDetailResponse,
    SessionHistoryResponse,
)
from app.api.session_dependencies import (
    get_session_manager,
)
from app.exceptions.client_exceptions import (
    AIClientError,
    ClientAuthenticationError,
    ClientConnectionError,
    ClientRateLimitError,
    ClientTimeoutError,
)
from app.models.chat_stream_event import (
    ChatStreamCompleted,
    ChatStreamEvent,
)
from app.session.session_id import SessionId
from app.session.session_manager_protocol import (
    SessionManagerProtocol,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sessions",
    tags=[
        "Sessions",
    ],
)

SessionManagerDependency = Annotated[
    SessionManagerProtocol,
    Depends(get_session_manager),
]


@router.post(
    "",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    manager: SessionManagerDependency,
) -> CreateSessionResponse:
    session = manager.create()

    return CreateSessionResponse(
        session_id=session.session_id.value,
    )


@router.post(
    "/{session_id}/chat",
    response_model=ChatResponse,
)
def chat_with_session(
    session_id: str,
    request: ChatRequest,
    manager: SessionManagerDependency,
) -> ChatResponse:
    session = manager.get(
        SessionId(
            value=session_id,
        )
    )

    response = session.agent.chat(
        request.message,
        metadata={
            **request.metadata,
            "source": "api",
            "session_id": session_id,
        },
    )

    manager.save(
        session,
    )

    return ChatResponse(
        response=response,
    )


@router.post(
    "/{session_id}/chat/stream",
)
def stream_chat_with_session(
    session_id: str,
    request: ChatRequest,
    manager: SessionManagerDependency,
) -> StreamingResponse:
    session = manager.get(
        SessionId(
            value=session_id,
        )
    )

    events = session.agent.stream_chat(
        request.message,
        metadata={
            **request.metadata,
            "source": "api",
            "session_id": session_id,
        },
    )

    serialized_events = _serialize_chat_stream(
        events,
        on_completed=lambda: manager.save(
            session,
        ),
    )

    return StreamingResponse(
        content=serialized_events,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete(
    "/{session_id}",
    response_model=DeleteSessionResponse,
)
def delete_session(
    session_id: str,
    manager: SessionManagerDependency,
) -> DeleteSessionResponse:
    manager.delete(
        SessionId(
            value=session_id,
        )
    )

    return DeleteSessionResponse(
        deleted=True,
    )


@router.get(
    "/{session_id}/history",
    response_model=SessionHistoryResponse,
)
def get_session_history(
    session_id: str,
    manager: SessionManagerDependency,
) -> SessionHistoryResponse:
    session = manager.get(
        SessionId(
            value=session_id,
        )
    )

    history = session.agent.get_history()

    return SessionHistoryResponse(
        session_id=session_id,
        messages=[
            HistoryMessageResponse(
                role=message.role.value,
                content=message.content,
            )
            for message in history
        ],
    )


@router.delete(
    "/{session_id}/history",
    response_model=ClearSessionHistoryResponse,
)
def clear_session_history(
    session_id: str,
    manager: SessionManagerDependency,
) -> ClearSessionHistoryResponse:
    session = manager.get(
        SessionId(
            value=session_id,
        )
    )

    session.agent.clear_history()

    manager.save(
        session,
    )

    return ClearSessionHistoryResponse(
        cleared=True,
    )


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
)
def get_session_detail(
    session_id: str,
    manager: SessionManagerDependency,
) -> SessionDetailResponse:
    session = manager.get(
        SessionId(
            value=session_id,
        )
    )

    return SessionDetailResponse(
        session_id=session.session_id.value,
        created_at=session.created_at,
        last_activity_at=session.last_activity_at,
        message_count=len(session.agent.get_history()),
    )


def _serialize_chat_stream(
    events: Iterable[ChatStreamEvent],
    *,
    on_completed: Callable[[], None],
) -> Iterator[str]:
    try:
        for event in events:
            serialized_event = serialize_chat_stream_event(
                event,
            )

            if isinstance(
                event,
                ChatStreamCompleted,
            ):
                on_completed()

            yield serialized_event

    except ClientAuthenticationError as error:
        logger.warning(
            "Streaming AI client authentication failed: %s",
            error,
        )

        yield serialize_chat_stream_error(
            error="client_authentication_error",
            message="The AI service authentication failed.",
        )

    except ClientTimeoutError as error:
        logger.warning(
            "Streaming AI client request timed out: %s",
            error,
        )

        yield serialize_chat_stream_error(
            error="client_timeout",
            message="The AI service took too long to respond.",
        )

    except ClientConnectionError as error:
        logger.warning(
            "Streaming AI client connection failed: %s",
            error,
        )

        yield serialize_chat_stream_error(
            error="client_connection_error",
            message="Unable to connect to the AI service.",
        )

    except ClientRateLimitError as error:
        logger.warning(
            "Streaming AI client rate limit exceeded: %s",
            error,
        )

        yield serialize_chat_stream_error(
            error="client_rate_limit",
            message=(
                "The AI service is temporarily rate limited. Please try again later."
            ),
        )

    except AIClientError:
        logger.exception("Unexpected streaming AI client error")
        yield serialize_chat_stream_error(
            error="ai_client_error",
            message="The AI service returned an error.",
        )
    except Exception:
        logger.exception("Unexpected chat stream error")
        yield serialize_chat_stream_error(
            error="stream_error",
            message="The chat stream failed unexpectedly.",
        )
