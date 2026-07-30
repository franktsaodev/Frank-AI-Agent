import pytest

from app.agent.agent_runner import AgentRunner
from app.exceptions.max_iterations_exceeded_error import (
    MaxIterationsExceededError,
)
from app.models.client_response import ClientResponse
from app.models.message import Message
from app.models.message_role import MessageRole
from app.tools.tool_call import ToolCall
from tests.fakes.fake_client import FakeClient
from tests.fakes.fake_tool_executor import FakeToolExecutor


def test_run_returns_text_response_when_client_returns_content() -> None:
    client = FakeClient(
        response=ClientResponse(
            content="Hello!",
        ),
    )

    tool_executor = FakeToolExecutor()

    runner = AgentRunner(
        client=client,
        tool_executor=tool_executor,
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content="Hello",
        ),
    ]

    response = runner.run(messages)

    assert response == ClientResponse(
        content="Hello!",
    )

    assert client.call_count == 1
    assert tool_executor.received_tool_calls == []


def test_run_executes_tool_call_and_returns_follow_up_response() -> None:
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

    runner = AgentRunner(
        client=client,
        tool_executor=tool_executor,
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content="What is 1 + 2?",
        ),
    ]

    response = runner.run(messages)

    assert tool_executor.received_tool_calls == [
        tool_call,
    ]

    assert client.call_count == 2

    assert response == ClientResponse(
        content="1 + 2 equals 3.",
    )


def test_run_sends_tool_result_message_to_client() -> None:
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

    runner = AgentRunner(
        client=client,
        tool_executor=tool_executor,
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content="What is 1 + 2?",
        ),
    ]

    runner.run(messages)

    second_request_messages = client.received_message_batches[1]

    assert (
        Message(
            role=MessageRole.TOOL,
            content="3",
            tool_call_id="call_123",
        )
        in second_request_messages
    )


def test_run_executes_all_tool_calls() -> None:
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

    runner = AgentRunner(
        client=client,
        tool_executor=tool_executor,
    )

    runner.run(
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


def test_run_continues_until_client_returns_text_response() -> None:
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

    runner = AgentRunner(
        client=client,
        tool_executor=tool_executor,
    )

    response = runner.run(
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


def test_run_accumulates_tool_messages_across_iterations() -> None:
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

    runner = AgentRunner(
        client=client,
        tool_executor=tool_executor,
    )

    runner.run(
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


def test_init_raises_when_max_iterations_is_less_than_one() -> None:
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
        AgentRunner(
            client=client,
            tool_executor=tool_executor,
            max_iterations=0,
        )


def test_run_raises_when_max_iterations_is_exceeded() -> None:
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

    runner = AgentRunner(
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
        runner.run(messages)

    assert client.call_count == 3

    assert tool_executor.received_tool_calls == [
        tool_call,
        tool_call,
    ]


def test_run_returns_response_on_last_allowed_iteration() -> None:
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

    runner = AgentRunner(
        client=client,
        tool_executor=tool_executor,
        max_iterations=3,
    )

    response = runner.run(
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


def test_run_sends_assistant_tool_call_message_before_tool_result() -> None:
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

    runner = AgentRunner(
        client=client,
        tool_executor=tool_executor,
    )

    runner.run(
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


def test_run_preserves_tool_call_conversation_order() -> None:
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

    runner = AgentRunner(
        client=client,
        tool_executor=tool_executor,
    )

    user_message = Message(
        role=MessageRole.USER,
        content="Calculate it.",
    )

    runner.run([user_message])

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
