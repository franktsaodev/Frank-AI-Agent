from collections.abc import Callable, Mapping, Sequence
from typing import ClassVar

from app.tools.plugins.core_tool_plugin import (
    CoreToolPlugin,
)
from app.tools.plugins.tool_plugin_name import (
    ToolPluginName,
)
from app.tools.plugins.tool_plugin_protocol import (
    ToolPluginProtocol,
)


class ToolPluginFactory:
    _PLUGIN_TYPES: ClassVar[
        Mapping[
            ToolPluginName,
            Callable[[], ToolPluginProtocol],
        ]
    ] = {
        ToolPluginName.CORE: CoreToolPlugin,
    }

    def create(
        self,
        plugin_name: ToolPluginName,
    ) -> ToolPluginProtocol:
        try:
            plugin_type = self._PLUGIN_TYPES[plugin_name]
        except KeyError as error:
            raise ValueError(f"Unsupported tool plugin: {plugin_name}") from error

        return plugin_type()

    def create_all(
        self,
        plugin_names: Sequence[ToolPluginName],
    ) -> tuple[ToolPluginProtocol, ...]:
        return tuple(self.create(plugin_name) for plugin_name in plugin_names)
