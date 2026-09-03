from collections.abc import Iterator

import pytest

from app.api.runtime_provider import (
    get_runtime_info,
)


@pytest.fixture(autouse=True)
def clear_runtime_cache() -> Iterator[None]:
    get_runtime_info.cache_clear()

    yield

    get_runtime_info.cache_clear()


def test_runtime_provider_should_return_runtime_information(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "APP_SERVICE_NAME",
        raising=False,
    )
    monkeypatch.delenv(
        "APP_VERSION",
        raising=False,
    )

    runtime = get_runtime_info()

    assert runtime.service_name == "Frank AI Agent"
    assert runtime.version == "1.2.0"


def test_runtime_provider_should_use_runtime_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "APP_SERVICE_NAME",
        "Test Agent",
    )
    monkeypatch.setenv(
        "APP_VERSION",
        "2.0.0",
    )

    runtime = get_runtime_info()

    assert runtime.service_name == "Test Agent"
    assert runtime.version == "2.0.0"
