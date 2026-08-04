from collections.abc import Mapping

from app.tools.tool_call import ToolCall
from app.tracing.trace_context import TraceContext
from app.types.json_types import JsonValue


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
        self.received_metadata: list[Mapping[str, JsonValue] | None] = []

    def execute(
        self,
        tool_call: ToolCall,
        trace_context: TraceContext,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> object:
        self.received_tool_calls.append(tool_call)
        self.received_trace_contexts.append(trace_context)
        self.received_metadata.append(metadata)

        if self._results:
            return self._results.pop(0)

        return self._result
