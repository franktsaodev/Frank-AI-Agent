from typing import Any, Never

from app.tools.base_tool import BaseTool
from app.tools.tool_execution_context import (
    ToolExecutionContext,
)
from app.types.json_types import JsonObject


class FailingTool(BaseTool):
    @property
    def name(self) -> str:
        return "failing"

    @property
    def description(self) -> str:
        return "Always fails."

    @property
    def input_schema(self) -> JsonObject:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        }

    def execute(
        self,
        *,
        context: ToolExecutionContext,
        **kwargs: Any,
    ) -> Never:
        del context
        del kwargs

        raise RuntimeError("Tool execution failed")
