import pytest

from app.retrieval.citations.citation_guard import CitationGuard
from app.retrieval.citations.invalid_citation_error import (
    InvalidCitationError,
)
from app.retrieval.retrieved_context import RetrievedContext


def test_should_replace_citation_token_with_trusted_source_and_page() -> None:
    guard = CitationGuard()
    contexts = [
        RetrievedContext(
            content="The application uses a modular architecture.",
            source="architecture.pdf",
            page=2,
        ),
    ]

    result = guard.apply(
        "The application uses a modular architecture. [source:1]",
        contexts,
    )

    assert result == (
        "The application uses a modular architecture. "
        "[Source: architecture.pdf (page 2)]"
    )


def test_should_replace_citation_token_with_source_without_page() -> None:
    guard = CitationGuard()
    contexts = [
        RetrievedContext(
            content="Sessions use sliding expiration.",
            source="session.md",
        ),
    ]

    result = guard.apply(
        "Sessions use sliding expiration. [source:1]",
        contexts,
    )

    assert result == ("Sessions use sliding expiration. [Source: session.md]")


def test_should_leave_response_without_citation_tokens_unchanged() -> None:
    guard = CitationGuard()

    result = guard.apply(
        "Hello Frank!",
        [],
    )

    assert result == "Hello Frank!"


def test_should_reject_unknown_citation_token() -> None:
    guard = CitationGuard()
    contexts = [
        RetrievedContext(
            content="Sessions use sliding expiration.",
            source="session.md",
        ),
    ]

    with pytest.raises(
        InvalidCitationError,
        match="Unknown citation token: source:2",
    ):
        guard.apply(
            "Sessions use sliding expiration. [source:2]",
            contexts,
        )


def test_should_reject_citation_when_no_sources_are_available() -> None:
    guard = CitationGuard()

    with pytest.raises(
        InvalidCitationError,
        match="Unknown citation token: source:1",
    ):
        guard.apply(
            "This came from a document. [source:1]",
            [],
        )


def test_should_number_only_contexts_with_sources() -> None:
    guard = CitationGuard()
    contexts = [
        RetrievedContext(
            content="Context without source metadata.",
        ),
        RetrievedContext(
            content="Deployment uses Docker.",
            source="deployment.txt",
        ),
    ]

    result = guard.apply(
        "Deployment uses Docker. [source:1]",
        contexts,
    )

    assert result == ("Deployment uses Docker. [Source: deployment.txt]")


def test_should_reject_malformed_citation_token() -> None:
    guard = CitationGuard()
    contexts = [
        RetrievedContext(
            content="Sessions use sliding expiration.",
            source="session.md",
        ),
    ]

    with pytest.raises(
        InvalidCitationError,
        match="Untrusted citation format",
    ):
        guard.apply(
            "Sessions use sliding expiration. [source:abc]",
            contexts,
        )


@pytest.mark.parametrize(
    "response",
    [
        ("Sessions use sliding expiration. [Source: fake.pdf (page 99)]"),
        ("Sessions use sliding expiration.\nSource: fake.pdf (page 99)"),
    ],
)
def test_should_reject_direct_source_labels(
    response: str,
) -> None:
    guard = CitationGuard()
    contexts = [
        RetrievedContext(
            content="Sessions use sliding expiration.",
            source="session.md",
        ),
    ]

    with pytest.raises(
        InvalidCitationError,
        match="Untrusted citation format",
    ):
        guard.apply(
            response,
            contexts,
        )


@pytest.mark.parametrize(
    "token",
    [
        "【source:1】",
        "【source：1】",
    ],
)
def test_should_replace_localized_citation_token(
    token: str,
) -> None:
    guard = CitationGuard()
    contexts = [
        RetrievedContext(
            content="Sessions use sliding expiration.",
            source="session.md",
            page=2,
        ),
    ]

    result = guard.apply(
        f"Sessions use sliding expiration. {token}",
        contexts,
    )

    assert result == ("Sessions use sliding expiration. [Source: session.md (page 2)]")


@pytest.mark.parametrize(
    "token",
    [
        "【source:abc】",
        "【source：abc】",
    ],
)
def test_should_reject_malformed_localized_citation_token(
    token: str,
) -> None:
    guard = CitationGuard()

    with pytest.raises(
        InvalidCitationError,
        match="Untrusted citation format",
    ):
        guard.apply(
            f"Unverified response. {token}",
            [],
        )
