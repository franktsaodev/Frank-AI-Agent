from typing import Any

from app.tools.base_tool import BaseTool
from app.tools.tool_execution_context import (
    ToolExecutionContext,
)
from app.tools.tool_schema_adapter import ToolSchemaAdapter
from app.types.json_types import JsonObject
from tests.fakes.fake_tool import FakeTool


class ToolWithSharedSchema(BaseTool):
    def __init__(self) -> None:
        self.schema: JsonObject = {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                },
            },
        }

    @property
    def name(self) -> str:
        return "shared"

    @property
    def description(self) -> str:
        return "A tool with a shared schema."

    @property
    def input_schema(self) -> JsonObject:
        return self.schema

    def execute(
        self,
        *,
        context: ToolExecutionContext,
        **kwargs: Any,
    ) -> None:
        del context
        del kwargs


class SecondFakeTool(BaseTool):
    @property
    def name(self) -> str:
        return "second"

    @property
    def description(self) -> str:
        return "A second fake tool."

    @property
    def input_schema(self) -> JsonObject:
        return {
            "type": "object",
            "properties": {},
        }

    def execute(
        self,
        *,
        context: ToolExecutionContext,
        **kwargs: Any,
    ) -> str:
        del context
        del kwargs

        return "second fake result"


def test_adapt_returns_function_tool_schema() -> None:
    adapter = ToolSchemaAdapter()
    tool = FakeTool()

    result = adapter.adapt(tool)

    assert result == {
        "type": "function",
        "function": {
            "name": "fake",
            "description": "A fake tool for testing.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": True,
            },
        },
    }


def test_adapt_copies_input_schema() -> None:
    adapter = ToolSchemaAdapter()
    tool = ToolWithSharedSchema()

    result = adapter.adapt(tool)

    parameters = result["function"]["parameters"]

    properties = parameters["properties"]

    assert isinstance(
        properties,
        dict,
    )

    properties.clear()

    assert tool.schema["properties"] == {
        "message": {
            "type": "string",
        },
    }


def test_adapt_all_returns_all_tool_schemas() -> None:
    adapter = ToolSchemaAdapter()

    result = adapter.adapt_all(
        [
            FakeTool(),
            SecondFakeTool(),
        ]
    )

    assert len(result) == 2
    assert result[0]["function"]["name"] == "fake"
    assert result[1]["function"]["name"] == "second"


def test_adapt_all_returns_empty_list_for_no_tools() -> None:
    adapter = ToolSchemaAdapter()

    result = adapter.adapt_all([])

    assert result == []
