from app.clients.base_client import BaseClient
from app.exceptions.max_iterations_exceeded_error import (
    MaxIterationsExceededError,
)
from app.models.client_response import ClientResponse
from app.models.message import Message
from app.models.message_role import MessageRole
from app.tools.tool_call import ToolCall
from app.tools.tool_executor import ToolExecutor


class AgentRunner:
    def __init__(
        self,
        client: BaseClient,
        tool_executor: ToolExecutor,
        max_iterations: int = 10,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1.")

        self._client = client
        self._tool_executor = tool_executor
        self._max_iterations = max_iterations

    def run(
        self,
        messages: list[Message],
    ) -> ClientResponse:
        current_messages = list(messages)

        for iteration in range(self._max_iterations):
            response = self._client.chat(current_messages)

            if not response.has_tool_calls:
                return response

            is_last_iteration = iteration == self._max_iterations - 1

            if is_last_iteration:
                raise MaxIterationsExceededError(
                    max_iterations=self._max_iterations,
                )

            current_messages.append(self._create_assistant_tool_call_message(response))

            current_messages.extend(self._execute_tool_calls(response.tool_calls))

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
    ) -> list[Message]:
        tool_messages: list[Message] = []

        for tool_call in tool_calls:
            tool_result = self._tool_executor.execute(tool_call)

            tool_messages.append(
                Message(
                    role=MessageRole.TOOL,
                    content=str(tool_result),
                    tool_call_id=tool_call.call_id,
                )
            )

        return tool_messages
