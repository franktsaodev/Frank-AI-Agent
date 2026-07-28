from typing import Any

from app.tools.base_tool import BaseTool


class FailingTool(BaseTool):
    @property
    def name(self) -> str:
        return "failing"

    @property
    def description(self) -> str:
        return "Always fails."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        }

    def execute(self, **kwargs: Any) -> Any:
        raise RuntimeError("Tool execution failed")
