from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pytest

from app.agent.agent_runner import AgentRunner
from app.clients.base_client import BaseClient
from app.exceptions.max_iterations_exceeded_error import (
    MaxIterationsExceededError,
)
from app.models.client_response import ClientResponse
from app.models.message import Message
from app.models.message_role import MessageRole
from app.tools.tool_call import ToolCall
from app.tools.tool_executor import ToolExecutor
from app.tracing.base_tracer import BaseTracer
from app.tracing.trace_event_type import TraceEventType
from tests.fakes.fake_client import FakeClient
from tests.fakes.fake_clock import FakeClock
from tests.fakes.fake_tool_executor import FakeToolExecutor


@pytest.fixture
def create_agent_runner() -> Callable[..., AgentRunner]:
    def _create_agent_runner(
        *,
        client: BaseClient,
        tool_executor: ToolExecutor | FakeToolExecutor,
        tracer: BaseTracer | None = None,
        clock: FakeClock | None = None,
        max_iterations: int = 10,
    ) -> AgentRunner:
        return AgentRunner(
            client=client,
            tool_executor=tool_executor,
            tracer=tracer or MagicMock(spec=BaseTracer),
            clock=clock
            or FakeClock.for_duration(
                1.0,
            ),
            max_iterations=max_iterations,
        )

    return _create_agent_runner


def test_run_returns_text_response_when_client_returns_content(
    create_agent_runner,
) -> None:
    client = FakeClient(
        response=ClientResponse(
            content="Hello!",
        ),
    )

    tool_executor = FakeToolExecutor()

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content="Hello",
        ),
    ]

    response = agent_runner.run(messages)

    assert response == ClientResponse(
        content="Hello!",
    )

    assert client.call_count == 1
    assert tool_executor.received_tool_calls == []


def test_run_executes_tool_call_and_returns_follow_up_response(
    create_agent_runner,
) -> None:
    tool_call = ToolCall(
        call_id="call_123",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    client = FakeClient(
        responses=[
            ClientResponse(
                tool_calls=(tool_call,),
            ),
            ClientResponse(
                content="1 + 2 equals 3.",
            ),
        ],
    )

    tool_executor = FakeToolExecutor(
        result=3,
    )

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content="What is 1 + 2?",
        ),
    ]

    response = agent_runner.run(messages)

    assert tool_executor.received_tool_calls == [
        tool_call,
    ]

    assert client.call_count == 2

    assert response == ClientResponse(
        content="1 + 2 equals 3.",
    )


def test_run_sends_tool_result_message_to_client(
    create_agent_runner,
) -> None:
    tool_call = ToolCall(
        call_id="call_123",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    client = FakeClient(
        responses=[
            ClientResponse(
                tool_calls=(tool_call,),
            ),
            ClientResponse(
                content="The answer is 3.",
            ),
        ],
    )

    tool_executor = FakeToolExecutor(
        result=3,
    )

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content="What is 1 + 2?",
        ),
    ]

    agent_runner.run(messages)

    second_request_messages = client.received_message_batches[1]

    assert (
        Message(
            role=MessageRole.TOOL,
            content="3",
            tool_call_id="call_123",
        )
        in second_request_messages
    )


def test_run_executes_all_tool_calls(
    create_agent_runner,
) -> None:
    first_call = ToolCall(
        call_id="call_1",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    second_call = ToolCall(
        call_id="call_2",
        name="calculator",
        arguments={
            "expression": "3 + 4",
        },
    )

    client = FakeClient(
        responses=[
            ClientResponse(
                tool_calls=(
                    first_call,
                    second_call,
                ),
            ),
            ClientResponse(
                content="The answers are 3 and 7.",
            ),
        ],
    )

    tool_executor = FakeToolExecutor(
        result=3,
    )

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
    )

    agent_runner.run(
        [
            Message(
                role=MessageRole.USER,
                content="Calculate these.",
            ),
        ]
    )

    assert tool_executor.received_tool_calls == [
        first_call,
        second_call,
    ]


def test_run_continues_until_client_returns_text_response(
    create_agent_runner,
) -> None:
    first_tool_call = ToolCall(
        call_id="call_1",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    second_tool_call = ToolCall(
        call_id="call_2",
        name="calculator",
        arguments={
            "expression": "3 * 4",
        },
    )

    client = FakeClient(
        responses=[
            ClientResponse(
                tool_calls=(first_tool_call,),
            ),
            ClientResponse(
                tool_calls=(second_tool_call,),
            ),
            ClientResponse(
                content="The final answer is 12.",
            ),
        ],
    )

    tool_executor = FakeToolExecutor(
        results=[
            3,
            12,
        ],
    )

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
    )

    response = agent_runner.run(
        [
            Message(
                role=MessageRole.USER,
                content="Calculate 1 + 2, then multiply it by 4.",
            ),
        ]
    )

    assert client.call_count == 3

    assert tool_executor.received_tool_calls == [
        first_tool_call,
        second_tool_call,
    ]

    assert response == ClientResponse(
        content="The final answer is 12.",
    )


def test_run_accumulates_tool_messages_across_iterations(
    create_agent_runner,
) -> None:
    first_tool_call = ToolCall(
        call_id="call_1",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    second_tool_call = ToolCall(
        call_id="call_2",
        name="calculator",
        arguments={
            "expression": "3 * 4",
        },
    )

    client = FakeClient(
        responses=[
            ClientResponse(
                tool_calls=(first_tool_call,),
            ),
            ClientResponse(
                tool_calls=(second_tool_call,),
            ),
            ClientResponse(
                content="12",
            ),
        ],
    )

    tool_executor = FakeToolExecutor(
        results=[
            3,
            12,
        ],
    )

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
    )

    agent_runner.run(
        [
            Message(
                role=MessageRole.USER,
                content="Calculate it.",
            ),
        ]
    )

    third_request_messages = client.received_message_batches[2]

    assert (
        Message(
            role=MessageRole.TOOL,
            content="3",
            tool_call_id="call_1",
        )
        in third_request_messages
    )

    assert (
        Message(
            role=MessageRole.TOOL,
            content="12",
            tool_call_id="call_2",
        )
        in third_request_messages
    )


def test_init_raises_when_max_iterations_is_less_than_one(
    create_agent_runner,
) -> None:
    client = FakeClient(
        response=ClientResponse(
            content="Hello!",
        ),
    )

    tool_executor = FakeToolExecutor()

    with pytest.raises(
        ValueError,
        match="max_iterations must be at least 1",
    ):
        create_agent_runner(
            client=client,
            tool_executor=tool_executor,
            max_iterations=0,
        )


def test_run_raises_when_max_iterations_is_exceeded(
    create_agent_runner,
) -> None:
    tool_call = ToolCall(
        call_id="call_123",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    client = FakeClient(
        responses=[
            ClientResponse(
                tool_calls=(tool_call,),
            ),
            ClientResponse(
                tool_calls=(tool_call,),
            ),
            ClientResponse(
                tool_calls=(tool_call,),
            ),
        ],
    )

    tool_executor = FakeToolExecutor(
        results=[
            3,
            3,
            3,
        ],
    )

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
        max_iterations=3,
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content="Keep calculating.",
        ),
    ]

    with pytest.raises(
        MaxIterationsExceededError,
        match="maximum number of iterations: 3",
    ):
        agent_runner.run(messages)

    assert client.call_count == 3

    assert tool_executor.received_tool_calls == [
        tool_call,
        tool_call,
    ]


def test_run_returns_response_on_last_allowed_iteration(
    create_agent_runner,
) -> None:
    first_tool_call = ToolCall(
        call_id="call_1",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    second_tool_call = ToolCall(
        call_id="call_2",
        name="calculator",
        arguments={
            "expression": "3 * 4",
        },
    )

    client = FakeClient(
        responses=[
            ClientResponse(
                tool_calls=(first_tool_call,),
            ),
            ClientResponse(
                tool_calls=(second_tool_call,),
            ),
            ClientResponse(
                content="The final answer is 12.",
            ),
        ],
    )

    tool_executor = FakeToolExecutor(
        results=[
            3,
            12,
        ],
    )

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
        max_iterations=3,
    )

    response = agent_runner.run(
        [
            Message(
                role=MessageRole.USER,
                content="Calculate it.",
            ),
        ]
    )

    assert client.call_count == 3

    assert response == ClientResponse(
        content="The final answer is 12.",
    )


def test_run_sends_assistant_tool_call_message_before_tool_result(
    create_agent_runner,
) -> None:
    tool_call = ToolCall(
        call_id="call_123",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    client = FakeClient(
        responses=[
            ClientResponse(
                tool_calls=(tool_call,),
            ),
            ClientResponse(
                content="The answer is 3.",
            ),
        ],
    )

    tool_executor = FakeToolExecutor(
        result=3,
    )

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
    )

    agent_runner.run(
        [
            Message(
                role=MessageRole.USER,
                content="What is 1 + 2?",
            ),
        ]
    )

    second_request_messages = client.received_message_batches[1]

    assistant_message = Message(
        role=MessageRole.ASSISTANT,
        content=None,
        tool_calls=(tool_call,),
    )

    tool_message = Message(
        role=MessageRole.TOOL,
        content="3",
        tool_call_id="call_123",
    )

    assert assistant_message in second_request_messages

    assert tool_message in second_request_messages

    assert second_request_messages.index(
        assistant_message
    ) < second_request_messages.index(tool_message)


def test_run_preserves_tool_call_conversation_order(
    create_agent_runner,
) -> None:
    first_call = ToolCall(
        call_id="call_1",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    second_call = ToolCall(
        call_id="call_2",
        name="calculator",
        arguments={
            "expression": "3 * 4",
        },
    )

    client = FakeClient(
        responses=[
            ClientResponse(
                tool_calls=(first_call,),
            ),
            ClientResponse(
                tool_calls=(second_call,),
            ),
            ClientResponse(
                content="The answer is 12.",
            ),
        ],
    )

    tool_executor = FakeToolExecutor(
        results=[
            3,
            12,
        ],
    )

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
    )

    user_message = Message(
        role=MessageRole.USER,
        content="Calculate it.",
    )

    agent_runner.run([user_message])

    third_request_messages = client.received_message_batches[2]

    assert third_request_messages == [
        user_message,
        Message(
            role=MessageRole.ASSISTANT,
            content=None,
            tool_calls=(first_call,),
        ),
        Message(
            role=MessageRole.TOOL,
            content="3",
            tool_call_id="call_1",
        ),
        Message(
            role=MessageRole.ASSISTANT,
            content=None,
            tool_calls=(second_call,),
        ),
        Message(
            role=MessageRole.TOOL,
            content="12",
            tool_call_id="call_2",
        ),
    ]


def test_run_should_trace_agent_lifecycle(
    create_agent_runner,
) -> None:
    client = MagicMock(spec=BaseClient)
    tool_executor = MagicMock(spec=ToolExecutor)
    tracer = MagicMock(spec=BaseTracer)

    client.chat.return_value = ClientResponse(
        content="完成",
        tool_calls=(),
    )

    runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content="你好",
        )
    ]

    runner.run(messages)

    events = [call.args[0] for call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.AGENT_STARTED,
        TraceEventType.AGENT_FINISHED,
    ]

    assert events[0].metadata["message_count"] == 1
    assert events[0].metadata["max_iterations"] == 10

    assert events[1].metadata["iterations"] == 1
    assert events[1].metadata["final_message_count"] == 1
    assert events[1].metadata["duration_ms"] == 1000.0


def test_run_should_trace_agent_failed_when_max_iterations_exceeded(
    create_agent_runner,
) -> None:
    client = MagicMock(spec=BaseClient)
    tool_executor = MagicMock(spec=ToolExecutor)
    tracer = MagicMock(spec=BaseTracer)

    client.chat.return_value = ClientResponse(
        content=None,
        tool_calls=(
            ToolCall(
                call_id="call-1",
                name="calculator",
                arguments={"expression": "1 + 1"},
            ),
        ),
    )

    runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
        max_iterations=1,
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content="幫我計算 1 + 1",
        )
    ]

    with pytest.raises(MaxIterationsExceededError) as exception_info:
        runner.run(messages)

    events = [call.args[0] for call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.AGENT_STARTED,
        TraceEventType.AGENT_FAILED,
    ]

    assert events[1].metadata["error_type"] == "MaxIterationsExceededError"
    assert events[1].metadata["error_message"] == str(exception_info.value)
    assert events[1].metadata["duration_ms"] == 1000.0


@patch(
    "app.agent.agent_runner.uuid.uuid4",
)
def test_run_should_use_root_span_for_agent_lifecycle_events(
    mock_uuid4: MagicMock,
    create_agent_runner,
) -> None:
    trace_uuid = MagicMock()
    trace_uuid.hex = "test-trace-id"

    span_uuid = MagicMock()
    span_uuid.hex = "agent-span-id"

    mock_uuid4.side_effect = [
        trace_uuid,
        span_uuid,
    ]

    client = MagicMock(spec=BaseClient)
    tool_executor = MagicMock(spec=ToolExecutor)
    tracer = MagicMock(spec=BaseTracer)

    client.chat.return_value = ClientResponse(
        content="完成",
        tool_calls=(),
    )

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
    )

    agent_runner.run(
        messages=[],
    )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.AGENT_STARTED,
        TraceEventType.AGENT_FINISHED,
    ]

    assert {event.trace_id for event in events} == {"test-trace-id"}

    assert {event.span_id for event in events} == {"agent-span-id"}

    assert {event.parent_span_id for event in events} == {None}


def test_run_should_pass_trace_context_to_client(
    create_agent_runner,
) -> None:
    client = FakeClient(
        response=ClientResponse(
            content="完成",
        ),
    )

    tool_executor = FakeToolExecutor()
    tracer = MagicMock(spec=BaseTracer)

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
    )

    agent_runner.run(
        messages=[
            Message(
                role=MessageRole.USER,
                content="你好",
            ),
        ],
    )

    events = [call.args[0] for call in tracer.trace.call_args_list]

    assert len(client.received_trace_contexts) == 1

    received_context = client.received_trace_contexts[0]

    assert received_context.trace_id == events[0].trace_id


def test_run_should_pass_trace_context_to_tool_executor(
    create_agent_runner,
) -> None:
    tool_call = ToolCall(
        call_id="call-123",
        name="calculator",
        arguments={
            "expression": "1 + 1",
        },
    )

    client = FakeClient(
        responses=[
            ClientResponse(
                content=None,
                tool_calls=(tool_call,),
            ),
            ClientResponse(
                content="答案是 2。",
            ),
        ],
    )

    tool_executor = FakeToolExecutor(
        result=2,
    )

    tracer = MagicMock(spec=BaseTracer)

    agent_runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
    )

    agent_runner.run(
        messages=[
            Message(
                role=MessageRole.USER,
                content="幫我計算 1 + 1",
            ),
        ],
    )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert len(tool_executor.received_trace_contexts) == 1

    received_context = tool_executor.received_trace_contexts[0]

    assert received_context.trace_id == events[0].trace_id


def test_run_should_trace_agent_duration(
    create_agent_runner,
) -> None:
    client = FakeClient(
        response=ClientResponse(
            content="完成",
        ),
    )

    tool_executor = FakeToolExecutor()
    tracer = MagicMock(spec=BaseTracer)

    clock = FakeClock.for_duration(
        0.25,
        start_time=10.0,
    )

    runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
        clock=clock,
    )

    runner.run(
        messages=[
            Message(
                role=MessageRole.USER,
                content="你好",
            ),
        ],
    )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert events[-1].event_type == TraceEventType.AGENT_FINISHED

    assert events[-1].metadata["duration_ms"] == 250.0


def test_run_should_trace_agent_duration_when_failed(
    create_agent_runner,
) -> None:
    client = MagicMock(spec=BaseClient)
    tool_executor = MagicMock(spec=ToolExecutor)
    tracer = MagicMock(spec=BaseTracer)

    client.chat.side_effect = RuntimeError("Agent failed")

    clock = FakeClock.for_duration(
        0.4,
        start_time=20.0,
    )

    runner = create_agent_runner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
        clock=clock,
    )

    with pytest.raises(
        RuntimeError,
        match="Agent failed",
    ):
        runner.run(
            messages=[],
        )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert events[-1].event_type == TraceEventType.AGENT_FAILED

    assert events[-1].metadata["duration_ms"] == pytest.approx(400.0)
