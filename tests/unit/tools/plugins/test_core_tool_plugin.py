from app.tools.calculator_tool import CalculatorTool
from app.tools.plugins.core_tool_plugin import CoreToolPlugin


def test_get_tools_should_return_core_tools() -> None:
    plugin = CoreToolPlugin()

    tools = plugin.get_tools()

    assert len(tools) == 1
    assert isinstance(
        tools[0],
        CalculatorTool,
    )


def test_get_tools_should_include_calculator() -> None:
    plugin = CoreToolPlugin()

    tool_names = {tool.name for tool in plugin.get_tools()}

    assert tool_names == {
        "calculator",
    }
