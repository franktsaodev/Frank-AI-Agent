from collections.abc import Sequence
from copy import deepcopy

from app.tools.base_tool import BaseTool
from app.tools.tool_schema_types import ToolSchema


class ToolSchemaAdapter:
    def adapt(self, tool: BaseTool) -> ToolSchema:
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
        tools: Sequence[BaseTool],
    ) -> list[ToolSchema]:
        return [self.adapt(tool) for tool in tools]
