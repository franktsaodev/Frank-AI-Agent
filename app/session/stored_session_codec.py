import json
from datetime import datetime
from typing import cast

from app.agent.chat_agent_state import ChatAgentState
from app.models.message import Message
from app.models.message_role import MessageRole
from app.session.session_id import SessionId
from app.session.stored_session import (
    STORED_SESSION_SCHEMA_VERSION,
    StoredSession,
)
from app.session.stored_session_decode_error import (
    StoredSessionDecodeError,
)
from app.tools.tool_call import ToolCall
from app.types.json_types import JsonObject, JsonValue


class StoredSessionCodec:
    def encode(
        self,
        session: StoredSession,
    ) -> str:
        messages: list[JsonValue] = [
            self._encode_message(message) for message in session.agent_state.messages
        ]
        facts: JsonObject = {
            key: value for key, value in session.agent_state.facts.items()
        }

        payload: JsonObject = {
            "schema_version": session.schema_version,
            "session_id": session.session_id.value,
            "created_at": session.created_at.isoformat(),
            "last_activity_at": session.last_activity_at.isoformat(),
            "agent_state": {
                "messages": messages,
                "facts": facts,
            },
        }

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def decode(
        self,
        payload: str,
    ) -> StoredSession:
        try:
            return self._decode(
                payload,
            )
        except StoredSessionDecodeError:
            raise
        except (
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise StoredSessionDecodeError("Invalid stored session payload.") from error

    def _decode(
        self,
        payload: str,
    ) -> StoredSession:
        data = self._decode_json_object(
            json.loads(payload),
        )
        schema_version = self._decode_integer(
            data["schema_version"],
        )

        if schema_version != STORED_SESSION_SCHEMA_VERSION:
            raise StoredSessionDecodeError(
                f"Unsupported stored session schema version: {schema_version!r}"
            )

        agent_state_data = self._decode_json_object(
            data["agent_state"],
        )
        message_data = self._decode_list(
            agent_state_data["messages"],
        )
        facts = self._decode_string_map(
            agent_state_data["facts"],
        )

        return StoredSession(
            session_id=SessionId(
                value=self._decode_string(
                    data["session_id"],
                ),
            ),
            created_at=self._decode_datetime(
                data["created_at"],
            ),
            last_activity_at=self._decode_datetime(
                data["last_activity_at"],
            ),
            agent_state=ChatAgentState(
                messages=tuple(
                    self._decode_message(
                        self._decode_json_object(item),
                    )
                    for item in message_data
                ),
                facts=facts,
            ),
        )

    def _encode_message(
        self,
        message: Message,
    ) -> JsonObject:
        tool_calls: list[JsonValue] = [
            self._encode_tool_call(tool_call) for tool_call in message.tool_calls
        ]

        return {
            "role": message.role.value,
            "content": message.content,
            "tool_calls": tool_calls,
            "tool_call_id": message.tool_call_id,
        }

    def _encode_tool_call(
        self,
        tool_call: ToolCall,
    ) -> JsonObject:
        return {
            "call_id": tool_call.call_id,
            "name": tool_call.name,
            "arguments": tool_call.arguments,
        }

    def _decode_message(
        self,
        data: JsonObject,
    ) -> Message:
        tool_call_data = self._decode_list(
            data["tool_calls"],
        )

        return Message(
            role=MessageRole(
                self._decode_string(
                    data["role"],
                )
            ),
            content=self._decode_optional_string(
                data["content"],
            ),
            tool_calls=tuple(
                self._decode_tool_call(
                    self._decode_json_object(item),
                )
                for item in tool_call_data
            ),
            tool_call_id=self._decode_optional_string(
                data["tool_call_id"],
            ),
        )

    def _decode_tool_call(
        self,
        data: JsonObject,
    ) -> ToolCall:
        return ToolCall(
            call_id=self._decode_string(
                data["call_id"],
            ),
            name=self._decode_string(
                data["name"],
            ),
            arguments=self._decode_json_object(
                data["arguments"],
            ),
        )

    def _decode_integer(
        self,
        value: object,
    ) -> int:
        if type(value) is not int:
            raise TypeError("Stored session value must be an integer.")

        return value

    def _decode_list(
        self,
        value: object,
    ) -> list[object]:
        if not isinstance(value, list):
            raise TypeError("Stored session value must be a list.")

        return value

    def _decode_string(
        self,
        value: object,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError("Stored session value must be a string.")

        return value

    def _decode_string_map(
        self,
        value: object,
    ) -> dict[str, str]:
        result = self._decode_json_object(
            value,
        )

        if not all(isinstance(item, str) for item in result.values()):
            raise TypeError("Stored session map values must be strings.")

        return cast(
            dict[str, str],
            result,
        )

    def _decode_datetime(
        self,
        value: object,
    ) -> datetime:
        if not isinstance(value, str):
            raise TypeError("Stored session datetime must be a string.")

        result = datetime.fromisoformat(
            value,
        )

        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError("Stored session datetime must include a timezone.")

        return result

    def _decode_optional_string(
        self,
        value: object,
    ) -> str | None:
        if value is not None and not isinstance(value, str):
            raise TypeError("Stored session value must be a string or null.")

        return value

    def _decode_json_object(
        self,
        value: object,
    ) -> JsonObject:
        if not isinstance(value, dict):
            raise TypeError("Stored session value must be a JSON object.")

        return cast(
            JsonObject,
            value,
        )
