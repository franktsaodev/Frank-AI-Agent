from typing import Annotated

from fastapi import APIRouter, Depends, status

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
from app.session.session_id import SessionId
from app.session.session_manager_protocol import (
    SessionManagerProtocol,
)

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

    return ChatResponse(
        response=response,
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
