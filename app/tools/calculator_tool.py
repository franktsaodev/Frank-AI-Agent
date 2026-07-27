from typing import Any

from app.tools.base_tool import BaseTool


class CalculatorTool(BaseTool):
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Perform basic arithmetic calculations."

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
