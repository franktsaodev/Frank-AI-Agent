from app.tools.plugins.core_tool_plugin import (
    CoreToolPlugin,
)
from app.tools.plugins.tool_plugin_factory import (
    ToolPluginFactory,
)
from app.tools.plugins.tool_plugin_name import (
    ToolPluginName,
)


def test_create_should_return_core_plugin() -> None:
    factory = ToolPluginFactory()

    plugin = factory.create(
        ToolPluginName.CORE,
    )

    assert isinstance(
        plugin,
        CoreToolPlugin,
    )


def test_create_all_should_return_plugins() -> None:
    factory = ToolPluginFactory()

    plugins = factory.create_all((ToolPluginName.CORE,))

    assert len(plugins) == 1
    assert isinstance(
        plugins[0],
        CoreToolPlugin,
    )


def test_create_all_should_return_empty_tuple() -> None:
    factory = ToolPluginFactory()

    plugins = factory.create_all(())

    assert plugins == ()
