import pytest

from app.config_models.tool_plugin_config import (
    ToolPluginConfig,
)
from app.tools.plugins.tool_plugin_name import (
    ToolPluginName,
)


def test_should_enable_core_plugin_by_default() -> None:
    config = ToolPluginConfig()

    assert config.enabled_plugins == (ToolPluginName.CORE,)


def test_should_allow_no_plugins() -> None:
    config = ToolPluginConfig(
        enabled_plugins=(),
    )

    assert config.enabled_plugins == ()


def test_should_store_enabled_plugins() -> None:
    config = ToolPluginConfig(
        enabled_plugins=(ToolPluginName.CORE,),
    )

    assert config.enabled_plugins == (ToolPluginName.CORE,)


def test_should_reject_duplicate_plugins() -> None:
    with pytest.raises(
        ValueError,
        match="enabled_plugins cannot contain duplicates",
    ):
        ToolPluginConfig(
            enabled_plugins=(
                ToolPluginName.CORE,
                ToolPluginName.CORE,
            ),
        )
