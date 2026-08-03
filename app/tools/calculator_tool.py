from typing import Any

from app.tools.base_tool import BaseTool
from app.types.json_types import JsonObject


class CalculatorTool(BaseTool):
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

    def execute(self, **kwargs: Any) -> float:
        operation = kwargs.get("operation")
        a = kwargs.get("a")
        b = kwargs.get("b")

        if operation is None:
            raise ValueError("Missing required argument: operation")

        if a is None:
            raise ValueError("Missing required argument: a")

        if b is None:
            raise ValueError("Missing required argument: b")

        match operation:
            case "add":
                return a + b
            case "subtract":
                return a - b
            case "multiply":
                return a * b
            case "divide":
                return a / b
            case _:
                raise ValueError(f"Unsupported operation: {operation}")
