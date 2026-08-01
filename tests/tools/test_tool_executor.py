from unittest.mock import MagicMock, patch

import pytest

from app.tools.tool_call import ToolCall
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_registry import ToolRegistry
from app.tracing.base_tracer import BaseTracer
from app.tracing.trace_context import TraceContext
from app.tracing.trace_event_type import TraceEventType
from tests.fakes.failing_tool import FailingTool
from tests.fakes.fake_tool import FakeTool


@pytest.fixture
def tracer() -> MagicMock:
    return MagicMock(spec=BaseTracer)


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry()


@pytest.fixture
def executor(
    registry: ToolRegistry,
    tracer: MagicMock,
) -> ToolExecutor:
    return ToolExecutor(
        registry=registry,
        tracer=tracer,
    )


@pytest.fixture
def trace_context() -> TraceContext:
    return TraceContext(
        trace_id="test-trace-id",
        span_id="agent-span-id",
    )


def test_execute_calls_tool_with_arguments(
    executor: ToolExecutor,
    registry: ToolRegistry,
    trace_context: TraceContext,
) -> None:
    fake_tool = FakeTool()
    registry.register(fake_tool)

    tool_call = ToolCall(
        call_id="",
        name="fake",
        arguments={
            "message": "hello",
            "count": 3,
        },
    )

    result = executor.execute(
        tool_call=tool_call,
        trace_context=trace_context,
    )

    assert result == "fake result"
    assert fake_tool.received_arguments == {
        "message": "hello",
        "count": 3,
    }


def test_execute_raises_error_when_tool_does_not_exist(
    executor: ToolExecutor,
    trace_context: TraceContext,
) -> None:
    with pytest.raises(
        KeyError,
        match="Tool not found: weather",
    ):
        executor.execute(
            tool_call=ToolCall(
                call_id="",
                name="weather",
                arguments={},
            ),
            trace_context=trace_context,
        )


def test_execute_propagates_tool_error(
    executor: ToolExecutor,
    registry: ToolRegistry,
    trace_context: TraceContext,
) -> None:
    registry.register(FailingTool())

    with pytest.raises(
        RuntimeError,
        match="Tool execution failed",
    ):
        executor.execute(
            tool_call=ToolCall(
                call_id="",
                name="failing",
                arguments={},
            ),
            trace_context=trace_context,
        )


@patch("app.tracing.trace_context.uuid.uuid4")
def test_execute_should_trace_tool_lifecycle(
    mock_uuid4: MagicMock,
    executor: ToolExecutor,
    registry: ToolRegistry,
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    mock_uuid4.return_value.hex = "tool-span-id"

    registry.register(FakeTool())

    tool_call = ToolCall(
        call_id="call_123",
        name="fake",
        arguments={
            "message": "hello",
            "count": 3,
        },
    )

    result = executor.execute(
        tool_call=tool_call,
        trace_context=trace_context,
    )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert result == "fake result"

    assert [event.event_type for event in events] == [
        TraceEventType.TOOL_STARTED,
        TraceEventType.TOOL_FINISHED,
    ]

    assert events[0].metadata == {
        "tool_name": "fake",
        "tool_call_id": "call_123",
    }

    assert events[1].metadata == {
        "tool_name": "fake",
        "tool_call_id": "call_123",
        "result_type": "str",
    }

    assert {event.trace_id for event in events} == {"test-trace-id"}

    assert {event.span_id for event in events} == {"tool-span-id"}

    assert {event.parent_span_id for event in events} == {"agent-span-id"}


@patch("app.tracing.trace_context.uuid.uuid4")
def test_execute_should_trace_tool_failed(
    mock_uuid4: MagicMock,
    executor: ToolExecutor,
    registry: ToolRegistry,
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    mock_uuid4.return_value.hex = "tool-span-id"

    registry.register(FailingTool())

    tool_call = ToolCall(
        call_id="call_456",
        name="failing",
        arguments={},
    )

    with pytest.raises(
        RuntimeError,
        match="Tool execution failed",
    ):
        executor.execute(
            tool_call=tool_call,
            trace_context=trace_context,
        )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.TOOL_STARTED,
        TraceEventType.TOOL_FAILED,
    ]

    assert events[0].metadata == {
        "tool_name": "failing",
        "tool_call_id": "call_456",
    }

    assert events[1].metadata == {
        "tool_name": "failing",
        "tool_call_id": "call_456",
        "error_type": "RuntimeError",
        "error_message": "Tool execution failed",
    }

    assert {event.trace_id for event in events} == {"test-trace-id"}

    assert {event.span_id for event in events} == {"tool-span-id"}

    assert {event.parent_span_id for event in events} == {"agent-span-id"}


@patch("app.tracing.trace_context.uuid.uuid4")
def test_execute_should_trace_tool_failed_when_tool_not_found(
    mock_uuid4: MagicMock,
    executor: ToolExecutor,
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    mock_uuid4.return_value.hex = "tool-span-id"

    tool_call = ToolCall(
        call_id="call_missing",
        name="missing_tool",
        arguments={},
    )

    with pytest.raises(
        KeyError,
        match="Tool not found: missing_tool",
    ):
        executor.execute(
            tool_call=tool_call,
            trace_context=trace_context,
        )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.TOOL_STARTED,
        TraceEventType.TOOL_FAILED,
    ]

    assert events[0].metadata == {
        "tool_name": "missing_tool",
        "tool_call_id": "call_missing",
    }

    assert events[1].metadata == {
        "tool_name": "missing_tool",
        "tool_call_id": "call_missing",
        "error_type": "KeyError",
        "error_message": "'Tool not found: missing_tool'",
    }

    assert {event.trace_id for event in events} == {"test-trace-id"}

    assert {event.span_id for event in events} == {"tool-span-id"}

    assert {event.parent_span_id for event in events} == {"agent-span-id"}


@patch("app.tracing.trace_context.uuid.uuid4")
def test_each_execute_should_create_a_new_tool_span(
    mock_uuid4: MagicMock,
    executor: ToolExecutor,
    registry: ToolRegistry,
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    first_uuid = MagicMock()
    first_uuid.hex = "tool-span-1"

    second_uuid = MagicMock()
    second_uuid.hex = "tool-span-2"

    mock_uuid4.side_effect = [
        first_uuid,
        second_uuid,
    ]

    registry.register(FakeTool())

    first_call = ToolCall(
        call_id="call_1",
        name="fake",
        arguments={
            "message": "first",
            "count": 1,
        },
    )

    second_call = ToolCall(
        call_id="call_2",
        name="fake",
        arguments={
            "message": "second",
            "count": 2,
        },
    )

    executor.execute(
        tool_call=first_call,
        trace_context=trace_context,
    )

    executor.execute(
        tool_call=second_call,
        trace_context=trace_context,
    )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert [event.span_id for event in events] == [
        "tool-span-1",
        "tool-span-1",
        "tool-span-2",
        "tool-span-2",
    ]

    assert {event.parent_span_id for event in events} == {"agent-span-id"}
