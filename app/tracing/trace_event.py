from dataclasses import dataclass, field
from typing import Any

from app.tracing.trace_event_type import TraceEventType


@dataclass(frozen=True)
class TraceEvent:
    trace_id: str
    event_type: TraceEventType
    metadata: dict[str, Any] = field(default_factory=dict)
