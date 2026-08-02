import pytest

from app.config_models.memory_config import MemoryConfig


def test_should_store_max_history_rounds() -> None:
    config = MemoryConfig(
        max_history_rounds=2,
    )

    assert config.max_history_rounds == 2


def test_should_reject_max_history_rounds_less_than_one() -> None:
    with pytest.raises(
        ValueError,
        match="max_history_rounds must be at least 1",
    ):
        MemoryConfig(
            max_history_rounds=0,
        )
