from app.tools.plugins.tool_plugin_load_result import (
    ToolPluginLoadResult,
)


def test_tool_count_should_return_number_of_loaded_tools() -> None:
    result = ToolPluginLoadResult(
        plugin_count=2,
        tool_names=(
            "calculator",
            "weather",
        ),
    )

    assert result.tool_count == 2
