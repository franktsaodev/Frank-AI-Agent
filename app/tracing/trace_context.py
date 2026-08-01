import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None = None

    def create_child(self) -> "TraceContext":
        return TraceContext(
            trace_id=self.trace_id,
            span_id=uuid.uuid4().hex,
            parent_span_id=self.span_id,
        )