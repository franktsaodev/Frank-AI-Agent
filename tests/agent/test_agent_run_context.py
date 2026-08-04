import pytest

from app.agent.agent_run_context import (
    AgentRunContext,
)


def test_should_use_empty_metadata_by_default() -> None:
    context = AgentRunContext()

    assert context.metadata == {}


def test_should_store_metadata() -> None:
    metadata = {
        "request_id": "request-123",
        "user_id": "frank",
    }

    context = AgentRunContext(
        metadata=metadata,
    )

    assert context.metadata == metadata


def test_should_copy_metadata() -> None:
    metadata = {
        "request_id": "request-123",
    }

    context = AgentRunContext(
        metadata=metadata,
    )

    metadata["request_id"] = "changed"

    assert context.metadata["request_id"] == "request-123"


def test_metadata_should_be_read_only() -> None:
    context = AgentRunContext(
        metadata={
            "request_id": "request-123",
        },
    )

    with pytest.raises(
        TypeError,
    ):
        context.metadata["request_id"] = "changed"  # pyright: ignore[reportIndexIssue]
