import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.agent.agent_runner import AgentRunner
from app.clients.groq_client import GroqClient
from app.config_models.groq_config import GroqConfig
from app.config_models.retry_config import RetryConfig
from app.models.message import Message
from app.models.message_role import MessageRole
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_provider import ToolProvider
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_schema_adapter import ToolSchemaAdapter
from app.tracing.base_tracer import BaseTracer
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
def groq_client(
    registry: ToolRegistry,
    tracer: MagicMock,
) -> GroqClient:
    tool_provider = ToolProvider(
        registry=registry,
        adapter=ToolSchemaAdapter(),
    )

    return GroqClient(
        groq_config=GroqConfig(
            api_key="test-api-key",
            model="test-model",
        ),
        retry_config=RetryConfig(
            max_attempts=3,
            initial_delay_seconds=0,
            backoff_multiplier=1,
        ),
        tool_provider=tool_provider,
        tracer=tracer,
    )


@pytest.fixture
def tool_executor(
    registry: ToolRegistry,
    tracer: MagicMock,
) -> ToolExecutor:
    return ToolExecutor(
        registry=registry,
        tracer=tracer,
    )


@pytest.fixture
def agent_runner(
    groq_client: GroqClient,
    tool_executor: ToolExecutor,
    tracer: MagicMock,
) -> AgentRunner:
    return AgentRunner(
        client=groq_client,
        tool_executor=tool_executor,
        tracer=tracer,
        max_iterations=10,
    )


def create_success_response(content: str) -> MagicMock:
    response = MagicMock()

    response.choices[0].message.content = content
    response.choices[0].message.tool_calls = None
    response.choices[0].finish_reason = "stop"

    return response


def create_tool_call_response(
    *,
    call_id: str,
    name: str,
    arguments: dict[str, Any],
) -> MagicMock:
    tool_call = MagicMock()
    tool_call.id = call_id
    tool_call.function.name = name
    tool_call.function.arguments = json.dumps(arguments)

    response = MagicMock()
    response.choices[0].message.content = None
    response.choices[0].message.tool_calls = [tool_call]
    response.choices[0].finish_reason = "tool_calls"

    return response


def test_agent_should_trace_complete_lifecycle_without_tool(
    agent_runner: AgentRunner,
    groq_client: GroqClient,
    tracer: MagicMock,
) -> None:
    mock_create = MagicMock(
        return_value=create_success_response("你好，Frank！"),
    )

    groq_client.client.chat.completions.create = mock_create

    messages = [
        Message(
            role=MessageRole.USER,
            content="你好",
        )
    ]

    result = agent_runner.run(messages)

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.AGENT_STARTED,
        TraceEventType.LLM_STARTED,
        TraceEventType.LLM_FINISHED,
        TraceEventType.AGENT_FINISHED,
    ]

    assert result.content == "你好，Frank！"


def test_agent_should_trace_complete_lifecycle_with_tool(
    agent_runner: AgentRunner,
    groq_client: GroqClient,
    registry: ToolRegistry,
    tracer: MagicMock,
) -> None:
    registry.register(FakeTool())

    tool_response = create_tool_call_response(
        call_id="call_123",
        name="fake",
        arguments={
            "message": "hello",
            "count": 3,
        },
    )

    final_response = create_success_response(
        "工具已執行完成",
    )

    mock_create = MagicMock(
        side_effect=[
            tool_response,
            final_response,
        ]
    )

    groq_client.client.chat.completions.create = mock_create

    messages = [
        Message(
            role=MessageRole.USER,
            content="請使用 fake tool",
        )
    ]

    result = agent_runner.run(messages)

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.AGENT_STARTED,
        TraceEventType.LLM_STARTED,
        TraceEventType.LLM_FINISHED,
        TraceEventType.TOOL_STARTED,
        TraceEventType.TOOL_FINISHED,
        TraceEventType.LLM_STARTED,
        TraceEventType.LLM_FINISHED,
        TraceEventType.AGENT_FINISHED,
    ]

    assert mock_create.call_count == 2

    assert result.content == "工具已執行完成"


def test_agent_should_trace_complete_lifecycle_when_tool_fails(
    agent_runner: AgentRunner,
    groq_client: GroqClient,
    registry: ToolRegistry,
    tracer: MagicMock,
) -> None:
    registry.register(FailingTool())

    tool_response = create_tool_call_response(
        call_id="call_456",
        name="failing",
        arguments={},
    )

    mock_create = MagicMock(
        return_value=tool_response,
    )

    groq_client.client.chat.completions.create = mock_create

    messages = [
        Message(
            role=MessageRole.USER,
            content="請執行 failing tool",
        )
    ]

    with pytest.raises(
        RuntimeError,
        match="Tool execution failed",
    ):
        agent_runner.run(messages)

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.AGENT_STARTED,
        TraceEventType.LLM_STARTED,
        TraceEventType.LLM_FINISHED,
        TraceEventType.TOOL_STARTED,
        TraceEventType.TOOL_FAILED,
        TraceEventType.AGENT_FAILED,
    ]
