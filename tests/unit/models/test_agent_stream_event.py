from dataclasses import FrozenInstanceError

import pytest

from app.models.agent_stream_event import (
    AgentContentDelta,
    AgentStreamCompleted,
)
from app.models.client_response import ClientResponse


def test_content_delta_stores_content() -> None:
    event = AgentContentDelta(
        content="你好",
    )

    assert event.content == "你好"


def test_content_delta_rejects_empty_content() -> None:
    with pytest.raises(
        ValueError,
        match="Agent content delta cannot be empty",
    ):
        AgentContentDelta(
            content="",
        )


def test_content_delta_is_frozen() -> None:
    event = AgentContentDelta(
        content="你好",
    )

    with pytest.raises(FrozenInstanceError):
        event.content = "更新"  # pyright: ignore[reportAttributeAccessIssue]


def test_completed_event_stores_response() -> None:
    response = ClientResponse(
        content="完成",
    )

    event = AgentStreamCompleted(
        response=response,
    )

    assert event.response is response


def test_completed_event_is_frozen() -> None:
    event = AgentStreamCompleted(
        response=ClientResponse(
            content="完成",
        ),
    )

    with pytest.raises(FrozenInstanceError):
        event.response = ClientResponse(  # pyright: ignore[reportAttributeAccessIssue]
            content="更新",
        )
