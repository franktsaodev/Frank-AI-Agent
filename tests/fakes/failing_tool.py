from typing import Any

from app.tools.base_tool import BaseTool


class FailingTool(BaseTool):
    @property
    def name(self) -> str:
        return "failing"

    @property
    def description(self) -> str:
        return "Always fails."

    def execute(self, **kwargs: Any) -> Any:
        raise RuntimeError("Tool execution failed")
