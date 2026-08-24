from app.retrieval.policies.keyword_retrieval_policy import KeywordRetrievalPolicy


def test_should_retrieve_when_query_contains_keyword() -> None:
    policy = KeywordRetrievalPolicy(
        keywords={
            "documentation",
            "manual",
        },
    )

    assert policy.should_retrieve("What does the documentation say?") is True


def test_should_match_keywords_case_insensitively() -> None:
    policy = KeywordRetrievalPolicy(
        keywords={"documentation"},
    )

    assert policy.should_retrieve("Check the DOCUMENTATION")


def test_should_not_retrieve_when_no_keyword_matches() -> None:
    policy = KeywordRetrievalPolicy(
        keywords={"documentation"},
    )

    assert policy.should_retrieve("Hello, how are you?") is False


def test_should_not_retrieve_when_keywords_are_empty() -> None:
    policy = KeywordRetrievalPolicy(
        keywords=set(),
    )

    assert policy.should_retrieve("What does the documentation say?") is False
