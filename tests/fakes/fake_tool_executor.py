from app.tools.tool_call import ToolCall
from app.tracing.trace_context import TraceContext


class FakeToolExecutor:
    def __init__(
        self,
        result: object | None = None,
        results: list[object] | None = None,
    ) -> None:
        self._result = result
        self._results = list(results or [])
        self.received_tool_calls: list[ToolCall] = []
        self.received_trace_contexts: list[TraceContext] = []

    def execute(
        self,
        tool_call: ToolCall,
        trace_context: TraceContext,
    ) -> object:
        self.received_tool_calls.append(tool_call)
        self.received_trace_contexts.append(trace_context)

        if self._results:
            return self._results.pop(0)

        return self._result
