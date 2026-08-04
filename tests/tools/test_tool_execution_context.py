from app.tools.tool_execution_context import (
    ToolExecutionContext,
)
from app.tracing.trace_context import TraceContext
from tests.fakes.fake_clock import FakeClock


def test_should_store_trace_context() -> None:
    trace_context = TraceContext(
        trace_id="trace-123",
        span_id="tool-span",
        parent_span_id="agent-span",
    )

    context = ToolExecutionContext(
        trace_context=trace_context,
        tool_name="calculator",
        tool_call_id="call-123",
        clock=FakeClock.for_duration(1.0),
    )

    assert context.trace_context is trace_context


def test_should_store_tool_metadata() -> None:
    trace_context = TraceContext(
        trace_id="trace-id",
        span_id="span-id",
        parent_span_id="parent-span-id",
    )

    context = ToolExecutionContext(
        trace_context=trace_context,
        tool_name="calculator",
        tool_call_id="call-123",
        clock=FakeClock.for_duration(1.0),
    )

    assert context.tool_name == "calculator"
    assert context.tool_call_id == "call-123"


def test_should_store_runtime_context() -> None:
    trace_context = TraceContext(
        trace_id="trace-123",
        span_id="tool-span",
        parent_span_id="agent-span",
    )

    clock = FakeClock.for_duration(
        1.0,
    )

    context = ToolExecutionContext(
        trace_context=trace_context,
        tool_name="calculator",
        tool_call_id="call-123",
        clock=clock,
    )

    assert context.trace_context is trace_context
    assert context.tool_name == "calculator"
    assert context.tool_call_id == "call-123"
    assert context.clock is clock


def test_should_use_empty_metadata_by_default() -> None:
    context = ToolExecutionContext(
        trace_context=TraceContext(
            trace_id="trace-123",
            span_id="tool-span",
            parent_span_id="agent-span",
        ),
        tool_name="calculator",
        tool_call_id="call-123",
        clock=FakeClock.for_duration(1.0),
    )

    assert context.metadata == {}


def test_should_store_request_metadata() -> None:
    metadata = {
        "request_id": "request-123",
        "user_id": "frank",
        "interactive": True,
    }

    context = ToolExecutionContext(
        trace_context=TraceContext(
            trace_id="trace-123",
            span_id="tool-span",
            parent_span_id="agent-span",
        ),
        tool_name="calculator",
        tool_call_id="call-123",
        clock=FakeClock.for_duration(1.0),
        metadata=metadata,
    )

    assert context.metadata == metadata
