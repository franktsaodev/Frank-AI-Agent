from dataclasses import dataclass, field

from app.tools.tool_call import ToolCall


@dataclass(frozen=True)
class ClientResponse:
    content: str | None = None
    tool_calls: tuple[ToolCall, ...] = field(
        default_factory=tuple,
    )

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)
