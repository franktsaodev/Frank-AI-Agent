from app.tools.tool_call import ToolCall


class FakeToolExecutor:
    def __init__(
        self,
        result: object | None = None,
        results: list[object] | None = None,
    ) -> None:
        self._result = result
        self._results = list(results or [])
        self.received_tool_calls: list[ToolCall] = []

    def execute(
        self,
        tool_call: ToolCall,
    ) -> object:
        self.received_tool_calls.append(tool_call)

        if self._results:
            return self._results.pop(0)

        return self._result
