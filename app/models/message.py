from dataclasses import dataclass, field

from app.models.message_role import MessageRole
from app.tools.tool_call import ToolCall


@dataclass(frozen=True)
class Message:
    role: MessageRole
    content: str | None = None
    tool_calls: tuple[ToolCall, ...] = field(
        default_factory=tuple,
    )
    tool_call_id: str | None = None
