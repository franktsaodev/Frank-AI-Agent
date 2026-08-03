from collections.abc import Sequence

from app.tools.base_tool import BaseTool
from app.tools.plugins.tool_plugin_load_result import (
    ToolPluginLoadResult,
)
from app.tools.plugins.tool_plugin_protocol import (
    ToolPluginProtocol,
)
from app.tools.tool_registry import ToolRegistry


class ToolPluginLoader:
    def __init__(
        self,
        registry: ToolRegistry,
    ) -> None:
        self._registry = registry

    def load(
        self,
        plugins: Sequence[ToolPluginProtocol],
    ) -> ToolPluginLoadResult:
        tools = self._collect_tools(
            plugins,
        )

        self._validate_tools(
            tools,
        )

        for tool in tools:
            self._registry.register(tool)

        return ToolPluginLoadResult(
            plugin_count=len(plugins),
            tool_names=tuple(tool.name for tool in tools),
        )

    def _collect_tools(
        self,
        plugins: Sequence[ToolPluginProtocol],
    ) -> list[BaseTool]:
        return [tool for plugin in plugins for tool in plugin.get_tools()]

    def _validate_tools(
        self,
        tools: Sequence[BaseTool],
    ) -> None:
        seen_names: set[str] = set()

        for tool in tools:
            if tool.name in seen_names:
                raise ValueError(f"Duplicate tool in plugins: {tool.name}")

            if self._registry.contains(tool.name):
                raise ValueError(f"Tool already registered: {tool.name}")

            seen_names.add(tool.name)
