from typing import Any

from app.tools.base_tool import BaseTool


class FakeTool(BaseTool):
    def __init__(self) -> None:
        self.received_arguments: dict[str, Any] | None = None

    @property
    def name(self) -> str:
        return "fake"

    @property
    def description(self) -> str:
        return "A fake tool for testing."

    def execute(self, **kwargs: Any) -> str:
        self.received_arguments = dict(kwargs)
        return "fake result"
