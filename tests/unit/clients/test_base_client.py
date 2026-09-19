from app.models.client_response import ClientResponse
from app.models.client_stream_event import ClientStreamCompleted
from app.tracing.trace_context import TraceContext
from tests.fakes.fake_client import FakeClient


def test_stream_chat_should_fall_back_to_synchronous_chat() -> None:
    response = ClientResponse(
        content="Complete response",
    )
    client = FakeClient(
        response=response,
    )
    trace_context = TraceContext(
        trace_id="trace-123",
        span_id="span-123",
    )

    events = list(
        client.stream_chat(
            messages=[],
            trace_context=trace_context,
        )
    )

    assert events == [
        ClientStreamCompleted(
            response=response,
        )
    ]
    assert client.call_count == 1
    assert client.received_messages == []
    assert client.received_trace_contexts == [
        trace_context,
    ]
