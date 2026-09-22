from dataclasses import FrozenInstanceError

import pytest

from app.agent.chat_agent_state import ChatAgentState
from app.models.message import Message
from app.models.message_role import MessageRole


def test_create_chat_agent_state() -> None:
    state = ChatAgentState(
        messages=(
            Message(
                role=MessageRole.USER,
                content="My name is Frank.",
            ),
            Message(
                role=MessageRole.ASSISTANT,
                content="Nice to meet you, Frank.",
            ),
        ),
        facts={
            "name": "Frank",
        },
    )

    assert state.messages[0].content == "My name is Frank."
    assert state.facts == {
        "name": "Frank",
    }


def test_chat_agent_state_copies_facts() -> None:
    facts = {
        "name": "Frank",
    }

    state = ChatAgentState(
        messages=(),
        facts=facts,
    )

    facts["name"] = "Changed"

    assert state.facts == {
        "name": "Frank",
    }


def test_chat_agent_state_is_frozen() -> None:
    state = ChatAgentState(
        messages=(),
        facts={},
    )

    with pytest.raises(FrozenInstanceError):
        state.messages = ()  # pyright: ignore[reportAttributeAccessIssue]
