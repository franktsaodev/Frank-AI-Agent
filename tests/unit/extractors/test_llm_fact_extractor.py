import json

import pytest

from app.extractors.llm_fact_extractor import LLMFactExtractor
from app.models.client_response import ClientResponse
from app.models.message_role import MessageRole
from app.tracing.trace_context import TraceContext
from tests.fakes.fake_client import FakeClient


@pytest.fixture
def extractor() -> LLMFactExtractor:
    return LLMFactExtractor(
        client=FakeClient(
            response=ClientResponse(),
        ),
    )


def test_build_messages_contains_system_and_user_messages(
    extractor: LLMFactExtractor,
) -> None:
    messages = extractor._build_messages(
        "My name is Frank.",
    )

    prompt_content = messages[0].content

    assert len(messages) == 2
    assert messages[0].role == MessageRole.SYSTEM
    assert prompt_content is not None
    assert "valid JSON object" in prompt_content
    assert messages[1].role == MessageRole.USER
    assert messages[1].content == "My name is Frank."


def test_extract_calls_client_and_returns_parsed_facts(
    trace_context: TraceContext,
) -> None:
    client = FakeClient(
        response=ClientResponse(
            content='{"user_name": "Frank"}',
        ),
    )

    extractor = LLMFactExtractor(
        client=client,
    )

    result = extractor.extract(
        "My name is Frank.",
        trace_context=trace_context,
    )

    assert result == {
        "user_name": "Frank",
    }

    assert client.call_count == 1
    assert len(client.received_messages) == 2
    assert client.received_messages[0].role == MessageRole.SYSTEM
    assert client.received_messages[1].role == MessageRole.USER
    assert client.received_messages[1].content == "My name is Frank."


def test_parse_response_returns_facts(
    extractor: LLMFactExtractor,
) -> None:
    result = extractor._parse_response(
        '{"user_name": "Frank", "location": "Hai Phong"}',
    )

    assert result == {
        "user_name": "Frank",
        "location": "Hai Phong",
    }


def test_parse_response_returns_empty_dict(
    extractor: LLMFactExtractor,
) -> None:
    result = extractor._parse_response(
        "{}",
    )

    assert result == {}


def test_parse_response_raises_for_invalid_json(
    extractor: LLMFactExtractor,
) -> None:
    with pytest.raises(json.JSONDecodeError):
        extractor._parse_response(
            "not json",
        )


def test_parse_response_raises_for_json_array(
    extractor: LLMFactExtractor,
) -> None:
    with pytest.raises(
        ValueError,
        match="must be a JSON object",
    ):
        extractor._parse_response(
            '["Frank"]',
        )


def test_parse_response_raises_for_non_string_value(
    extractor: LLMFactExtractor,
) -> None:
    with pytest.raises(
        ValueError,
        match="Fact values must be strings",
    ):
        extractor._parse_response(
            '{"age": 32}',
        )


def test_clean_response_removes_json_code_block(
    extractor: LLMFactExtractor,
) -> None:
    result = extractor._clean_response(
        "```json\n{}\n```",
    )

    assert result == "{}"


def test_clean_response_removes_plain_code_block(
    extractor: LLMFactExtractor,
) -> None:
    result = extractor._clean_response(
        "```\n{}\n```",
    )

    assert result == "{}"


def test_clean_response_strips_whitespace(
    extractor: LLMFactExtractor,
) -> None:
    result = extractor._clean_response(
        "\n  {}  \n",
    )

    assert result == "{}"


def test_clean_response_keeps_clean_json(
    extractor: LLMFactExtractor,
) -> None:
    result = extractor._clean_response(
        "{}",
    )

    assert result == "{}"


def test_extract_cleans_markdown_and_returns_parsed_facts(
    trace_context: TraceContext,
) -> None:
    client = FakeClient(
        response=ClientResponse(
            content=('```json\n{"user_name": "Frank"}\n```'),
        ),
    )

    extractor = LLMFactExtractor(
        client=client,
    )

    result = extractor.extract(
        "My name is Frank.",
        trace_context=trace_context,
    )

    assert result == {
        "user_name": "Frank",
    }
