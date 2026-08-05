import pytest

from app.config_loaders.prompt_config_loader import (
    PromptConfigLoader,
)


def test_load_should_use_default_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "PROMPT_NAME",
        raising=False,
    )
    monkeypatch.delenv(
        "PROMPT_USER_NAME",
        raising=False,
    )
    monkeypatch.delenv(
        "PROMPT_LANGUAGE",
        raising=False,
    )

    config = PromptConfigLoader().load()

    assert config.prompt_name == "system_prompt.txt"
    assert config.user_name == "Frank"
    assert config.language == "Traditional Chinese"


def test_load_should_parse_environment_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "PROMPT_NAME",
        "custom_prompt.txt",
    )
    monkeypatch.setenv(
        "PROMPT_USER_NAME",
        "David",
    )
    monkeypatch.setenv(
        "PROMPT_LANGUAGE",
        "English",
    )

    config = PromptConfigLoader().load()

    assert config.prompt_name == "custom_prompt.txt"
    assert config.user_name == "David"
    assert config.language == "English"


def test_load_should_use_defaults_for_blank_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "PROMPT_NAME",
        "   ",
    )
    monkeypatch.setenv(
        "PROMPT_USER_NAME",
        "   ",
    )
    monkeypatch.setenv(
        "PROMPT_LANGUAGE",
        "   ",
    )

    config = PromptConfigLoader().load()

    assert config.prompt_name == "system_prompt.txt"
    assert config.user_name == "Frank"
    assert config.language == "Traditional Chinese"
