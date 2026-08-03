import json

from app.tracing.trace_event import TraceEvent
from app.types.json_types import JsonObject


class TraceEventSerializer:
    def to_dict(
        self,
        event: TraceEvent,
    ) -> JsonObject:
        result: JsonObject = {
            "timestamp": event.timestamp.isoformat(),
            "trace_id": event.trace_id,
            "span_id": event.span_id,
            "parent_span_id": event.parent_span_id,
            "event_type": event.event_type.value,
            "metadata": event.metadata,
        }

        return result

    def to_json(
        self,
        event: TraceEvent,
    ) -> str:
        return json.dumps(
            self.to_dict(event),
            ensure_ascii=False,
        )
