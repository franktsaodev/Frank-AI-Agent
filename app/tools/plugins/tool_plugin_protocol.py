from collections.abc import Sequence
from typing import Protocol

from app.tools.base_tool import BaseTool


class ToolPluginProtocol(Protocol):
    def get_tools(
        self,
    ) -> Sequence[BaseTool]: ...
