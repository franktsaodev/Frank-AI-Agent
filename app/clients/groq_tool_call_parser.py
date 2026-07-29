import json
from typing import Any

from app.tools.tool_call import ToolCall


class GroqToolCallParser:
    def parse(
        self,
        raw_tool_call: Any,
    ) -> ToolCall:
        arguments = json.loads(raw_tool_call.function.arguments)

        return ToolCall(
            call_id=raw_tool_call.id,
            name=raw_tool_call.function.name,
            arguments=arguments,
        )
