from unittest.mock import MagicMock

from app.clients.groq_tool_call_parser import GroqToolCallParser


def test_parse_converts_groq_tool_call_to_domain_tool_call() -> None:
    raw_tool_call = MagicMock()
    raw_tool_call.id = "call-123"
    raw_tool_call.function.name = "calculator"
    raw_tool_call.function.arguments = '{"expression": "2 + 3 * 5"}'

    parser = GroqToolCallParser()

    result = parser.parse(raw_tool_call)

    assert result.call_id == "call-123"
    assert result.name == "calculator"
    assert result.arguments == {
        "expression": "2 + 3 * 5",
    }
