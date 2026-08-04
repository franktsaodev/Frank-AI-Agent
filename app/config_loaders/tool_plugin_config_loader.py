import os

from app.config_models.tool_plugin_config import (
    ToolPluginConfig,
)
from app.tools.plugins.tool_plugin_name import (
    ToolPluginName,
)


class ToolPluginConfigLoader:
    def load(
        self,
    ) -> ToolPluginConfig:
        raw_value = os.getenv(
            "ENABLED_TOOL_PLUGINS",
            ToolPluginName.CORE.value,
        )

        plugin_names = tuple(
            item.strip() for item in raw_value.split(",") if item.strip()
        )

        enabled_plugins = tuple(
            self._parse_plugin_name(plugin_name) for plugin_name in plugin_names
        )

        return ToolPluginConfig(
            enabled_plugins=enabled_plugins,
        )

    def _parse_plugin_name(
        self,
        plugin_name: str,
    ) -> ToolPluginName:
        try:
            return ToolPluginName(plugin_name)
        except ValueError as error:
            raise RuntimeError(
                f"Unsupported tool plugin configured: {plugin_name}"
            ) from error
