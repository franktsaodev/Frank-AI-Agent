import pytest

from app.tools.calculator_tool import CalculatorTool
from app.tools.tool_execution_context import (
    ToolExecutionContext,
)
from app.tracing.trace_context import TraceContext
from tests.fakes.fake_clock import FakeClock


@pytest.fixture
def tool_execution_context() -> ToolExecutionContext:
    return ToolExecutionContext(
        trace_context=TraceContext(
            trace_id="test-trace-id",
            span_id="tool-span-id",
            parent_span_id="agent-span-id",
        ),
        tool_name="calculator",
        tool_call_id="call-calculator-123",
        clock=FakeClock.for_duration(
            1.0,
        ),
    )


def test_name_returns_calculator() -> None:
    tool = CalculatorTool()

    assert tool.name == "calculator"


def test_description_is_not_empty() -> None:
    tool = CalculatorTool()

    assert tool.description


def test_execute_adds_two_numbers(
    tool_execution_context: ToolExecutionContext,
) -> None:
    tool = CalculatorTool()

    result = tool.execute(
        context=tool_execution_context,
        operation="add",
        a=10,
        b=20,
    )

    assert result == 30


def test_execute_subtracts_two_numbers(
    tool_execution_context: ToolExecutionContext,
) -> None:
    tool = CalculatorTool()

    result = tool.execute(
        context=tool_execution_context,
        operation="subtract",
        a=20,
        b=5,
    )

    assert result == 15


def test_execute_multiplies_two_numbers(
    tool_execution_context: ToolExecutionContext,
) -> None:
    tool = CalculatorTool()

    result = tool.execute(
        context=tool_execution_context,
        operation="multiply",
        a=6,
        b=7,
    )

    assert result == 42


def test_execute_divides_two_numbers(
    tool_execution_context: ToolExecutionContext,
) -> None:
    tool = CalculatorTool()

    result = tool.execute(
        context=tool_execution_context,
        operation="divide",
        a=20,
        b=4,
    )

    assert result == 5


def test_execute_raises_error_for_unsupported_operation(
    tool_execution_context: ToolExecutionContext,
) -> None:
    tool = CalculatorTool()

    with pytest.raises(ValueError):
        tool.execute(
            context=tool_execution_context,
            operation="power",
            a=2,
            b=3,
        )


def test_execute_raises_error_when_dividing_by_zero(
    tool_execution_context: ToolExecutionContext,
) -> None:
    tool = CalculatorTool()

    with pytest.raises(
        ZeroDivisionError,
        match="Division by zero is not allowed",
    ):
        tool.execute(
            context=tool_execution_context,
            operation="divide",
            a=10,
            b=0,
        )


def test_execute_raises_error_when_operation_is_missing(
    tool_execution_context: ToolExecutionContext,
) -> None:
    tool = CalculatorTool()

    with pytest.raises(
        ValueError,
        match="Missing required argument: operation",
    ):
        tool.execute(
            context=tool_execution_context,
            a=10,
            b=20,
        )


def test_input_schema_describes_calculator_arguments() -> None:
    tool = CalculatorTool()

    schema = tool.input_schema

    assert schema["type"] == "object"
    assert schema["required"] == [
        "operation",
        "a",
        "b",
    ]
    assert schema["additionalProperties"] is False

    properties = schema["properties"]

    assert isinstance(properties, dict)

    assert set(properties) == {
        "operation",
        "a",
        "b",
    }

    operation_schema = properties["operation"]

    assert isinstance(operation_schema, dict)
    assert operation_schema["type"] == "string"
    assert operation_schema["enum"] == [
        "add",
        "subtract",
        "multiply",
        "divide",
    ]


def test_input_schema_returns_independent_dictionary() -> None:
    tool = CalculatorTool()

    first_schema = tool.input_schema
    second_schema = tool.input_schema

    first_properties = first_schema["properties"]

    assert isinstance(first_properties, dict)

    first_properties.clear()

    second_properties = second_schema["properties"]

    assert isinstance(second_properties, dict)

    assert list(second_properties) == [
        "operation",
        "a",
        "b",
    ]


def test_description_should_limit_tool_to_numeric_calculations() -> None:
    tool = CalculatorTool()

    description = tool.description.lower()

    assert "numerical calculation" in description
    assert "general conversation" in description
    assert "memory retrieval" in description


def test_input_schema_should_reject_additional_properties() -> None:
    tool = CalculatorTool()

    schema = tool.input_schema

    assert schema["additionalProperties"] is False


def test_input_schema_should_describe_calculator_operands() -> None:
    tool = CalculatorTool()

    properties = tool.input_schema["properties"]

    assert isinstance(properties, dict)

    operation_schema = properties["operation"]
    first_operand_schema = properties["a"]
    second_operand_schema = properties["b"]

    assert isinstance(operation_schema, dict)
    assert isinstance(first_operand_schema, dict)
    assert isinstance(second_operand_schema, dict)

    operation_description = operation_schema["description"]
    first_operand_description = first_operand_schema["description"]
    second_operand_description = second_operand_schema["description"]

    assert isinstance(operation_description, str)
    assert isinstance(first_operand_description, str)
    assert isinstance(second_operand_description, str)

    assert "arithmetic operation" in operation_description.lower()
    assert "first numeric operand" in first_operand_description.lower()
    assert "second numeric operand" in second_operand_description.lower()


def test_input_schema_should_define_supported_operations() -> None:
    tool = CalculatorTool()

    properties = tool.input_schema["properties"]

    assert isinstance(properties, dict)

    operation_schema = properties["operation"]

    assert isinstance(operation_schema, dict)

    assert operation_schema["enum"] == [
        "add",
        "subtract",
        "multiply",
        "divide",
    ]
