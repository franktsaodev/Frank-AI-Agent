from typing import Any

from app.tools.tool_call import ToolCall


class FakeToolExecutor:
    def __init__(
        self,
        result: Any = "Fake tool result",
    ) -> None:
        self.result = result
        self.received_tool_calls: list[ToolCall] = []

    def execute(
        self,
        tool_call: ToolCall,
    ) -> Any:
        self.received_tool_calls.append(tool_call)

        return self.result
