from app.config_models.tool_plugin_config import ToolPluginConfig
from app.tools.plugins.tool_plugin_factory import ToolPluginFactory
from app.tools.plugins.tool_plugin_loader import ToolPluginLoader
from app.tools.plugins.tool_plugin_name import ToolPluginName
from app.tools.tool_registry import ToolRegistry


def test_configured_plugins_should_be_created_and_loaded() -> None:
    config = ToolPluginConfig(
        enabled_plugins=(ToolPluginName.CORE,),
    )

    plugins = ToolPluginFactory().create_all(
        config.enabled_plugins,
    )

    registry = ToolRegistry()

    result = ToolPluginLoader(
        registry=registry,
    ).load(
        plugins=plugins,
    )

    assert registry.contains("calculator") is True
    assert result.plugin_count == 1
    assert result.tool_names == ("calculator",)


def test_empty_plugin_config_should_load_no_tools() -> None:
    config = ToolPluginConfig(
        enabled_plugins=(),
    )

    plugins = ToolPluginFactory().create_all(
        config.enabled_plugins,
    )

    registry = ToolRegistry()

    result = ToolPluginLoader(
        registry=registry,
    ).load(
        plugins=plugins,
    )

    assert registry.get_all() == []
    assert result.plugin_count == 0
    assert result.tool_count == 0
    assert result.tool_names == ()
