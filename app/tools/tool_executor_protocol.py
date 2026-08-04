from collections.abc import Mapping
from typing import Protocol

from app.tools.tool_call import ToolCall
from app.tracing.trace_context import TraceContext
from app.types.json_types import JsonValue


class ToolExecutorProtocol(Protocol):
    def execute(
        self,
        tool_call: ToolCall,
        trace_context: TraceContext,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> object: ...
