import pytest

from app.tools.calculator_tool import CalculatorTool
from app.tools.tool_registry import ToolRegistry


def test_register_and_get_tool() -> None:
    registry = ToolRegistry()
    calculator = CalculatorTool()

    registry.register(calculator)

    result = registry.get("calculator")

    assert result is calculator


def test_register_raises_error_for_duplicate_tool_name() -> None:
    registry = ToolRegistry()
    first_tool = CalculatorTool()
    second_tool = CalculatorTool()

    registry.register(first_tool)

    with pytest.raises(
        ValueError,
        match="Tool already registered: calculator",
    ):
        registry.register(second_tool)


def test_get_raises_error_when_tool_does_not_exist() -> None:
    registry = ToolRegistry()

    with pytest.raises(
        KeyError,
        match="Tool not found: weather",
    ):
        registry.get("weather")


def test_contains_returns_true_for_registered_tool() -> None:
    registry = ToolRegistry()
    registry.register(CalculatorTool())

    assert registry.contains("calculator") is True


def test_contains_returns_false_for_unknown_tool() -> None:
    registry = ToolRegistry()

    assert registry.contains("weather") is False


def test_get_all_returns_registered_tools() -> None:
    registry = ToolRegistry()
    calculator = CalculatorTool()

    registry.register(calculator)

    result = registry.get_all()

    assert result == [calculator]
