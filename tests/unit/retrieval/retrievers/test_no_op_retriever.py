from app.retrieval.retrievers.no_op_retriever import NoOpRetriever


def test_should_return_no_results() -> None:
    retriever = NoOpRetriever()

    results = retriever.retrieve("What is RAG?")

    assert results == []
