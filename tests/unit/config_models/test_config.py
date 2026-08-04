import pytest

from app.config import get_required_env


def test_get_required_env_should_return_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_REQUIRED_VALUE",
        "configured-value",
    )

    assert (
        get_required_env(
            "TEST_REQUIRED_VALUE",
        )
        == "configured-value"
    )


def test_get_required_env_should_reject_missing_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "TEST_REQUIRED_VALUE",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match=("Required environment variable is missing: TEST_REQUIRED_VALUE"),
    ):
        get_required_env(
            "TEST_REQUIRED_VALUE",
        )


def test_get_required_env_should_reject_blank_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_REQUIRED_VALUE",
        "   ",
    )

    with pytest.raises(
        RuntimeError,
        match=("Required environment variable is missing: TEST_REQUIRED_VALUE"),
    ):
        get_required_env(
            "TEST_REQUIRED_VALUE",
        )
