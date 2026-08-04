from typing import Any

from app.tools.base_tool import BaseTool
from app.tools.tool_execution_context import (
    ToolExecutionContext,
)
from app.types.json_types import JsonObject


class FakeTool(BaseTool):
    def __init__(self) -> None:
        self.received_arguments: dict[str, Any] = {}
        self.received_context: ToolExecutionContext | None = None

    @property
    def name(self) -> str:
        return "fake"

    @property
    def description(self) -> str:
        return "A fake tool for testing."

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
    ) -> str:
        self.received_context = context
        self.received_arguments = kwargs

        return "fake result"
