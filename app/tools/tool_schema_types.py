from typing import TypedDict

from app.types.json_types import JsonObject


class ToolFunctionSchema(TypedDict):
    name: str
    description: str
    parameters: JsonObject


class ToolSchema(TypedDict):
    type: str
    function: ToolFunctionSchema
