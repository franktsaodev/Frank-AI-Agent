import pytest

from app.config_loaders.environment_reader import (
    EnvironmentReader,
)


def test_get_required_should_return_environment_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_REQUIRED_VALUE",
        "configured-value",
    )

    reader = EnvironmentReader()

    result = reader.get_required(
        "TEST_REQUIRED_VALUE",
    )

    assert result == "configured-value"


def test_get_required_should_reject_missing_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "TEST_REQUIRED_VALUE",
        raising=False,
    )

    reader = EnvironmentReader()

    with pytest.raises(
        RuntimeError,
        match=("Required environment variable is missing: TEST_REQUIRED_VALUE"),
    ):
        reader.get_required(
            "TEST_REQUIRED_VALUE",
        )


def test_get_required_should_reject_blank_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_REQUIRED_VALUE",
        "   ",
    )

    reader = EnvironmentReader()

    with pytest.raises(
        RuntimeError,
        match=("Required environment variable is missing: TEST_REQUIRED_VALUE"),
    ):
        reader.get_required(
            "TEST_REQUIRED_VALUE",
        )


def test_get_str_should_return_environment_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_STRING_VALUE",
        "configured-value",
    )

    reader = EnvironmentReader()

    result = reader.get_str(
        name="TEST_STRING_VALUE",
        default="default-value",
    )

    assert result == "configured-value"


def test_get_str_should_return_default_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "TEST_STRING_VALUE",
        raising=False,
    )

    reader = EnvironmentReader()

    result = reader.get_str(
        name="TEST_STRING_VALUE",
        default="default-value",
    )

    assert result == "default-value"


def test_get_str_should_return_default_when_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_STRING_VALUE",
        "   ",
    )

    reader = EnvironmentReader()

    result = reader.get_str(
        name="TEST_STRING_VALUE",
        default="default-value",
    )

    assert result == "default-value"


def test_get_int_should_parse_integer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_INTEGER_VALUE",
        "12",
    )

    reader = EnvironmentReader()

    result = reader.get_int(
        name="TEST_INTEGER_VALUE",
        default=5,
    )

    assert result == 12


def test_get_int_should_return_default_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "TEST_INTEGER_VALUE",
        raising=False,
    )

    reader = EnvironmentReader()

    result = reader.get_int(
        name="TEST_INTEGER_VALUE",
        default=5,
    )

    assert result == 5


def test_get_int_should_return_default_when_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_INTEGER_VALUE",
        "   ",
    )

    reader = EnvironmentReader()

    result = reader.get_int(
        name="TEST_INTEGER_VALUE",
        default=5,
    )

    assert result == 5


def test_get_int_should_reject_non_integer_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_INTEGER_VALUE",
        "invalid",
    )

    reader = EnvironmentReader()

    with pytest.raises(
        RuntimeError,
        match=("Environment variable TEST_INTEGER_VALUE must be an integer"),
    ):
        reader.get_int(
            name="TEST_INTEGER_VALUE",
            default=5,
        )


def test_get_float_should_parse_number(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_FLOAT_VALUE",
        "1.5",
    )

    reader = EnvironmentReader()

    result = reader.get_float(
        name="TEST_FLOAT_VALUE",
        default=2.0,
    )

    assert result == 1.5


def test_get_float_should_parse_integer_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_FLOAT_VALUE",
        "3",
    )

    reader = EnvironmentReader()

    result = reader.get_float(
        name="TEST_FLOAT_VALUE",
        default=2.0,
    )

    assert result == 3.0


def test_get_float_should_return_default_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "TEST_FLOAT_VALUE",
        raising=False,
    )

    reader = EnvironmentReader()

    result = reader.get_float(
        name="TEST_FLOAT_VALUE",
        default=2.0,
    )

    assert result == 2.0


def test_get_float_should_return_default_when_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_FLOAT_VALUE",
        "   ",
    )

    reader = EnvironmentReader()

    result = reader.get_float(
        name="TEST_FLOAT_VALUE",
        default=2.0,
    )

    assert result == 2.0


def test_get_float_should_reject_non_numeric_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_FLOAT_VALUE",
        "invalid",
    )

    reader = EnvironmentReader()

    with pytest.raises(
        RuntimeError,
        match=("Environment variable TEST_FLOAT_VALUE must be a number"),
    ):
        reader.get_float(
            name="TEST_FLOAT_VALUE",
            default=2.0,
        )


@pytest.mark.parametrize(
    "raw_value",
    [
        "true",
        "TRUE",
        "1",
        "yes",
        "on",
    ],
)
def test_get_bool_should_parse_true_values(
    monkeypatch: pytest.MonkeyPatch,
    raw_value: str,
) -> None:
    monkeypatch.setenv(
        "TEST_BOOLEAN_VALUE",
        raw_value,
    )

    result = EnvironmentReader().get_bool(
        name="TEST_BOOLEAN_VALUE",
        default=False,
    )

    assert result is True


@pytest.mark.parametrize(
    "raw_value",
    [
        "false",
        "FALSE",
        "0",
        "no",
        "off",
    ],
)
def test_get_bool_should_parse_false_values(
    monkeypatch: pytest.MonkeyPatch,
    raw_value: str,
) -> None:
    monkeypatch.setenv(
        "TEST_BOOLEAN_VALUE",
        raw_value,
    )

    result = EnvironmentReader().get_bool(
        name="TEST_BOOLEAN_VALUE",
        default=True,
    )

    assert result is False


def test_get_bool_should_return_default_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "TEST_BOOLEAN_VALUE",
        raising=False,
    )

    result = EnvironmentReader().get_bool(
        name="TEST_BOOLEAN_VALUE",
        default=True,
    )

    assert result is True


def test_get_bool_should_return_default_when_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_BOOLEAN_VALUE",
        "   ",
    )

    result = EnvironmentReader().get_bool(
        name="TEST_BOOLEAN_VALUE",
        default=False,
    )

    assert result is False


def test_get_bool_should_reject_invalid_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "TEST_BOOLEAN_VALUE",
        "maybe",
    )

    with pytest.raises(
        RuntimeError,
        match=("Environment variable TEST_BOOLEAN_VALUE must be a boolean"),
    ):
        EnvironmentReader().get_bool(
            name="TEST_BOOLEAN_VALUE",
            default=False,
        )
