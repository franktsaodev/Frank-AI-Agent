from dataclasses import dataclass


@dataclass(frozen=True)
class ToolPluginLoadResult:
    plugin_count: int
    tool_names: tuple[str, ...]

    @property
    def tool_count(self) -> int:
        return len(self.tool_names)
