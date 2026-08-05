from typing import Annotated

from fastapi import APIRouter, Depends

from app.agent.chat_agent import ChatAgent
from app.api.dependencies import get_chat_agent
from app.api.models import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
)

router = APIRouter()

ChatAgentDependency = Annotated[
    ChatAgent,
    Depends(get_chat_agent),
]


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        502: {
            "model": ErrorResponse,
            "description": "The upstream AI service failed.",
        },
        503: {
            "model": ErrorResponse,
            "description": "The AI service is unavailable.",
        },
        504: {
            "model": ErrorResponse,
            "description": "The AI service request timed out.",
        },
    },
    tags=[
        "Chat",
    ],
)
def chat(
    request: ChatRequest,
    agent: ChatAgentDependency,
) -> ChatResponse:
    response = agent.chat(
        request.message,
        metadata={
            **request.metadata,
            "source": "api",
        },
    )

    return ChatResponse(
        response=response,
    )
