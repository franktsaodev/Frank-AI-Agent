from typing import Any

from app.tools.base_tool import BaseTool
from app.tools.tool_execution_context import ToolExecutionContext
from app.types.json_types import JsonObject


class CalculatorTool(BaseTool):
    def execute(
        self,
        *,
        context: ToolExecutionContext,
        **kwargs: Any,
    ) -> int | float:
        del context

        operation = self._get_required_argument(
            kwargs,
            "operation",
        )
        a = self._get_required_argument(
            kwargs,
            "a",
        )
        b = self._get_required_argument(
            kwargs,
            "b",
        )

        if not isinstance(operation, str):
            raise TypeError("Argument 'operation' must be a string.")

        if not self._is_number(a):
            raise TypeError("Argument 'a' must be a number.")

        if not self._is_number(b):
            raise TypeError("Argument 'b' must be a number.")

        return self._calculate(
            operation=operation,
            a=a,
            b=b,
        )

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "Evaluate an explicit arithmetic expression containing numbers "
            "and supported mathematical operators. Use this tool only when "
            "the user asks for a numerical calculation. Do not use it for "
            "general conversation, personal information, memory retrieval, "
            "or non-mathematical questions."
        )

    @property
    def input_schema(self) -> JsonObject:
        return {
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
                    "description": "The first numeric operand in the calculation.",
                },
                "b": {
                    "type": "number",
                    "description": "The second numeric operand in the calculation.",
                },
            },
            "required": [
                "operation",
                "a",
                "b",
            ],
            "additionalProperties": False,
        }

    def _get_required_argument(
        self,
        arguments: dict[str, Any],
        name: str,
    ) -> Any:
        if name not in arguments:
            raise ValueError(f"Missing required argument: {name}")

        return arguments[name]

    def _is_number(
        self,
        value: object,
    ) -> bool:
        return isinstance(
            value,
            (int, float),
        ) and not isinstance(value, bool)

    def _calculate(
        self,
        *,
        operation: str,
        a: float,
        b: float,
    ) -> int | float:
        match operation:
            case "add":
                return a + b
            case "subtract":
                return a - b
            case "multiply":
                return a * b
            case "divide":
                if b == 0:
                    raise ZeroDivisionError("Division by zero is not allowed.")

                return a / b
            case _:
                raise ValueError(f"Unsupported operation: {operation}")
