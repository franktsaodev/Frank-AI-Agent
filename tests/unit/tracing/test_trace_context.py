import pytest

from app.tracing.trace_context import TraceContext


def test_trace_context_should_store_trace_id() -> None:
    context = TraceContext(
        trace_id="test-trace-id",
    )

    assert context.trace_id == "test-trace-id"
