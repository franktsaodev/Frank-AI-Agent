from typing import Any

from app.tools.base_tool import BaseTool
from app.tools.tool_schema_adapter import ToolSchemaAdapter
from tests.fakes.fake_tool import FakeTool


class ToolWithSharedSchema(BaseTool):
    def __init__(self) -> None:
        self.schema = {
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
    def input_schema(self) -> dict[str, Any]:
        return self.schema

    def execute(self, **kwargs: Any) -> Any:
        return None


class SecondFakeTool(BaseTool):
    @property
    def name(self) -> str:
        return "second"

    @property
    def description(self) -> str:
        return "A second fake tool."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
        }

    def execute(self, **kwargs: Any) -> str:
        return "second result"


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

    result["function"]["parameters"]["properties"].clear()

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
