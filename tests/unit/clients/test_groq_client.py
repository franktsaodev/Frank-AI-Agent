from unittest.mock import MagicMock, call, patch

import httpx
import pytest
from groq import (
    APIConnectionError,
    AuthenticationError,
    RateLimitError,
)

from app.clients.groq_client import GroqClient
from app.config_models.groq_config import GroqConfig
from app.config_models.retry_config import RetryConfig
from app.exceptions.client_exceptions import (
    ClientAuthenticationError,
    ClientConnectionError,
    ClientRateLimitError,
)
from app.models.message import Message
from app.models.message_role import MessageRole
from app.tools.calculator_tool import CalculatorTool
from app.tools.tool_provider import ToolProvider
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_schema_adapter import ToolSchemaAdapter


def create_groq_client(
    *,
    tool_provider: ToolProvider | None = None,
    max_attempts: int = 3,
    initial_delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    model: str = "test-model",
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
    )


@pytest.fixture
def groq_client() -> GroqClient:
    return create_groq_client()


@pytest.fixture
def messages() -> list[Message]:
    return [
        Message(
            role=MessageRole.USER,
            content="Hello",
        )
    ]


@patch("app.clients.groq_client.time.sleep")
def test_chat_retries_connection_error_then_succeeds(
    mock_sleep: MagicMock,
    groq_client: GroqClient,
    messages: list[Message],
) -> None:
    request = httpx.Request(
        method="POST",
        url="https://api.groq.com/openai/v1/chat/completions",
    )

    connection_error = APIConnectionError(
        request=request,
    )

    successful_response = MagicMock()
    successful_response.choices[0].message.content = "你好, Frank!"
    successful_response.choices[0].finish_reason = "stop"

    mock_create = MagicMock(
        side_effect=[
            connection_error,
            connection_error,
            successful_response,
        ]
    )

    groq_client.client.chat.completions.create = mock_create

    result = groq_client.chat(messages)

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
        groq_client.chat(messages)

    assert mock_create.call_count == 3


def test_chat_does_not_retry_authentication_error(
    groq_client: GroqClient,
    messages: list[Message],
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
        groq_client.chat(messages)

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

    successful_response = MagicMock()
    successful_response.choices[0].message.content = "你好, Frank!"

    mock_create = MagicMock(
        side_effect=[
            rate_limit_error,
            rate_limit_error,
            successful_response,
        ]
    )

    groq_client.client.chat.completions.create = mock_create

    result = groq_client.chat(messages)

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
        groq_client.chat(messages)

    assert mock_create.call_count == 3

    assert mock_sleep.call_args_list == [
        call(1.0),
        call(2.0),
    ]


def test_chat_includes_tool_schemas_when_tools_registered(
    messages: list[Message],
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
    )

    successful_response = MagicMock()
    successful_response.choices[0].message.content = "好的"
    successful_response.choices[0].finish_reason = "stop"

    mock_create = MagicMock(
        return_value=successful_response,
    )

    groq_client.client.chat.completions.create = mock_create

    result = groq_client.chat(messages)

    kwargs = mock_create.call_args.kwargs

    assert result.content == "好的"
    assert result.tool_calls == ()
    assert "tools" in kwargs
    assert len(kwargs["tools"]) == 1
    assert kwargs["tools"][0]["function"]["name"] == "calculator"


def test_chat_omits_tools_when_no_tools_registered(
    messages: list[Message],
) -> None:
    registry = ToolRegistry()
    adapter = ToolSchemaAdapter()

    provider = ToolProvider(
        registry=registry,
        adapter=adapter,
    )

    groq_client = create_groq_client(
        tool_provider=provider,
    )

    successful_response = MagicMock()
    successful_response.choices[0].message.content = "好的"
    successful_response.choices[0].finish_reason = "stop"

    mock_create = MagicMock(
        return_value=successful_response,
    )

    groq_client.client.chat.completions.create = mock_create

    result = groq_client.chat(messages)

    kwargs = mock_create.call_args.kwargs

    assert result.content == "好的"
    assert result.tool_calls == ()
    assert "tools" not in kwargs
