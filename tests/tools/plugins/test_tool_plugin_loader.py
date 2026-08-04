from collections.abc import Sequence
from typing import Any

import pytest

from app.tools.base_tool import BaseTool
from app.tools.plugins.tool_plugin_loader import (
    ToolPluginLoader,
)
from app.tools.tool_execution_context import ToolExecutionContext
from app.tools.tool_registry import ToolRegistry
from app.types.json_types import JsonObject
from tests.fakes.fake_tool import FakeTool


class FakeToolPlugin:
    def __init__(
        self,
        tools: Sequence[BaseTool],
    ) -> None:
        self._tools = tuple(tools)

    def get_tools(
        self,
    ) -> Sequence[BaseTool]:
        return self._tools


def test_load_should_register_plugin_tools() -> None:
    registry = ToolRegistry()

    plugin = FakeToolPlugin(
        tools=(FakeTool(),),
    )

    loader = ToolPluginLoader(
        registry=registry,
    )

    loader.load(
        plugins=(plugin,),
    )

    assert registry.get("fake").name == "fake"


class SecondFakeTool(BaseTool):
    @property
    def name(self) -> str:
        return "second_fake"

    @property
    def description(self) -> str:
        return "Second fake tool"

    @property
    def input_schema(self) -> JsonObject:
        return {
            "type": "object",
            "properties": {},
        }

    def execute(
        self,
        *,
        context: ToolExecutionContext,
        **kwargs: Any,
    ) -> str:
        del context
        del kwargs

        return "second fake result"


def test_load_should_register_tools_from_all_plugins() -> None:
    registry = ToolRegistry()

    first_plugin = FakeToolPlugin(
        tools=(FakeTool(),),
    )

    second_plugin = FakeToolPlugin(
        tools=(SecondFakeTool(),),
    )

    loader = ToolPluginLoader(
        registry=registry,
    )

    loader.load(
        plugins=(
            first_plugin,
            second_plugin,
        ),
    )

    assert registry.get("fake").name == "fake"
    assert registry.get("second_fake").name == "second_fake"


def test_load_should_reject_duplicate_tools_across_plugins() -> None:
    registry = ToolRegistry()

    first_plugin = FakeToolPlugin(
        tools=(FakeTool(),),
    )

    second_plugin = FakeToolPlugin(
        tools=(FakeTool(),),
    )

    loader = ToolPluginLoader(
        registry=registry,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate tool in plugins: fake",
    ):
        loader.load(
            plugins=(
                first_plugin,
                second_plugin,
            ),
        )

    assert registry.contains("fake") is False


def test_load_should_not_register_any_tools_when_plugin_contains_duplicates() -> None:
    registry = ToolRegistry()

    plugin = FakeToolPlugin(
        tools=(
            FakeTool(),
            FakeTool(),
        ),
    )

    loader = ToolPluginLoader(
        registry=registry,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate tool in plugins: fake",
    ):
        loader.load(
            plugins=(plugin,),
        )

    assert not registry.contains("fake")


def test_load_should_not_register_any_tools_when_plugins_conflict() -> None:
    registry = ToolRegistry()

    first_plugin = FakeToolPlugin(
        tools=(
            SecondFakeTool(),
            FakeTool(),
        ),
    )

    second_plugin = FakeToolPlugin(
        tools=(FakeTool(),),
    )

    loader = ToolPluginLoader(
        registry=registry,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate tool in plugins: fake",
    ):
        loader.load(
            plugins=(
                first_plugin,
                second_plugin,
            ),
        )

    assert not registry.contains("second_fake")
    assert not registry.contains("fake")


def test_load_should_not_register_tools_when_name_already_exists() -> None:
    registry = ToolRegistry()
    registry.register(FakeTool())

    plugin = FakeToolPlugin(
        tools=(
            SecondFakeTool(),
            FakeTool(),
        ),
    )

    loader = ToolPluginLoader(
        registry=registry,
    )

    with pytest.raises(
        ValueError,
        match="Tool already registered: fake",
    ):
        loader.load(
            plugins=(plugin,),
        )

    assert registry.contains("fake")
    assert not registry.contains("second_fake")


def test_load_should_return_loaded_plugin_summary() -> None:
    registry = ToolRegistry()

    first_plugin = FakeToolPlugin(
        tools=(FakeTool(),),
    )

    second_plugin = FakeToolPlugin(
        tools=(SecondFakeTool(),),
    )

    loader = ToolPluginLoader(
        registry=registry,
    )

    result = loader.load(
        plugins=(
            first_plugin,
            second_plugin,
        ),
    )

    assert result.plugin_count == 2
    assert result.tool_count == 2
    assert result.tool_names == (
        "fake",
        "second_fake",
    )
