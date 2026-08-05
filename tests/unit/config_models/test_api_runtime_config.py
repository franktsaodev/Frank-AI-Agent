import pytest

from app.config_models.api_runtime_config import (
    ApiRuntimeConfig,
)


def test_should_store_runtime_configuration() -> None:
    config = ApiRuntimeConfig(
        service_name="Frank AI Agent",
        version="0.1.0",
    )

    assert config.service_name == "Frank AI Agent"
    assert config.version == "0.1.0"


def test_should_reject_blank_service_name() -> None:
    with pytest.raises(
        ValueError,
        match="service_name must not be blank",
    ):
        ApiRuntimeConfig(
            service_name="   ",
            version="0.1.0",
        )


def test_should_reject_blank_version() -> None:
    with pytest.raises(
        ValueError,
        match="version must not be blank",
    ):
        ApiRuntimeConfig(
            service_name="Frank AI Agent",
            version="   ",
        )
