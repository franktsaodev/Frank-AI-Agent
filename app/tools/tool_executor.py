from typing import Any

from app.tools.tool_registry import ToolRegistry


class ToolExecutor:
    def __init__(self, tool_registry: ToolRegistry) -> None:
        self._tool_registry = tool_registry

    def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> Any:
        tool = self._tool_registry.get(tool_name)
        return tool.execute(**arguments)
