from dataclasses import dataclass

from app.tools.plugins.tool_plugin_name import (
    ToolPluginName,
)


@dataclass(frozen=True)
class ToolPluginConfig:
    enabled_plugins: tuple[ToolPluginName, ...] = (ToolPluginName.CORE,)

    def __post_init__(self) -> None:
        if len(self.enabled_plugins) != len(set(self.enabled_plugins)):
            raise ValueError("enabled_plugins cannot contain duplicates.")
