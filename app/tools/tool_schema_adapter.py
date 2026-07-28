from copy import deepcopy
from typing import Any

from app.tools.base_tool import BaseTool


class ToolSchemaAdapter:
    def adapt(self, tool: BaseTool) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": deepcopy(tool.input_schema),
            },
        }

    def adapt_all(
        self,
        tools: list[BaseTool],
    ) -> list[dict[str, Any]]:
        return [self.adapt(tool) for tool in tools]
