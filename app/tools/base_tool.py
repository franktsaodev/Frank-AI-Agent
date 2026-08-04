from abc import ABC, abstractmethod
from typing import Any

from app.tools.tool_execution_context import (
    ToolExecutionContext,
)
from app.types.json_types import JsonObject


class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def input_schema(self) -> JsonObject:
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        *,
        context: ToolExecutionContext,
        **kwargs: Any,
    ) -> Any:
        raise NotImplementedError
