from app.tools.calculator_tool import CalculatorTool
from app.tools.tool_provider import ToolProvider
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_schema_adapter import ToolSchemaAdapter


def test_get_tool_schemas_returns_all_registered_tools() -> None:
    registry = ToolRegistry()
    adapter = ToolSchemaAdapter()
    provider = ToolProvider(registry, adapter)

    registry.register(CalculatorTool())

    schemas = provider.get_tool_schemas()

    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "calculator"

    assert schemas == adapter.adapt_all(registry.get_all())


def test_get_tool_schemas_returns_empty_list_when_no_tools_registered() -> None:
    registry = ToolRegistry()
    adapter = ToolSchemaAdapter()
    provider = ToolProvider(registry, adapter)

    schemas = provider.get_tool_schemas()

    assert schemas == []
