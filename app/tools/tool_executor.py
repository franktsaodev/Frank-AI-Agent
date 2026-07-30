from typing import Any

from app.tools.tool_call import ToolCall
from app.tools.tool_registry import ToolRegistry
from app.tracing.base_tracer import BaseTracer
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        tracer: BaseTracer,
    ) -> None:
        self._registry = registry
        self._tracer = tracer

    def execute(self, tool_call: ToolCall) -> Any:
        self._tracer.trace(
            TraceEvent(
                event_type=TraceEventType.TOOL_STARTED,
                metadata={
                    "tool_name": tool_call.name,
                    "tool_call_id": tool_call.call_id,
                },
            )
        )

        try:
            tool = self._registry.get(tool_call.name)
            result = tool.execute(**tool_call.arguments)
        except Exception as error:
            self._tracer.trace(
                TraceEvent(
                    event_type=TraceEventType.TOOL_FAILED,
                    metadata={
                        "tool_name": tool_call.name,
                        "tool_call_id": tool_call.call_id,
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                    },
                )
            )
            raise

        self._tracer.trace(
            TraceEvent(
                event_type=TraceEventType.TOOL_FINISHED,
                metadata={
                    "tool_name": tool_call.name,
                    "tool_call_id": tool_call.call_id,
                    "result_type": type(result).__name__,
                },
            )
        )

        return result
