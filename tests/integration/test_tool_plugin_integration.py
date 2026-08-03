from app.tools.calculator_tool import CalculatorTool
from app.tools.plugins.core_tool_plugin import CoreToolPlugin
from app.tools.plugins.tool_plugin_loader import ToolPluginLoader
from app.tools.tool_registry import ToolRegistry


def test_core_plugin_should_register_calculator_tool() -> None:
    registry = ToolRegistry()

    loader = ToolPluginLoader(
        registry=registry,
    )

    result = loader.load(
        plugins=(CoreToolPlugin(),),
    )

    calculator = registry.get(
        "calculator",
    )

    assert isinstance(
        calculator,
        CalculatorTool,
    )

    assert result.plugin_count == 1
    assert result.tool_count == 1
    assert result.tool_names == ("calculator",)
