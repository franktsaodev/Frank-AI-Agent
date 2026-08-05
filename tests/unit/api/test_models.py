import pytest
from pydantic import ValidationError

from app.api.models import ChatRequest, ChatResponse


def test_chat_request_should_store_message() -> None:
    request = ChatRequest(
        message="Hello",
    )

    assert request.message == "Hello"


def test_chat_request_should_strip_message() -> None:
    request = ChatRequest(
        message="  Hello  ",
    )

    assert request.message == "Hello"


def test_chat_request_should_reject_empty_message() -> None:
    with pytest.raises(
        ValidationError,
        match="message must not be blank",
    ):
        ChatRequest(
            message="",
        )


def test_chat_request_should_reject_blank_message() -> None:
    with pytest.raises(
        ValidationError,
        match="message must not be blank",
    ):
        ChatRequest(
            message="   ",
        )


def test_chat_request_should_use_empty_metadata_by_default() -> None:
    request = ChatRequest(
        message="Hello",
    )

    assert request.metadata == {}


def test_chat_request_should_store_metadata() -> None:
    request = ChatRequest(
        message="Hello",
        metadata={
            "request_id": "request-123",
            "user_id": "frank",
        },
    )

    assert request.metadata == {
        "request_id": "request-123",
        "user_id": "frank",
    }


def test_chat_request_should_use_independent_metadata() -> None:
    first_request = ChatRequest(
        message="First",
    )

    second_request = ChatRequest(
        message="Second",
    )

    first_request.metadata["request_id"] = "request-123"

    assert second_request.metadata == {}


def test_chat_request_should_reject_message_over_max_length() -> None:
    with pytest.raises(
        ValidationError,
        match="String should have at most 10000 characters",
    ):
        ChatRequest(
            message="a" * 10_001,
        )


def test_chat_response_should_store_response() -> None:
    response = ChatResponse(
        response="Hello Frank!",
    )

    assert response.response == "Hello Frank!"
