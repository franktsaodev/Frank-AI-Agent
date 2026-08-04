import pytest

from app.config_loaders.tool_plugin_config_loader import (
    ToolPluginConfigLoader,
)
from app.tools.plugins.tool_plugin_name import (
    ToolPluginName,
)


def test_load_should_enable_core_plugin_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "ENABLED_TOOL_PLUGINS",
        raising=False,
    )

    config = ToolPluginConfigLoader().load()

    assert config.enabled_plugins == (ToolPluginName.CORE,)


def test_load_should_parse_enabled_plugins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ENABLED_TOOL_PLUGINS",
        "core",
    )

    config = ToolPluginConfigLoader().load()

    assert config.enabled_plugins == (ToolPluginName.CORE,)


def test_load_should_allow_no_plugins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ENABLED_TOOL_PLUGINS",
        "",
    )

    config = ToolPluginConfigLoader().load()

    assert config.enabled_plugins == ()


def test_load_should_ignore_surrounding_whitespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ENABLED_TOOL_PLUGINS",
        "  core  ",
    )

    config = ToolPluginConfigLoader().load()

    assert config.enabled_plugins == (ToolPluginName.CORE,)


def test_load_should_reject_unknown_plugin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ENABLED_TOOL_PLUGINS",
        "unknown",
    )

    with pytest.raises(
        RuntimeError,
        match="Unsupported tool plugin configured: unknown",
    ):
        ToolPluginConfigLoader().load()


def test_load_should_reject_duplicate_plugins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ENABLED_TOOL_PLUGINS",
        "core,core",
    )

    with pytest.raises(
        ValueError,
        match="enabled_plugins cannot contain duplicates",
    ):
        ToolPluginConfigLoader().load()
