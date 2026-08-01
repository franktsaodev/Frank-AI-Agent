import uuid

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
from app.tracing.trace_context import TraceContext
from app.tracing.trace_event import TraceEvent
from app.tracing.trace_event_type import TraceEventType


class AgentRunner:
    def __init__(
        self,
        client: BaseClient,
        tool_executor: ToolExecutor,
        tracer: BaseTracer,
        max_iterations: int = 10,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1.")

        self._client = client
        self._tool_executor = tool_executor
        self._tracer = tracer
        self._max_iterations = max_iterations

    def run(
        self,
        messages: list[Message],
    ) -> ClientResponse:
        agent_context = self._create_trace_context()

        current_messages = list(messages)

        self._tracer.trace(
            TraceEvent(
                trace_id=agent_context.trace_id,
                span_id=agent_context.span_id,
                parent_span_id=agent_context.parent_span_id,
                event_type=TraceEventType.AGENT_STARTED,
                metadata={
                    "message_count": len(current_messages),
                    "max_iterations": self._max_iterations,
                },
            )
        )

        try:
            for iteration in range(self._max_iterations):
                response = self._client.chat(
                    messages=current_messages,
                    trace_context=agent_context,
                )

                if not response.has_tool_calls:
                    self._tracer.trace(
                        TraceEvent(
                            trace_id=agent_context.trace_id,
                            span_id=agent_context.span_id,
                            parent_span_id=agent_context.parent_span_id,
                            event_type=TraceEventType.AGENT_FINISHED,
                            metadata={
                                "iterations": iteration + 1,
                                "final_message_count": len(current_messages),
                            },
                        )
                    )

                    return response

                is_last_iteration = iteration == self._max_iterations - 1

                if is_last_iteration:
                    raise MaxIterationsExceededError(
                        max_iterations=self._max_iterations,
                    )

                current_messages.append(
                    self._create_assistant_tool_call_message(response)
                )

                current_messages.extend(
                    self._execute_tool_calls(
                        tool_calls=response.tool_calls,
                        trace_context=agent_context,
                    )
                )

        except Exception as error:
            self._tracer.trace(
                TraceEvent(
                    trace_id=agent_context.trace_id,
                    span_id=agent_context.span_id,
                    parent_span_id=agent_context.parent_span_id,
                    event_type=TraceEventType.AGENT_FAILED,
                    metadata={
                        "error_type": type(error).__name__,
                        "error_message": str(error),
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
    ) -> list[Message]:
        tool_messages: list[Message] = []

        for tool_call in tool_calls:
            tool_result = self._tool_executor.execute(
                tool_call=tool_call,
                trace_context=trace_context,
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
