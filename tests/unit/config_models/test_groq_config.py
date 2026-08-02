import pytest

from app.config_models.groq_config import GroqConfig


def test_should_store_groq_settings() -> None:
    config = GroqConfig(
        api_key="test-api-key",
        model="test-model",
        temperature=0.7,
        max_completion_tokens=1024,
    )

    assert config.api_key == "test-api-key"
    assert config.model == "test-model"
    assert config.temperature == 0.7
    assert config.max_completion_tokens == 1024


def test_should_reject_empty_api_key() -> None:
    with pytest.raises(
        ValueError,
        match="api_key cannot be empty",
    ):
        GroqConfig(
            api_key="   ",
            model="test-model",
        )


def test_should_reject_empty_model() -> None:
    with pytest.raises(
        ValueError,
        match="model cannot be empty",
    ):
        GroqConfig(
            api_key="test-api-key",
            model="   ",
        )


def test_should_reject_max_completion_tokens_less_than_one() -> None:
    with pytest.raises(
        ValueError,
        match="max_completion_tokens must be at least 1",
    ):
        GroqConfig(
            api_key="test-api-key",
            model="test-model",
            max_completion_tokens=0,
        )
