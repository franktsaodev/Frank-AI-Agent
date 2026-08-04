from collections.abc import Mapping
from dataclasses import dataclass, field

from app.clock.base_clock import BaseClock
from app.tracing.trace_context import TraceContext
from app.types.json_types import JsonValue


@dataclass(frozen=True)
class ToolExecutionContext:
    trace_context: TraceContext
    tool_name: str
    tool_call_id: str
    clock: BaseClock
    metadata: Mapping[str, JsonValue] = field(
        default_factory=dict,
    )
