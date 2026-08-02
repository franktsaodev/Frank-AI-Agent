import pytest

from app.config_models.agent_config import AgentConfig


def test_should_use_default_max_iterations() -> None:
    config = AgentConfig()

    assert config.max_iterations == 10


def test_should_store_max_iterations() -> None:
    config = AgentConfig(
        max_iterations=5,
    )

    assert config.max_iterations == 5


def test_should_reject_max_iterations_less_than_one() -> None:
    with pytest.raises(
        ValueError,
        match="max_iterations must be at least 1",
    ):
        AgentConfig(
            max_iterations=0,
        )
