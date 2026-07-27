from dataclasses import FrozenInstanceError

import pytest

from app.tools.tool_call import ToolCall


def test_create_tool_call() -> None:
    tool_call = ToolCall(
        name="calculator",
        arguments={
            "operation": "add",
            "a": 10,
            "b": 20,
        },
    )

    assert tool_call.name == "calculator"
    assert tool_call.arguments == {
        "operation": "add",
        "a": 10,
        "b": 20,
    }


def test_tool_calls_with_same_values_are_equal() -> None:
    first = ToolCall(
        name="calculator",
        arguments={
            "operation": "add",
            "a": 10,
            "b": 20,
        },
    )
    second = ToolCall(
        name="calculator",
        arguments={
            "operation": "add",
            "a": 10,
            "b": 20,
        },
    )

    assert first == second


def test_tool_call_is_frozen() -> None:
    tool_call = ToolCall(
        name="calculator",
        arguments={},
    )

    with pytest.raises(FrozenInstanceError):
        tool_call.name = "weather"


def test_tool_call_copies_arguments() -> None:
    arguments = {
        "operation": "add",
        "a": 10,
        "b": 20,
    }

    tool_call = ToolCall(
        name="calculator",
        arguments=arguments,
    )

    arguments["a"] = 999

    assert tool_call.arguments["a"] == 10


def test_tool_call_rejects_empty_name() -> None:
    with pytest.raises(
        ValueError,
        match="Tool name cannot be empty",
    ):
        ToolCall(
            name="",
            arguments={},
        )


def test_tool_call_rejects_whitespace_name() -> None:
    with pytest.raises(
        ValueError,
        match="Tool name cannot be empty",
    ):
        ToolCall(
            name="   ",
            arguments={},
        )
