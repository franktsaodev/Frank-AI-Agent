from typing import Protocol

from app.tools.tool_call import ToolCall
from app.tracing.trace_context import TraceContext


class ToolExecutorProtocol(Protocol):
    def execute(
        self,
        tool_call: ToolCall,
        trace_context: TraceContext,
    ) -> object: ...
