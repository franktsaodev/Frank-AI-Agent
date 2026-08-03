from collections.abc import Sequence

from app.tools.base_tool import BaseTool
from app.tools.calculator_tool import CalculatorTool


class CoreToolPlugin:
    def get_tools(
        self,
    ) -> Sequence[BaseTool]:
        return (CalculatorTool(),)
