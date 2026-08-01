from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest

from app.clock.base_clock import BaseClock
from app.tools.tool_call import ToolCall
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_registry import ToolRegistry
from app.tracing.trace_context import TraceContext
from app.tracing.trace_event_type import TraceEventType
from tests.fakes.failing_tool import FailingTool
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_tool import FakeTool


@pytest.fixture
def create_tool_executor(
    registry: ToolRegistry,
    tracer: MagicMock,
) -> Callable[..., ToolExecutor]:
    def _create_tool_executor(
        *,
        clock: BaseClock | None = None,
    ) -> ToolExecutor:
        return ToolExecutor(
            registry=registry,
            tracer=tracer,
            clock=clock
            or FakeClock.for_duration(
                1.0,
            ),
        )

    return _create_tool_executor


def test_execute_calls_tool_with_arguments(
    create_tool_executor: Callable[..., ToolExecutor],
    registry: ToolRegistry,
    trace_context: TraceContext,
) -> None:
    fake_tool = FakeTool()
    registry.register(fake_tool)

    executor = create_tool_executor()

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
    create_tool_executor: Callable[..., ToolExecutor],
    trace_context: TraceContext,
) -> None:
    executor = create_tool_executor()

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
    create_tool_executor: Callable[..., ToolExecutor],
    registry: ToolRegistry,
    trace_context: TraceContext,
) -> None:
    registry.register(FailingTool())

    executor = create_tool_executor()

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
    create_tool_executor: Callable[..., ToolExecutor],
    registry: ToolRegistry,
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    mock_uuid4.return_value.hex = "tool-span-id"

    registry.register(FakeTool())

    executor = create_tool_executor()

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

    assert events[0].metadata["tool_name"] == "fake"
    assert events[0].metadata["tool_call_id"] == "call_123"

    assert events[1].metadata["tool_name"] == "fake"
    assert events[1].metadata["tool_call_id"] == "call_123"
    assert events[1].metadata["result_type"] == "str"
    assert events[1].metadata["duration_ms"] == 1000.0

    assert {event.trace_id for event in events} == {"test-trace-id"}

    assert {event.span_id for event in events} == {"tool-span-id"}

    assert {event.parent_span_id for event in events} == {"agent-span-id"}


@patch("app.tracing.trace_context.uuid.uuid4")
def test_execute_should_trace_tool_failed(
    mock_uuid4: MagicMock,
    create_tool_executor: Callable[..., ToolExecutor],
    registry: ToolRegistry,
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    mock_uuid4.return_value.hex = "tool-span-id"

    registry.register(FailingTool())

    executor = create_tool_executor()

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

    assert events[0].metadata["tool_name"] == "failing"
    assert events[0].metadata["tool_call_id"] == "call_456"

    assert events[1].metadata["tool_name"] == "failing"
    assert events[1].metadata["tool_call_id"] == "call_456"
    assert events[1].metadata["error_type"] == "RuntimeError"
    assert events[1].metadata["error_message"] == "Tool execution failed"
    assert events[1].metadata["duration_ms"] == 1000.0

    assert {event.trace_id for event in events} == {"test-trace-id"}

    assert {event.span_id for event in events} == {"tool-span-id"}

    assert {event.parent_span_id for event in events} == {"agent-span-id"}


@patch("app.tracing.trace_context.uuid.uuid4")
def test_execute_should_trace_tool_failed_when_tool_not_found(
    mock_uuid4: MagicMock,
    create_tool_executor: Callable[..., ToolExecutor],
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    mock_uuid4.return_value.hex = "tool-span-id"

    executor = create_tool_executor()

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

    assert events[0].metadata["tool_name"] == "missing_tool"
    assert events[0].metadata["tool_call_id"] == "call_missing"

    assert events[1].metadata["tool_name"] == "missing_tool"
    assert events[1].metadata["tool_call_id"] == "call_missing"
    assert events[1].metadata["error_type"] == "KeyError"
    assert events[1].metadata["error_message"] == "'Tool not found: missing_tool'"
    assert events[1].metadata["duration_ms"] == 1000.0

    assert {event.trace_id for event in events} == {"test-trace-id"}

    assert {event.span_id for event in events} == {"tool-span-id"}

    assert {event.parent_span_id for event in events} == {"agent-span-id"}


@patch("app.tracing.trace_context.uuid.uuid4")
def test_each_execute_should_create_a_new_tool_span(
    mock_uuid4: MagicMock,
    create_tool_executor: Callable[..., ToolExecutor],
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

    executor = create_tool_executor(
        clock=FakeClock(
            times=[
                0.0,
                1.0,
                2.0,
                3.0,
            ],
        ),
    )

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


def test_execute_should_trace_tool_duration(
    create_tool_executor: Callable[..., ToolExecutor],
    registry: ToolRegistry,
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    registry.register(FakeTool())

    executor = create_tool_executor(
        clock=FakeClock.for_duration(
            0.15,
            start_time=10.0,
        ),
    )

    executor.execute(
        tool_call=ToolCall(
            call_id="call_123",
            name="fake",
            arguments={
                "message": "hello",
                "count": 1,
            },
        ),
        trace_context=trace_context,
    )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert events[-1].event_type == TraceEventType.TOOL_FINISHED
    assert events[-1].metadata["duration_ms"] == pytest.approx(150.0)


def test_execute_should_trace_tool_duration_when_failed(
    create_tool_executor: Callable[..., ToolExecutor],
    registry: ToolRegistry,
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    registry.register(FailingTool())

    executor = create_tool_executor(
        clock=FakeClock.for_duration(
            0.4,
            start_time=20.0,
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="Tool execution failed",
    ):
        executor.execute(
            tool_call=ToolCall(
                call_id="call_456",
                name="failing",
                arguments={},
            ),
            trace_context=trace_context,
        )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert events[-1].event_type == TraceEventType.TOOL_FAILED
    assert events[-1].metadata["duration_ms"] == pytest.approx(400.0)
