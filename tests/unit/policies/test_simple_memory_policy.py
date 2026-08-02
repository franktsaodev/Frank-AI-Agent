import pytest

from app.config_models.memory_policy_config import (
    MemoryPolicyConfig,
)
from app.policies.simple_memory_policy import SimpleMemoryPolicy


@pytest.fixture
def policy() -> SimpleMemoryPolicy:
    return SimpleMemoryPolicy(
        config=MemoryPolicyConfig(
            allowed_keys=frozenset(
                {
                    "user_name",
                    "favorite_music",
                    "occupation",
                }
            ),
        ),
    )


def test_should_remember_returns_true_for_allowed_key(
    policy: SimpleMemoryPolicy,
):
    assert policy.should_remember(
        "user_name",
        "Frank",
    )


def test_should_remember_returns_false_for_unknown_key(
    policy: SimpleMemoryPolicy,
):
    assert not policy.should_remember(
        "current_emotion",
        "Tired",
    )


def test_should_not_remember_allowed_key_with_empty_value(
    policy: SimpleMemoryPolicy,
) -> None:
    assert not policy.should_remember(
        "user_name",
        "",
    )


def test_should_not_remember_allowed_key_with_whitespace_value(
    policy: SimpleMemoryPolicy,
) -> None:
    assert not policy.should_remember(
        "user_name",
        "   ",
    )


def test_should_use_allowed_keys_from_config() -> None:
    policy = SimpleMemoryPolicy(
        config=MemoryPolicyConfig(
            allowed_keys=frozenset(
                {
                    "custom_key",
                }
            ),
        ),
    )

    assert policy.should_remember(
        "custom_key",
        "custom value",
    )

    assert not policy.should_remember(
        "user_name",
        "Frank",
    )
