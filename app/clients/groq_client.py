import json
import logging
import time
from collections.abc import Iterable, Iterator, Sequence
from typing import Any, cast

from groq import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    Groq,
    RateLimitError,
)

from app.clients.base_client import BaseClient
from app.clock.base_clock import BaseClock
from app.config_models.groq_config import GroqConfig
from app.config_models.retry_config import RetryConfig
from app.exceptions.client_exceptions import (
    ClientAuthenticationError,
    ClientConnectionError,
    ClientInvalidResponseError,
    ClientRateLimitError,
    ClientTimeoutError,
)
from app.models.client_response import ClientResponse
from app.models.client_stream_event import (
    ClientContentDelta,
    ClientStreamCompleted,
    ClientStreamEvent,
)
from app.models.message import Message
from app.tools.tool_call import ToolCall
from app.tools.tool_provider import ToolProvider
from app.tracing.base_tracer import BaseTracer
from app.tracing.trace_context import TraceContext
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType

logger = logging.getLogger(__name__)


class GroqClient(BaseClient):
    def __init__(
        self,
        groq_config: GroqConfig,
        retry_config: RetryConfig,
        tool_provider: ToolProvider,
        tracer: BaseTracer,
        clock: BaseClock,
    ) -> None:
        self._client = Groq(
            api_key=groq_config.api_key,
            max_retries=0,
        )
        self._groq_config = groq_config
        self._retry_config = retry_config
        self._tool_provider = tool_provider
        self._tracer = tracer
        self._clock = clock

    def chat(
        self,
        messages: Sequence[Message],
        trace_context: TraceContext,
    ) -> ClientResponse:
        formatted_messages = self._format_messages(messages)

        llm_context = trace_context.create_child()

        start_time = self._clock.now()

        self._tracer.trace(
            TraceEvent(
                trace_id=llm_context.trace_id,
                span_id=llm_context.span_id,
                parent_span_id=llm_context.parent_span_id,
                event_type=TraceEventType.LLM_STARTED,
                metadata={
                    "model": self._groq_config.model,
                    "message_count": len(messages),
                },
            )
        )

        try:
            client_response, attempt = self._chat_with_retry(
                formatted_messages,
            )
        except Exception as error:
            duration_ms = (self._clock.now() - start_time) * 1000

            self._tracer.trace(
                TraceEvent(
                    trace_id=llm_context.trace_id,
                    span_id=llm_context.span_id,
                    parent_span_id=llm_context.parent_span_id,
                    event_type=TraceEventType.LLM_FAILED,
                    metadata={
                        "model": self._groq_config.model,
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                        "duration_ms": duration_ms,
                    },
                )
            )

            raise

        duration_ms = (self._clock.now() - start_time) * 1000
        self._tracer.trace(
            TraceEvent(
                trace_id=llm_context.trace_id,
                span_id=llm_context.span_id,
                parent_span_id=llm_context.parent_span_id,
                event_type=TraceEventType.LLM_FINISHED,
                metadata={
                    "model": self._groq_config.model,
                    "attempt": attempt,
                    "has_tool_calls": client_response.has_tool_calls,
                    "tool_call_count": len(client_response.tool_calls),
                    "duration_ms": duration_ms,
                },
            )
        )

        return client_response

    def stream_chat(
        self,
        messages: Sequence[Message],
        trace_context: TraceContext,
    ) -> Iterator[ClientStreamEvent]:
        formatted_messages = self._format_messages(messages)

        llm_context = trace_context.create_child()
        start_time = self._clock.now()

        self._tracer.trace(
            TraceEvent(
                trace_id=llm_context.trace_id,
                span_id=llm_context.span_id,
                parent_span_id=llm_context.parent_span_id,
                event_type=TraceEventType.LLM_STARTED,
                metadata={
                    "model": self._groq_config.model,
                    "message_count": len(messages),
                },
            )
        )

        try:
            stream, attempt = self._create_stream_with_retry(
                formatted_messages,
            )

            content_parts: list[str] = []
            tool_call_parts: dict[int, dict[str, str]] = {}

            for chunk in stream:
                if not chunk.choices:
                    continue

                choice = chunk.choices[0]

                self._accumulate_stream_tool_calls(
                    tool_call_parts,
                    choice.delta.tool_calls,
                )

                content_delta = choice.delta.content

                if content_delta is None or content_delta == "":
                    continue

                content_parts.append(content_delta)

                yield ClientContentDelta(
                    content=content_delta,
                )

            raw_content = "".join(content_parts)
            sanitized_content = self._sanitize_response(
                raw_content,
            )
            content = sanitized_content or None

            tool_calls = self._build_stream_tool_calls(
                tool_call_parts,
            )

            if not tool_calls and not self._is_valid_response(content):
                raise ClientInvalidResponseError(
                    "Groq returned invalid streamed content."
                )

            client_response = ClientResponse(
                content=content,
                tool_calls=tool_calls,
            )
        except Exception as error:
            mapped_error = self._map_stream_error(error)

            duration_ms = (self._clock.now() - start_time) * 1000

            self._tracer.trace(
                TraceEvent(
                    trace_id=llm_context.trace_id,
                    span_id=llm_context.span_id,
                    parent_span_id=llm_context.parent_span_id,
                    event_type=TraceEventType.LLM_FAILED,
                    metadata={
                        "model": self._groq_config.model,
                        "error_type": type(mapped_error).__name__,
                        "error_message": str(mapped_error),
                        "duration_ms": duration_ms,
                    },
                )
            )

            if mapped_error is error:
                raise

            raise mapped_error from error

        duration_ms = (self._clock.now() - start_time) * 1000

        self._tracer.trace(
            TraceEvent(
                trace_id=llm_context.trace_id,
                span_id=llm_context.span_id,
                parent_span_id=llm_context.parent_span_id,
                event_type=TraceEventType.LLM_FINISHED,
                metadata={
                    "model": self._groq_config.model,
                    "attempt": attempt,
                    "has_tool_calls": client_response.has_tool_calls,
                    "tool_call_count": len(
                        client_response.tool_calls,
                    ),
                    "duration_ms": duration_ms,
                },
            )
        )

        yield ClientStreamCompleted(
            response=client_response,
        )

    def _accumulate_stream_tool_calls(
        self,
        tool_call_parts: dict[int, dict[str, str]],
        raw_tool_calls: Any,
    ) -> None:
        if not raw_tool_calls:
            return

        for raw_tool_call in raw_tool_calls:
            parts = tool_call_parts.setdefault(
                raw_tool_call.index,
                {
                    "call_id": "",
                    "name": "",
                    "arguments": "",
                },
            )

            if raw_tool_call.id is not None:
                parts["call_id"] += raw_tool_call.id

            if raw_tool_call.function is None:
                continue

            if raw_tool_call.function.name is not None:
                parts["name"] += raw_tool_call.function.name

            if raw_tool_call.function.arguments is not None:
                parts["arguments"] += raw_tool_call.function.arguments

    def _build_stream_tool_calls(
        self,
        tool_call_parts: dict[int, dict[str, str]],
    ) -> tuple[ToolCall, ...]:
        return tuple(
            ToolCall(
                call_id=parts["call_id"],
                name=parts["name"],
                arguments=json.loads(
                    parts["arguments"] or "{}",
                ),
            )
            for _, parts in sorted(
                tool_call_parts.items(),
            )
        )

    def _map_stream_error(
        self,
        error: Exception,
    ) -> Exception:
        if isinstance(error, AuthenticationError):
            return ClientAuthenticationError("AI client authentication failed")

        if isinstance(error, RateLimitError):
            return ClientRateLimitError("AI service rate limit exceeded")

        if isinstance(error, APITimeoutError):
            return ClientTimeoutError("AI client request timed out")

        if isinstance(error, APIConnectionError):
            return ClientConnectionError("Failed to connect to AI service")

        return error

    def _create_stream_with_retry(
        self,
        formatted_messages: list[dict[str, object]],
    ) -> tuple[Iterable[Any], int]:
        max_attempts = self._retry_config.max_attempts

        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(
                    "Starting Groq stream attempt=%d/%d",
                    attempt,
                    max_attempts,
                )

                tool_schemas = self._tool_provider.get_tool_schemas()

                request_kwargs: dict[str, Any] = {
                    "messages": formatted_messages,
                    "model": self._groq_config.model,
                    "temperature": self._groq_config.temperature,
                    "max_completion_tokens": (self._groq_config.max_completion_tokens),
                    "stream": True,
                }

                if tool_schemas:
                    request_kwargs["tools"] = tool_schemas

                stream = cast(
                    Iterable[Any],
                    self._client.chat.completions.create(
                        **request_kwargs,
                    ),
                )

                logger.info(
                    "Groq stream started on attempt %d/%d",
                    attempt,
                    max_attempts,
                )

                return stream, attempt

            except AuthenticationError as error:
                logger.exception("Groq authentication failed")

                raise ClientAuthenticationError(
                    "AI client authentication failed"
                ) from error

            except RateLimitError as error:
                self._handle_retryable_error(
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=error,
                    error_name="rate limit",
                    final_exception=ClientRateLimitError(
                        "AI service rate limit exceeded"
                    ),
                )

            except APITimeoutError as error:
                self._handle_retryable_error(
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=error,
                    error_name="request timeout",
                    final_exception=ClientTimeoutError("AI client request timed out"),
                )

            except APIConnectionError as error:
                self._handle_retryable_error(
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=error,
                    error_name="connection",
                    final_exception=ClientConnectionError(
                        "Failed to connect to AI service"
                    ),
                )

        raise RuntimeError("Groq stream retry loop ended unexpectedly.")

    def _chat_with_retry(
        self,
        formatted_messages: list[dict[str, object]],
    ) -> tuple[ClientResponse, int]:
        max_attempts = self._retry_config.max_attempts

        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(
                    "Sending Groq request attempt=%d/%d",
                    attempt,
                    max_attempts,
                )

                tool_schemas = self._tool_provider.get_tool_schemas()

                request_kwargs = {
                    "messages": formatted_messages,
                    "model": self._groq_config.model,
                    "temperature": self._groq_config.temperature,
                    "max_completion_tokens": (self._groq_config.max_completion_tokens),
                }

                if tool_schemas:
                    request_kwargs["tools"] = tool_schemas

                response = self._client.chat.completions.create(
                    **request_kwargs,
                )

                choice = response.choices[0]
                raw_content = choice.message.content

                tool_calls = self._parse_tool_calls(choice.message.tool_calls)

                logger.debug(
                    "Groq response finish_reason=%s raw_content=%r",
                    choice.finish_reason,
                    raw_content,
                )

                content = (
                    self._sanitize_response(raw_content)
                    if raw_content is not None
                    else None
                )

                if raw_content != content:
                    logger.debug(
                        "Groq response sanitized from %r to %r",
                        raw_content,
                        content,
                    )

                if not tool_calls and not self._is_valid_response(content):
                    self._handle_invalid_response(
                        content=content,
                        attempt=attempt,
                        max_attempts=max_attempts,
                    )
                    continue

                logger.info(
                    "Groq request succeeded on attempt %d/%d",
                    attempt,
                    max_attempts,
                )

                client_response = ClientResponse(
                    content=content,
                    tool_calls=tool_calls,
                )

                return client_response, attempt

            except AuthenticationError as error:
                logger.exception("Groq authentication failed")

                raise ClientAuthenticationError(
                    "AI client authentication failed"
                ) from error

            except RateLimitError as error:
                self._handle_retryable_error(
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=error,
                    error_name="rate limit",
                    final_exception=ClientRateLimitError(
                        "AI service rate limit exceeded"
                    ),
                )

            except APITimeoutError as error:
                self._handle_retryable_error(
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=error,
                    error_name="request timeout",
                    final_exception=ClientTimeoutError("AI client request timed out"),
                )

            except APIConnectionError as error:
                self._handle_retryable_error(
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=error,
                    error_name="connection",
                    final_exception=ClientConnectionError(
                        "Failed to connect to AI service"
                    ),
                )

        raise RuntimeError("Groq retry loop ended unexpectedly.")

    def _format_messages(
        self,
        messages: Sequence[Message],
    ) -> list[dict[str, object]]:
        self._validate_messages(messages)

        formatted_messages: list[dict[str, object]] = []

        for message in messages:
            formatted_message: dict[str, object] = {
                "role": message.role.value,
                "content": message.content,
            }

            if message.tool_calls:
                formatted_message["tool_calls"] = [
                    {
                        "id": tool_call.call_id,
                        "type": "function",
                        "function": {
                            "name": tool_call.name,
                            "arguments": json.dumps(tool_call.arguments),
                        },
                    }
                    for tool_call in message.tool_calls
                ]

            if message.tool_call_id is not None:
                formatted_message["tool_call_id"] = message.tool_call_id

            formatted_messages.append(formatted_message)

        return formatted_messages

    def _parse_tool_calls(
        self,
        raw_tool_calls: Any,
    ) -> tuple[ToolCall, ...]:
        if not raw_tool_calls:
            return ()

        return tuple(
            ToolCall(
                call_id=raw_tool_call.id,
                name=raw_tool_call.function.name,
                arguments=json.loads(raw_tool_call.function.arguments),
            )
            for raw_tool_call in raw_tool_calls
        )

    def _validate_messages(
        self,
        messages: Sequence[Message],
    ) -> None:
        for message in messages:
            if not isinstance(message, Message):
                raise TypeError(
                    "All messages must be Message instances, "
                    f"but received {type(message).__name__}."
                )

    def _handle_retryable_error(
        self,
        *,
        attempt: int,
        max_attempts: int,
        error: Exception,
        error_name: str,
        final_exception: Exception,
    ) -> None:
        if attempt == max_attempts:
            logger.exception(
                "Groq %s failed after %d attempts",
                error_name,
                max_attempts,
            )

            raise final_exception from error

        delay_seconds = self._calculate_delay(attempt)

        logger.warning(
            "Groq %s failed on attempt %d/%d. Retrying in %.1f seconds. Reason: %s",
            error_name,
            attempt,
            max_attempts,
            delay_seconds,
            error,
        )

        time.sleep(delay_seconds)

    def _handle_invalid_response(
        self,
        *,
        content: str | None,
        attempt: int,
        max_attempts: int,
    ) -> None:
        logger.warning(
            "Groq returned invalid content on attempt %d/%d: %r",
            attempt,
            max_attempts,
            content,
        )

        if attempt == max_attempts:
            raise ClientInvalidResponseError(
                f"Groq returned invalid content after {max_attempts} attempts."
            )

        delay_seconds = self._calculate_delay(attempt)

        logger.debug(
            "Retrying invalid response in %.1f seconds",
            delay_seconds,
        )

        time.sleep(delay_seconds)

    def _is_valid_response(
        self,
        content: str | None,
    ) -> bool:
        if content is None:
            return False

        cleaned_content = content.strip()

        if not cleaned_content:
            return False

        if not any(character.isalnum() for character in cleaned_content):
            return False

        return self._contains_chinese(cleaned_content)

    def _calculate_delay(self, attempt: int) -> float:
        return (
            self._retry_config.initial_delay_seconds
            * self._retry_config.backoff_multiplier ** (attempt - 1)
        )

    def _sanitize_response(self, content: str) -> str:
        cleaned_content = content.strip()

        invalid_prefixes = (
            ", !",
            ",!",
            ", 。",
            ",。",
        )

        for prefix in invalid_prefixes:
            if cleaned_content.startswith(prefix):
                cleaned_content = cleaned_content[len(prefix) :].lstrip()
                break

        return cleaned_content

    def _contains_chinese(self, content: str) -> bool:
        """Check whether the response contains Chinese characters."""
        return any("\u4e00" <= character <= "\u9fff" for character in content)
