import pytest

from app.extractors.regex_fact_extractor import RegexFactExtractor


@pytest.fixture
def extractor() -> RegexFactExtractor:
    return RegexFactExtractor()


def test_extracts_user_name(
    extractor: RegexFactExtractor,
) -> None:
    facts = extractor.extract("My name is Frank.")

    assert facts == {
        "user_name": "Frank",
    }


def test_extracts_user_name_case_insensitively(
    extractor: RegexFactExtractor,
) -> None:
    facts = extractor.extract("MY NAME IS Frank.")

    assert facts == {
        "user_name": "Frank",
    }


def test_extracts_hyphenated_name(
    extractor: RegexFactExtractor,
) -> None:
    facts = extractor.extract("My name is Mary-Jane.")

    assert facts == {
        "user_name": "Mary-Jane",
    }


def test_returns_empty_dict_when_no_fact_is_found(
    extractor: RegexFactExtractor,
) -> None:
    facts = extractor.extract("How are you?")

    assert facts == {}


def test_returns_empty_dict_for_empty_message(
    extractor: RegexFactExtractor,
) -> None:
    facts = extractor.extract("   ")

    assert facts == {}


def test_raises_type_error_for_non_string_message(
    extractor: RegexFactExtractor,
) -> None:
    with pytest.raises(
        TypeError,
        match="user_message must be a string",
    ):
        extractor.extract(123)  # type: ignore[arg-type]
