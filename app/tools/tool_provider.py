from typing import Any

from app.tools.tool_registry import ToolRegistry
from app.tools.tool_schema_adapter import ToolSchemaAdapter


class ToolProvider:
    def __init__(
        self,
        registry: ToolRegistry,
        adapter: ToolSchemaAdapter,
    ) -> None:
        self._registry = registry
        self._adapter = adapter

    def get_tool_schemas(
        self,
    ) -> list[dict[str, Any]]:

        return self._adapter.adapt_all(self._registry.get_all())
