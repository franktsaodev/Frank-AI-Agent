import pytest

from app.models.client_response import ClientResponse
from app.models.client_stream_event import (
    ClientContentDelta,
    ClientStreamCompleted,
)


def test_content_delta_should_store_content() -> None:
    event = ClientContentDelta(
        content="Hello",
    )

    assert event.content == "Hello"


def test_content_delta_should_allow_whitespace() -> None:
    event = ClientContentDelta(
        content=" ",
    )

    assert event.content == " "


def test_content_delta_should_reject_empty_content() -> None:
    with pytest.raises(
        ValueError,
        match="Stream content delta cannot be empty.",
    ):
        ClientContentDelta(
            content="",
        )


def test_completed_event_should_store_response() -> None:
    response = ClientResponse(
        content="Complete response",
    )

    event = ClientStreamCompleted(
        response=response,
    )

    assert event.response is response
