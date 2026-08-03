import pytest

from app.tools.calculator_tool import CalculatorTool


def test_name_returns_calculator() -> None:
    tool = CalculatorTool()

    assert tool.name == "calculator"


def test_description_is_not_empty() -> None:
    tool = CalculatorTool()

    assert tool.description


def test_execute_adds_two_numbers() -> None:
    tool = CalculatorTool()

    result = tool.execute(
        operation="add",
        a=10,
        b=20,
    )

    assert result == 30


def test_execute_subtracts_two_numbers() -> None:
    tool = CalculatorTool()

    result = tool.execute(
        operation="subtract",
        a=20,
        b=5,
    )

    assert result == 15


def test_execute_multiplies_two_numbers() -> None:
    tool = CalculatorTool()

    result = tool.execute(
        operation="multiply",
        a=6,
        b=7,
    )

    assert result == 42


def test_execute_divides_two_numbers() -> None:
    tool = CalculatorTool()

    result = tool.execute(
        operation="divide",
        a=20,
        b=4,
    )

    assert result == 5


def test_execute_raises_error_for_unsupported_operation() -> None:
    tool = CalculatorTool()

    with pytest.raises(ValueError):
        tool.execute(
            operation="power",
            a=2,
            b=3,
        )


def test_execute_raises_error_when_dividing_by_zero() -> None:
    tool = CalculatorTool()

    with pytest.raises(ZeroDivisionError):
        tool.execute(
            operation="divide",
            a=10,
            b=0,
        )


def test_execute_raises_error_when_operation_is_missing() -> None:
    tool = CalculatorTool()

    with pytest.raises(
        ValueError,
        match="Missing required argument: operation",
    ):
        tool.execute(
            a=10,
            b=20,
        )


def test_input_schema_describes_calculator_arguments() -> None:
    tool = CalculatorTool()

    assert tool.input_schema == {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "description": "The arithmetic operation to perform.",
                "enum": [
                    "add",
                    "subtract",
                    "multiply",
                    "divide",
                ],
            },
            "a": {
                "type": "number",
                "description": "The first number.",
            },
            "b": {
                "type": "number",
                "description": "The second number.",
            },
        },
        "required": [
            "operation",
            "a",
            "b",
        ],
        "additionalProperties": False,
    }


def test_input_schema_returns_independent_dictionary() -> None:
    tool = CalculatorTool()

    first_schema = tool.input_schema
    second_schema = tool.input_schema

    first_properties = first_schema["properties"]

    assert isinstance(
        first_properties,
        dict,
    )

    first_properties.clear()

    second_properties = second_schema["properties"]

    assert isinstance(
        second_properties,
        dict,
    )

    assert second_properties != {}

    assert second_schema["required"] == [
        "operation",
        "a",
        "b",
    ]
