from collections.abc import Mapping
from types import MappingProxyType

from app.clock.base_clock import BaseClock
from app.tools.tool_call import ToolCall
from app.tools.tool_execution_context import (
    ToolExecutionContext,
)
from app.tools.tool_registry import ToolRegistry
from app.tracing.base_tracer import BaseTracer
from app.tracing.trace_context import TraceContext
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType
from app.types.json_types import JsonValue


class ToolExecutor:
    def __init__(
        self,
        registry: ToolRegistry,
        tracer: BaseTracer,
        clock: BaseClock,
    ) -> None:
        self._registry = registry
        self._tracer = tracer
        self._clock = clock

    def execute(
        self,
        tool_call: ToolCall,
        trace_context: TraceContext,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> object:
        tool_trace_context = trace_context.create_child()

        self._tracer.trace(
            TraceEvent(
                trace_id=tool_trace_context.trace_id,
                span_id=tool_trace_context.span_id,
                parent_span_id=tool_trace_context.parent_span_id,
                event_type=TraceEventType.TOOL_STARTED,
                metadata={
                    "tool_name": tool_call.name,
                    "tool_call_id": tool_call.call_id,
                },
            )
        )

        start_time = self._clock.now()

        try:
            tool = self._registry.get(
                tool_call.name,
            )

            metadata_copy = dict(metadata) if metadata is not None else {}

            execution_context = ToolExecutionContext(
                trace_context=tool_trace_context,
                tool_name=tool_call.name,
                tool_call_id=tool_call.call_id,
                clock=self._clock,
                metadata=MappingProxyType(
                    metadata_copy,
                ),
            )

            result = tool.execute(
                context=execution_context,
                **tool_call.arguments,
            )
        except Exception as error:
            duration_ms = (self._clock.now() - start_time) * 1000

            self._tracer.trace(
                TraceEvent(
                    trace_id=tool_trace_context.trace_id,
                    span_id=tool_trace_context.span_id,
                    parent_span_id=tool_trace_context.parent_span_id,
                    event_type=TraceEventType.TOOL_FAILED,
                    metadata={
                        "tool_name": tool_call.name,
                        "tool_call_id": tool_call.call_id,
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                        "duration_ms": duration_ms,
                    },
                )
            )
            raise

        duration_ms = (self._clock.now() - start_time) * 1000

        self._tracer.trace(
            TraceEvent(
                trace_id=tool_trace_context.trace_id,
                span_id=tool_trace_context.span_id,
                parent_span_id=tool_trace_context.parent_span_id,
                event_type=TraceEventType.TOOL_FINISHED,
                metadata={
                    "tool_name": tool_call.name,
                    "tool_call_id": tool_call.call_id,
                    "result_type": type(result).__name__,
                    "duration_ms": duration_ms,
                },
            )
        )

        return result
