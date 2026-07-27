from typing import Any

from app.tools.tool_call import ToolCall
from app.tools.tool_registry import ToolRegistry


class ToolExecutor:
    def __init__(self, tool_registry: ToolRegistry) -> None:
        self._tool_registry = tool_registry

    def execute(self, tool_call: ToolCall) -> Any:
        tool = self._tool_registry.get(tool_call.name)
        return tool.execute(**tool_call.arguments)
