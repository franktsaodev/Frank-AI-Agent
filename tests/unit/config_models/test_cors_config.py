import pytest

from app.config_models.cors_config import CorsConfig


def test_should_accept_allowed_origins() -> None:
    config = CorsConfig(
        allowed_origins=(
            "http://localhost:5173",
            "https://agent.example.com",
        ),
    )

    assert config.allowed_origins == (
        "http://localhost:5173",
        "https://agent.example.com",
    )


def test_should_reject_empty_allowed_origins() -> None:
    with pytest.raises(
        ValueError,
        match="allowed_origins cannot be empty",
    ):
        CorsConfig(
            allowed_origins=(),
        )


@pytest.mark.parametrize(
    "origin",
    [
        "",
        "   ",
        " http://localhost:5173",
        "http://localhost:5173 ",
    ],
)
def test_should_reject_invalid_origin(
    origin: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="allowed_origins must contain non-blank, trimmed origins",
    ):
        CorsConfig(
            allowed_origins=(origin,),
        )
