import uuid
from collections.abc import Mapping, Sequence

from app.agent.agent_run_context import AgentRunContext
from app.clients.base_client import BaseClient
from app.clock.base_clock import BaseClock
from app.config_models.agent_config import AgentConfig
from app.exceptions.max_iterations_exceeded_error import (
    MaxIterationsExceededError,
)
from app.models.client_response import ClientResponse
from app.models.message import Message
from app.models.message_role import MessageRole
from app.tools.tool_call import ToolCall
from app.tools.tool_executor_protocol import (
    ToolExecutorProtocol,
)
from app.tracing.base_tracer import BaseTracer
from app.tracing.trace_context import TraceContext
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType
from app.types.json_types import JsonValue


class AgentRunner:
    def __init__(
        self,
        client: BaseClient,
        tool_executor: ToolExecutorProtocol,
        tracer: BaseTracer,
        clock: BaseClock,
        config: AgentConfig,
    ) -> None:
        self._client = client
        self._tool_executor = tool_executor
        self._tracer = tracer
        self._clock = clock
        self._config = config

    def run(
        self,
        messages: Sequence[Message],
        context: AgentRunContext | None = None,
    ) -> ClientResponse:
        actual_context = context if context is not None else AgentRunContext()

        agent_context = self._create_trace_context()

        start_time = self._clock.now()

        current_messages = list(messages)

        self._tracer.trace(
            TraceEvent(
                trace_id=agent_context.trace_id,
                span_id=agent_context.span_id,
                parent_span_id=agent_context.parent_span_id,
                event_type=TraceEventType.AGENT_STARTED,
                metadata={
                    "message_count": len(current_messages),
                    "max_iterations": self._config.max_iterations,
                },
            )
        )

        try:
            for iteration in range(self._config.max_iterations):
                response = self._client.chat(
                    messages=current_messages,
                    trace_context=agent_context,
                )
                if not response.has_tool_calls:
                    duration_ms = (self._clock.now() - start_time) * 1000
                    self._tracer.trace(
                        TraceEvent(
                            trace_id=agent_context.trace_id,
                            span_id=agent_context.span_id,
                            parent_span_id=agent_context.parent_span_id,
                            event_type=TraceEventType.AGENT_FINISHED,
                            metadata={
                                "iterations": iteration + 1,
                                "final_message_count": len(current_messages),
                                "duration_ms": duration_ms,
                            },
                        )
                    )

                    return response

                is_last_iteration = iteration == self._config.max_iterations - 1

                if is_last_iteration:
                    raise MaxIterationsExceededError(
                        max_iterations=self._config.max_iterations,
                    )

                current_messages.append(
                    self._create_assistant_tool_call_message(response)
                )

                current_messages.extend(
                    self._execute_tool_calls(
                        tool_calls=response.tool_calls,
                        trace_context=agent_context,
                        metadata=actual_context.metadata,
                    )
                )

        except Exception as error:
            duration_ms = (self._clock.now() - start_time) * 1000

            self._tracer.trace(
                TraceEvent(
                    trace_id=agent_context.trace_id,
                    span_id=agent_context.span_id,
                    parent_span_id=agent_context.parent_span_id,
                    event_type=TraceEventType.AGENT_FAILED,
                    metadata={
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                        "duration_ms": duration_ms,
                    },
                )
            )

            raise

        raise AssertionError("AgentRunner reached an unreachable state.")

    def _create_assistant_tool_call_message(
        self,
        response: ClientResponse,
    ) -> Message:
        return Message(
            role=MessageRole.ASSISTANT,
            content=response.content,
            tool_calls=response.tool_calls,
        )

    def _execute_tool_calls(
        self,
        tool_calls: tuple[ToolCall, ...],
        trace_context: TraceContext,
        metadata: Mapping[str, JsonValue],
    ) -> list[Message]:
        tool_messages: list[Message] = []

        for tool_call in tool_calls:
            tool_result = self._tool_executor.execute(
                tool_call=tool_call,
                trace_context=trace_context,
                metadata=metadata,
            )

            tool_messages.append(
                Message(
                    role=MessageRole.TOOL,
                    content=str(tool_result),
                    tool_call_id=tool_call.call_id,
                )
            )

        return tool_messages

    def _create_trace_context(self) -> TraceContext:
        return TraceContext(
            trace_id=uuid.uuid4().hex,
            span_id=uuid.uuid4().hex,
        )
