import pytest

from app.config_models.prompt_config import PromptConfig


def test_should_store_prompt_settings() -> None:
    config = PromptConfig(
        prompt_name="system_prompt.txt",
        language="Traditional Chinese",
    )

    assert config.prompt_name == "system_prompt.txt"
    assert config.language == "Traditional Chinese"


def test_should_reject_empty_prompt_name() -> None:
    with pytest.raises(
        ValueError,
        match="prompt_name cannot be empty",
    ):
        PromptConfig(
            prompt_name="   ",
            language="Traditional Chinese",
        )


def test_should_reject_empty_language() -> None:
    with pytest.raises(
        ValueError,
        match="language cannot be empty",
    ):
        PromptConfig(
            prompt_name="system_prompt.txt",
            language="   ",
        )
