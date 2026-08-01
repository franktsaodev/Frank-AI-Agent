from unittest.mock import MagicMock, patch

from app.tracing.trace_context import TraceContext


def test_trace_context_should_store_trace_id() -> None:
    context = TraceContext(
        trace_id="test-trace-id",
        span_id="test-span-id",
    )

    assert context.trace_id == "test-trace-id"


def test_trace_context_should_store_trace_and_span_ids() -> None:
    context = TraceContext(
        trace_id="trace-123",
        span_id="span-123",
        parent_span_id="parent-span-123",
    )

    assert context.trace_id == "trace-123"
    assert context.span_id == "span-123"
    assert context.parent_span_id == "parent-span-123"


def test_root_trace_context_should_have_no_parent_span() -> None:
    context = TraceContext(
        trace_id="trace-123",
        span_id="root-span",
    )

    assert context.parent_span_id is None


@patch("app.tracing.trace_context.uuid.uuid4")
def test_create_child_should_preserve_trace_and_link_parent(
    mock_uuid4: MagicMock,
) -> None:
    mock_uuid4.return_value.hex = "child-span"

    parent_context = TraceContext(
        trace_id="trace-123",
        span_id="parent-span",
    )

    child_context = parent_context.create_child()

    assert child_context.trace_id == "trace-123"
    assert child_context.span_id == "child-span"
    assert child_context.parent_span_id == "parent-span"
