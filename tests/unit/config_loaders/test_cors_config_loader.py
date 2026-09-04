from app.config_loaders.cors_config_loader import CorsConfigLoader
from app.config_loaders.environment_reader import EnvironmentReader


def test_load_should_use_default_origin(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "CORS_ALLOWED_ORIGINS",
        raising=False,
    )

    loader = CorsConfigLoader(
        environment_reader=EnvironmentReader(),
    )

    config = loader.load()

    assert config.allowed_origins == ("http://localhost:5173",)


def test_load_should_parse_multiple_origins(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        ("http://localhost:5173, https://agent.example.com"),
    )

    loader = CorsConfigLoader(
        environment_reader=EnvironmentReader(),
    )

    config = loader.load()

    assert config.allowed_origins == (
        "http://localhost:5173",
        "https://agent.example.com",
    )


def test_load_should_ignore_empty_entries(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        ("http://localhost:5173, ,https://agent.example.com,"),
    )

    loader = CorsConfigLoader(
        environment_reader=EnvironmentReader(),
    )

    config = loader.load()

    assert config.allowed_origins == (
        "http://localhost:5173",
        "https://agent.example.com",
    )
