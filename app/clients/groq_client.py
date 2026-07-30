import json
import logging
import time
from typing import Any

from groq import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    Groq,
    RateLimitError,
)

from app.clients.base_client import BaseClient
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
from app.models.message import Message
from app.tools.tool_call import ToolCall
from app.tools.tool_provider import ToolProvider

logger = logging.getLogger(__name__)


class GroqClient(BaseClient):
    def __init__(
        self,
        groq_config: GroqConfig,
        retry_config: RetryConfig,
        tool_provider: ToolProvider,
    ) -> None:
        self.client = Groq(
            api_key=groq_config.api_key,
            max_retries=0,
        )
        self.groq_config = groq_config
        self.retry_config = retry_config
        self.tool_provider = tool_provider

    def chat(self, messages: list[Message]) -> ClientResponse:
        formatted_messages = self._format_messages(messages)

        max_attempts = self.retry_config.max_attempts

        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(
                    "Sending Groq request attempt=%d/%d",
                    attempt,
                    max_attempts,
                )

                tool_schemas = self.tool_provider.get_tool_schemas()

                request_kwargs = {
                    "messages": formatted_messages,
                    "model": self.groq_config.model,
                    "temperature": self.groq_config.temperature,
                    "max_completion_tokens": self.groq_config.max_completion_tokens,
                }

                if tool_schemas:
                    request_kwargs["tools"] = tool_schemas

                response = self.client.chat.completions.create(
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

                return ClientResponse(
                    content=content,
                    tool_calls=tool_calls,
                )
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
        messages: list[Message],
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
        messages: list[Message],
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
            self.retry_config.initial_delay_seconds
            * self.retry_config.backoff_multiplier ** (attempt - 1)
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
