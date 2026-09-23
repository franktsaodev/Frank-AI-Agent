import json
from datetime import UTC, datetime

import pytest

from app.agent.chat_agent_state import ChatAgentState
from app.models.message import Message
from app.models.message_role import MessageRole
from app.session.session_id import SessionId
from app.session.stored_session import (
    STORED_SESSION_SCHEMA_VERSION,
    StoredSession,
)
from app.session.stored_session_codec import StoredSessionCodec
from app.session.stored_session_decode_error import (
    StoredSessionDecodeError,
)
from app.tools.tool_call import ToolCall


def create_stored_session() -> StoredSession:
    return StoredSession(
        session_id=SessionId(
            value="session-123",
        ),
        created_at=datetime(
            2026,
            9,
            22,
            10,
            0,
            tzinfo=UTC,
        ),
        last_activity_at=datetime(
            2026,
            9,
            22,
            10,
            30,
            tzinfo=UTC,
        ),
        agent_state=ChatAgentState(
            messages=(
                Message(
                    role=MessageRole.USER,
                    content="Calculate 123 * 456.",
                ),
                Message(
                    role=MessageRole.ASSISTANT,
                    tool_calls=(
                        ToolCall(
                            call_id="call-123",
                            name="calculator",
                            arguments={
                                "operation": "multiply",
                                "a": 123,
                                "b": 456,
                            },
                        ),
                    ),
                ),
                Message(
                    role=MessageRole.TOOL,
                    content="56088",
                    tool_call_id="call-123",
                ),
                Message(
                    role=MessageRole.ASSISTANT,
                    content="56088",
                ),
            ),
            facts={
                "user_name": "Frank",
            },
        ),
    )


def test_encode_should_serialize_complete_session_state() -> None:
    stored_session = create_stored_session()

    result = StoredSessionCodec().encode(
        stored_session,
    )

    assert json.loads(result) == {
        "schema_version": STORED_SESSION_SCHEMA_VERSION,
        "session_id": "session-123",
        "created_at": "2026-09-22T10:00:00+00:00",
        "last_activity_at": "2026-09-22T10:30:00+00:00",
        "agent_state": {
            "messages": [
                {
                    "role": "user",
                    "content": "Calculate 123 * 456.",
                    "tool_calls": [],
                    "tool_call_id": None,
                },
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "call_id": "call-123",
                            "name": "calculator",
                            "arguments": {
                                "operation": "multiply",
                                "a": 123,
                                "b": 456,
                            },
                        }
                    ],
                    "tool_call_id": None,
                },
                {
                    "role": "tool",
                    "content": "56088",
                    "tool_calls": [],
                    "tool_call_id": "call-123",
                },
                {
                    "role": "assistant",
                    "content": "56088",
                    "tool_calls": [],
                    "tool_call_id": None,
                },
            ],
            "facts": {
                "user_name": "Frank",
            },
        },
    }


def test_decode_should_round_trip_complete_session_state() -> None:
    codec = StoredSessionCodec()
    expected_session = create_stored_session()

    encoded_session = codec.encode(
        expected_session,
    )
    decoded_session = codec.decode(
        encoded_session,
    )

    assert decoded_session == expected_session


@pytest.mark.parametrize(
    "payload",
    [
        "not-json",
        "[]",
        '{"schema_version":1}',
    ],
)
def test_decode_should_reject_invalid_payload(
    payload: str,
) -> None:
    with pytest.raises(
        StoredSessionDecodeError,
        match="Invalid stored session payload",
    ):
        StoredSessionCodec().decode(
            payload,
        )


def test_decode_should_reject_unsupported_schema_version() -> None:
    payload = json.dumps(
        {
            "schema_version": 999,
        }
    )

    with pytest.raises(
        StoredSessionDecodeError,
        match="Unsupported stored session schema version: 999",
    ):
        StoredSessionCodec().decode(
            payload,
        )


def test_decode_should_reject_datetime_without_timezone() -> None:
    codec = StoredSessionCodec()
    payload = json.loads(
        codec.encode(
            create_stored_session(),
        )
    )
    payload["created_at"] = "2026-09-22T10:00:00"

    with pytest.raises(
        StoredSessionDecodeError,
        match="Invalid stored session payload",
    ):
        codec.decode(
            json.dumps(payload),
        )


def test_decode_should_reject_non_string_message_content() -> None:
    codec = StoredSessionCodec()
    payload = json.loads(
        codec.encode(
            create_stored_session(),
        )
    )
    payload["agent_state"]["messages"][0]["content"] = 123

    with pytest.raises(
        StoredSessionDecodeError,
        match="Invalid stored session payload",
    ):
        codec.decode(
            json.dumps(payload),
        )


def test_decode_should_reject_non_object_tool_call_arguments() -> None:
    codec = StoredSessionCodec()
    payload = json.loads(
        codec.encode(
            create_stored_session(),
        )
    )
    payload["agent_state"]["messages"][1]["tool_calls"][0]["arguments"] = []

    with pytest.raises(
        StoredSessionDecodeError,
        match="Invalid stored session payload",
    ):
        codec.decode(
            json.dumps(payload),
        )


def test_decode_should_reject_boolean_schema_version() -> None:
    codec = StoredSessionCodec()
    payload = json.loads(
        codec.encode(
            create_stored_session(),
        )
    )
    payload["schema_version"] = True

    with pytest.raises(
        StoredSessionDecodeError,
        match="Invalid stored session payload",
    ):
        codec.decode(
            json.dumps(payload),
        )


def test_decode_should_reject_non_string_fact_value() -> None:
    codec = StoredSessionCodec()
    payload = json.loads(
        codec.encode(
            create_stored_session(),
        )
    )
    payload["agent_state"]["facts"]["age"] = 32

    with pytest.raises(
        StoredSessionDecodeError,
        match="Invalid stored session payload",
    ):
        codec.decode(
            json.dumps(payload),
        )


def test_decode_should_reject_non_string_tool_call_id() -> None:
    codec = StoredSessionCodec()
    payload = json.loads(
        codec.encode(
            create_stored_session(),
        )
    )
    payload["agent_state"]["messages"][1]["tool_calls"][0]["call_id"] = 123

    with pytest.raises(
        StoredSessionDecodeError,
        match="Invalid stored session payload",
    ):
        codec.decode(
            json.dumps(payload),
        )
