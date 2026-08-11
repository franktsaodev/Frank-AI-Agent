from app.retrieval.policies.always_retrieve_policy import AlwaysRetrievePolicy


def test_should_always_retrieve() -> None:
    policy = AlwaysRetrievePolicy()

    assert policy.should_retrieve("Hello") is True
    assert policy.should_retrieve("What is RAG?") is True
