from dataclasses import FrozenInstanceError

import pytest

from app.config_models.memory_policy_config import (
    MemoryPolicyConfig,
)


def test_should_store_allowed_keys() -> None:
    config = MemoryPolicyConfig(
        allowed_keys=frozenset(
            {
                "user_name",
                "occupation",
            }
        ),
    )

    assert config.allowed_keys == frozenset(
        {
            "user_name",
            "occupation",
        }
    )


def test_should_use_empty_allowed_keys_by_default() -> None:
    config = MemoryPolicyConfig()

    assert config.allowed_keys == frozenset()


def test_should_be_immutable() -> None:
    config = MemoryPolicyConfig(
        allowed_keys=frozenset(
            {
                "user_name",
            }
        ),
    )

    with pytest.raises(FrozenInstanceError):
        config.allowed_keys = frozenset(
            {
                "occupation",
            }
        )
