import json
from unittest.mock import MagicMock, call, patch

import httpx
import pytest
from groq import (
    APIConnectionError,
    AuthenticationError,
    RateLimitError,
)

from app.clients.groq_client import GroqClient
from app.clock.base_clock import BaseClock
from app.config_models.groq_config import GroqConfig
from app.config_models.retry_config import RetryConfig
from app.exceptions.client_exceptions import (
    ClientAuthenticationError,
    ClientConnectionError,
    ClientRateLimitError,
)
from app.models.client_response import ClientResponse
from app.models.message import Message
from app.models.message_role import MessageRole
from app.tools.calculator_tool import CalculatorTool
from app.tools.tool_call import ToolCall
from app.tools.tool_provider import ToolProvider
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_schema_adapter import ToolSchemaAdapter
from app.tracing.base_tracer import BaseTracer
from app.tracing.trace_context import TraceContext
from app.tracing.trace_event_type import TraceEventType
from tests.fakes.fake_clock import FakeClock


def create_groq_client(
    *,
    tool_provider: ToolProvider | None = None,
    max_attempts: int = 3,
    initial_delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    model: str = "test-model",
    tracer: BaseTracer,
    clock: BaseClock | None = None,
) -> GroqClient:
    groq_config = GroqConfig(
        api_key="test-api-key",
        model=model,
    )

    retry_config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay_seconds=initial_delay_seconds,
        backoff_multiplier=backoff_multiplier,
    )

    if tool_provider is None:
        registry = ToolRegistry()
        adapter = ToolSchemaAdapter()

        tool_provider = ToolProvider(
            registry=registry,
            adapter=adapter,
        )

    return GroqClient(
        groq_config=groq_config,
        retry_config=retry_config,
        tool_provider=tool_provider,
        tracer=tracer,
        clock=clock
        or FakeClock(
            times=[
                0.0,
                1.0,
            ],
        ),
    )


def create_success_response(
    content: str,
) -> MagicMock:
    response = MagicMock()

    response.choices[0].message.content = content
    response.choices[0].message.tool_calls = None
    response.choices[0].finish_reason = "stop"

    return response


def create_tool_call_response(
    tool_calls: list,
) -> MagicMock:
    response = MagicMock()

    response.choices[0].message.content = None
    response.choices[0].message.tool_calls = tool_calls
    response.choices[0].finish_reason = "tool_calls"

    return response


@pytest.fixture
def tracer() -> MagicMock:
    return MagicMock(spec=BaseTracer)


@pytest.fixture
def groq_client(
    tracer: MagicMock,
) -> GroqClient:
    return create_groq_client(
        tracer=tracer,
    )


@pytest.fixture
def messages() -> list[Message]:
    return [
        Message(
            role=MessageRole.USER,
            content="Hello",
        )
    ]


@pytest.fixture
def trace_context() -> TraceContext:
    return TraceContext(
        trace_id="test-trace-id",
        span_id="agent-span-id",
    )


@patch("app.clients.groq_client.time.sleep")
def test_chat_retries_connection_error_then_succeeds(
    mock_sleep: MagicMock,
    groq_client: GroqClient,
    messages: list[Message],
    trace_context: TraceContext,
) -> None:
    request = httpx.Request(
        method="POST",
        url="https://api.groq.com/openai/v1/chat/completions",
    )

    connection_error = APIConnectionError(
        request=request,
    )

    successful_response = create_success_response("你好, Frank!")

    mock_create = MagicMock(
        side_effect=[
            connection_error,
            connection_error,
            successful_response,
        ]
    )

    groq_client.client.chat.completions.create = mock_create

    result = groq_client.chat(
        messages=messages,
        trace_context=trace_context,
    )

    assert result.content == "你好, Frank!"
    assert mock_create.call_count == 3

    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1.0)
    mock_sleep.assert_any_call(2.0)

    assert mock_sleep.call_args_list == [
        call(1.0),
        call(2.0),
    ]


def test_chat_raises_connection_error_after_max_attempts(
    groq_client: GroqClient,
    messages: list[Message],
    trace_context: TraceContext,
) -> None:
    request = httpx.Request(
        method="POST",
        url="https://api.groq.com/openai/v1/chat/completions",
    )

    connection_error = APIConnectionError(
        request=request,
    )

    mock_create = MagicMock(
        side_effect=connection_error,
    )

    groq_client.client.chat.completions.create = mock_create

    with pytest.raises(ClientConnectionError):
        groq_client.chat(
            messages=messages,
            trace_context=trace_context,
        )

    assert mock_create.call_count == 3


def test_chat_does_not_retry_authentication_error(
    groq_client: GroqClient,
    messages: list[Message],
    trace_context: TraceContext,
) -> None:
    request = httpx.Request(
        method="POST",
        url="https://api.groq.com/openai/v1/chat/completions",
    )

    response = httpx.Response(
        status_code=401,
        request=request,
    )

    authentication_error = AuthenticationError(
        "Invalid API Key",
        response=response,
        body={
            "error": {
                "message": "Invalid API Key",
            }
        },
    )

    mock_create = MagicMock(
        side_effect=authentication_error,
    )

    groq_client.client.chat.completions.create = mock_create

    with pytest.raises(ClientAuthenticationError):
        groq_client.chat(
            messages=messages,
            trace_context=trace_context,
        )

    assert mock_create.call_count == 1


def test_calculate_delay_uses_exponential_backoff(
    groq_client: GroqClient,
) -> None:
    assert groq_client._calculate_delay(1) == 1.0
    assert groq_client._calculate_delay(2) == 2.0
    assert groq_client._calculate_delay(3) == 4.0


@patch("app.clients.groq_client.time.sleep")
def test_chat_retries_rate_limit_error_then_succeeds(
    mock_sleep: MagicMock,
    groq_client: GroqClient,
    messages: list[Message],
    trace_context: TraceContext,
) -> None:
    request = httpx.Request(
        method="POST",
        url="https://api.groq.com/openai/v1/chat/completions",
    )

    response = httpx.Response(
        status_code=429,
        request=request,
    )

    rate_limit_error = RateLimitError(
        message="Rate limit exceeded",
        response=response,
        body=None,
    )

    successful_response = create_success_response("你好, Frank!")

    mock_create = MagicMock(
        side_effect=[
            rate_limit_error,
            rate_limit_error,
            successful_response,
        ]
    )

    groq_client.client.chat.completions.create = mock_create

    result = groq_client.chat(
        messages=messages,
        trace_context=trace_context,
    )

    assert result.content == "你好, Frank!"
    assert mock_create.call_count == 3

    assert mock_sleep.call_args_list == [
        call(1.0),
        call(2.0),
    ]


@patch("app.clients.groq_client.time.sleep")
def test_chat_raises_rate_limit_error_after_max_attempts(
    mock_sleep: MagicMock,
    groq_client: GroqClient,
    messages: list[Message],
    trace_context: TraceContext,
) -> None:
    request = httpx.Request(
        method="POST",
        url="https://api.groq.com/openai/v1/chat/completions",
    )

    response = httpx.Response(
        status_code=429,
        request=request,
    )

    rate_limit_error = RateLimitError(
        message="Rate limit exceeded",
        response=response,
        body=None,
    )

    mock_create = MagicMock(
        side_effect=rate_limit_error,
    )

    groq_client.client.chat.completions.create = mock_create

    with pytest.raises(ClientRateLimitError):
        groq_client.chat(
            messages=messages,
            trace_context=trace_context,
        )

    assert mock_create.call_count == 3

    assert mock_sleep.call_args_list == [
        call(1.0),
        call(2.0),
    ]


def test_chat_includes_tool_schemas_when_tools_registered(
    messages: list[Message],
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    registry = ToolRegistry()
    registry.register(CalculatorTool())

    adapter = ToolSchemaAdapter()

    provider = ToolProvider(
        registry=registry,
        adapter=adapter,
    )

    groq_client = create_groq_client(
        tool_provider=provider,
        tracer=tracer,
    )

    successful_response = create_success_response("好的")

    mock_create = MagicMock(
        return_value=successful_response,
    )

    groq_client.client.chat.completions.create = mock_create

    result = groq_client.chat(
        messages=messages,
        trace_context=trace_context,
    )

    kwargs = mock_create.call_args.kwargs

    assert result.content == "好的"
    assert result.tool_calls == ()
    assert "tools" in kwargs
    assert len(kwargs["tools"]) == 1
    assert kwargs["tools"][0]["function"]["name"] == "calculator"


def test_chat_omits_tools_when_no_tools_registered(
    messages: list[Message],
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    registry = ToolRegistry()
    adapter = ToolSchemaAdapter()

    provider = ToolProvider(
        registry=registry,
        adapter=adapter,
    )

    groq_client = create_groq_client(
        tool_provider=provider,
        tracer=tracer,
    )

    successful_response = create_success_response("好的")

    mock_create = MagicMock(
        return_value=successful_response,
    )

    groq_client.client.chat.completions.create = mock_create

    result = groq_client.chat(
        messages=messages,
        trace_context=trace_context,
    )

    kwargs = mock_create.call_args.kwargs

    assert result.content == "好的"
    assert result.tool_calls == ()
    assert "tools" not in kwargs


def test_chat_returns_tool_calls_when_groq_requests_tool(
    groq_client: GroqClient,
    messages: list[Message],
    trace_context: TraceContext,
) -> None:
    groq_tool_call = MagicMock()
    groq_tool_call.id = "call_123"
    groq_tool_call.function.name = "calculator"
    groq_tool_call.function.arguments = json.dumps(
        {
            "expression": "1 + 2",
        }
    )

    successful_response = create_tool_call_response([groq_tool_call])

    mock_create = MagicMock(
        return_value=successful_response,
    )

    groq_client.client.chat.completions.create = mock_create

    result = groq_client.chat(
        messages=messages,
        trace_context=trace_context,
    )

    assert result == ClientResponse(
        content=None,
        tool_calls=(
            ToolCall(
                call_id="call_123",
                name="calculator",
                arguments={
                    "expression": "1 + 2",
                },
            ),
        ),
    )

    assert mock_create.call_count == 1


def test_format_messages_includes_assistant_tool_calls(
    groq_client: GroqClient,
) -> None:
    tool_call = ToolCall(
        call_id="call_123",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content="What is 1 + 2?",
        ),
        Message(
            role=MessageRole.ASSISTANT,
            content=None,
            tool_calls=(tool_call,),
        ),
    ]

    formatted_messages = groq_client._format_messages(messages)

    assert formatted_messages == [
        {
            "role": "user",
            "content": "What is 1 + 2?",
        },
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "calculator",
                        "arguments": json.dumps(
                            {
                                "expression": "1 + 2",
                            }
                        ),
                    },
                }
            ],
        },
    ]


def test_format_messages_includes_tool_call_id(
    groq_client: GroqClient,
) -> None:
    messages = [
        Message(
            role=MessageRole.TOOL,
            content="3",
            tool_call_id="call_123",
        ),
    ]

    formatted_messages = groq_client._format_messages(messages)

    assert formatted_messages == [
        {
            "role": "tool",
            "content": "3",
            "tool_call_id": "call_123",
        },
    ]


def test_chat_sends_tool_call_conversation_to_groq(
    groq_client: GroqClient,
    trace_context: TraceContext,
) -> None:
    tool_call = ToolCall(
        call_id="call_123",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    messages = [
        Message(
            role=MessageRole.USER,
            content="What is 1 + 2?",
        ),
        Message(
            role=MessageRole.ASSISTANT,
            content=None,
            tool_calls=(tool_call,),
        ),
        Message(
            role=MessageRole.TOOL,
            content="3",
            tool_call_id="call_123",
        ),
    ]

    successful_response = create_success_response("答案是 3。")

    mock_create = MagicMock(
        return_value=successful_response,
    )

    groq_client.client.chat.completions.create = mock_create

    result = groq_client.chat(
        messages=messages,
        trace_context=trace_context,
    )

    sent_messages = mock_create.call_args.kwargs["messages"]

    assert sent_messages == [
        {
            "role": "user",
            "content": "What is 1 + 2?",
        },
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "calculator",
                        "arguments": json.dumps(
                            {
                                "expression": "1 + 2",
                            }
                        ),
                    },
                }
            ],
        },
        {
            "role": "tool",
            "content": "3",
            "tool_call_id": "call_123",
        },
    ]

    assert result == ClientResponse(
        content="答案是 3。",
    )


@patch("app.tracing.trace_context.uuid.uuid4")
def test_chat_should_trace_llm_lifecycle(
    mock_uuid4: MagicMock,
    groq_client: GroqClient,
    tracer: MagicMock,
    trace_context: TraceContext,
) -> None:
    mock_uuid4.return_value.hex = "llm-span-id"

    mock_groq_response = create_success_response("你好")

    mock_create = MagicMock(
        return_value=mock_groq_response,
    )

    groq_client.client.chat.completions.create = mock_create

    groq_client.chat(
        messages=[
            Message(
                role=MessageRole.USER,
                content="你好",
            ),
        ],
        trace_context=trace_context,
    )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.LLM_STARTED,
        TraceEventType.LLM_FINISHED,
    ]

    assert events[0].metadata == {
        "model": groq_client._groq_config.model,
        "message_count": 1,
    }

    assert events[0].metadata["model"] == groq_client._groq_config.model
    assert events[0].metadata["message_count"] == 1

    assert events[1].metadata["model"] == groq_client._groq_config.model
    assert events[1].metadata["attempt"] == 1
    assert events[1].metadata["has_tool_calls"] == False
    assert events[1].metadata["tool_call_count"] == 0
    assert events[1].metadata["duration_ms"] == 1000.0

    assert {event.trace_id for event in events} == {"test-trace-id"}

    assert {event.span_id for event in events} == {"llm-span-id"}

    assert {event.parent_span_id for event in events} == {"agent-span-id"}


@patch("app.tracing.trace_context.uuid.uuid4")
def test_chat_should_trace_llm_failed_on_authentication_error(
    mock_uuid4: MagicMock,
    groq_client: GroqClient,
    tracer: MagicMock,
    messages: list[Message],
    trace_context: TraceContext,
) -> None:
    mock_uuid4.return_value.hex = "llm-span-id"

    request = httpx.Request(
        method="POST",
        url="https://api.groq.com/openai/v1/chat/completions",
    )

    response = httpx.Response(
        status_code=401,
        request=request,
    )

    authentication_error = AuthenticationError(
        "Invalid API Key",
        response=response,
        body={
            "error": {
                "message": "Invalid API Key",
            }
        },
    )

    mock_create = MagicMock(
        side_effect=authentication_error,
    )

    groq_client.client.chat.completions.create = mock_create

    with pytest.raises(ClientAuthenticationError):
        groq_client.chat(
            messages=messages,
            trace_context=trace_context,
        )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.LLM_STARTED,
        TraceEventType.LLM_FAILED,
    ]

    assert events[1].metadata["model"] == groq_client._groq_config.model
    assert events[1].metadata["error_type"] == "ClientAuthenticationError"
    assert events[1].metadata["error_message"] == "AI client authentication failed"
    assert events[1].metadata["duration_ms"] == 1000.0

    assert {event.trace_id for event in events} == {"test-trace-id"}

    assert {event.span_id for event in events} == {"llm-span-id"}

    assert {event.parent_span_id for event in events} == {"agent-span-id"}


@patch("app.tracing.trace_context.uuid.uuid4")
@patch("app.clients.groq_client.time.sleep")
def test_chat_should_not_trace_llm_failed_when_retry_succeeds(
    mock_sleep: MagicMock,
    mock_uuid4: MagicMock,
    groq_client: GroqClient,
    tracer: MagicMock,
    messages: list[Message],
    trace_context: TraceContext,
) -> None:
    mock_uuid4.return_value.hex = "llm-span-id"

    request = httpx.Request(
        method="POST",
        url="https://api.groq.com/openai/v1/chat/completions",
    )

    connection_error = APIConnectionError(
        request=request,
    )

    successful_response = create_success_response("你好, Frank!")

    mock_create = MagicMock(
        side_effect=[
            connection_error,
            successful_response,
        ]
    )

    groq_client.client.chat.completions.create = mock_create

    groq_client.chat(
        messages=messages,
        trace_context=trace_context,
    )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.LLM_STARTED,
        TraceEventType.LLM_FINISHED,
    ]

    assert TraceEventType.LLM_FAILED not in [event.event_type for event in events]

    assert {event.span_id for event in events} == {"llm-span-id"}

    assert {event.parent_span_id for event in events} == {"agent-span-id"}


@patch("app.tracing.trace_context.uuid.uuid4")
@patch("app.clients.groq_client.time.sleep")
def test_chat_should_trace_llm_failed_after_max_attempts(
    mock_sleep: MagicMock,
    mock_uuid4: MagicMock,
    groq_client: GroqClient,
    tracer: MagicMock,
    messages: list[Message],
    trace_context: TraceContext,
) -> None:
    mock_uuid4.return_value.hex = "llm-span-id"

    request = httpx.Request(
        method="POST",
        url="https://api.groq.com/openai/v1/chat/completions",
    )

    connection_error = APIConnectionError(
        request=request,
    )

    mock_create = MagicMock(
        side_effect=connection_error,
    )

    groq_client.client.chat.completions.create = mock_create

    with pytest.raises(ClientConnectionError):
        groq_client.chat(
            messages=messages,
            trace_context=trace_context,
        )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    assert [event.event_type for event in events] == [
        TraceEventType.LLM_STARTED,
        TraceEventType.LLM_FAILED,
    ]

    assert events[1].metadata["model"] == groq_client._groq_config.model
    assert events[1].metadata["error_type"] == "ClientConnectionError"
    assert events[1].metadata["error_message"] == "Failed to connect to AI service"

    assert mock_create.call_count == 3

    assert {event.trace_id for event in events} == {"test-trace-id"}

    assert {event.span_id for event in events} == {"llm-span-id"}

    assert {event.parent_span_id for event in events} == {"agent-span-id"}


def test_chat_should_trace_llm_duration(
    tracer: MagicMock,
    messages: list[Message],
    trace_context: TraceContext,
) -> None:
    clock = FakeClock(
        times=[
            10.0,
            10.35,
        ],
    )

    groq_client = create_groq_client(
        tracer=tracer,
        clock=clock,
    )

    groq_client.client.chat.completions.create = MagicMock(
        return_value=create_success_response("你好"),
    )

    groq_client.chat(
        messages=messages,
        trace_context=trace_context,
    )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    finished_event = events[-1]

    assert finished_event.event_type == TraceEventType.LLM_FINISHED
    assert finished_event.metadata["duration_ms"] == pytest.approx(350.0)


def test_chat_should_trace_llm_duration_when_failed(
    tracer: MagicMock,
    messages: list[Message],
    trace_context: TraceContext,
) -> None:
    clock = FakeClock(
        times=[
            20.0,
            20.4,
        ],
    )

    groq_client = create_groq_client(
        tracer=tracer,
        clock=clock,
    )

    request = httpx.Request(
        method="POST",
        url="https://api.groq.com/openai/v1/chat/completions",
    )

    response = httpx.Response(
        status_code=401,
        request=request,
    )

    groq_client.client.chat.completions.create = MagicMock(
        side_effect=AuthenticationError(
            "Invalid API Key",
            response=response,
            body=None,
        ),
    )

    with pytest.raises(ClientAuthenticationError):
        groq_client.chat(
            messages=messages,
            trace_context=trace_context,
        )

    events = [trace_call.args[0] for trace_call in tracer.trace.call_args_list]

    failed_event = events[-1]

    assert failed_event.event_type == TraceEventType.LLM_FAILED
    assert failed_event.metadata["duration_ms"] == pytest.approx(400.0)
