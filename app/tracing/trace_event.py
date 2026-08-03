from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.tracing.trace_event_type import TraceEventType
from app.types.json_types import JsonObject


@dataclass(frozen=True)
class TraceEvent:
    trace_id: str
    span_id: str
    event_type: TraceEventType
    parent_span_id: str | None = None
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(UTC),
    )
    metadata: JsonObject = field(default_factory=dict)
