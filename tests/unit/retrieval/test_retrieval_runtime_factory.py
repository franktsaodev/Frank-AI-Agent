from pathlib import Path

import pytest

from app.config_models.retrieval_config import RetrievalConfig
from app.retrieval.policies.never_retrieve_policy import NeverRetrievePolicy
from app.retrieval.retrieval_runtime_factory import RetrievalRuntimeFactory
from app.retrieval.retrievers.no_op_retriever import NoOpRetriever


def test_create_should_return_disabled_runtime_when_retrieval_is_disabled() -> None:
    factory = RetrievalRuntimeFactory()

    runtime = factory.create(
        RetrievalConfig(
            enabled=False,
            knowledge_path="knowledge/knowledge.txt",
            chunk_size=500,
            chunk_overlap=50,
            top_k=5,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        )
    )

    assert isinstance(runtime.retriever, NoOpRetriever)
    assert isinstance(runtime.retrieval_policy, NeverRetrievePolicy)


def test_create_should_fail_when_knowledge_path_does_not_exist(
    tmp_path: Path,
) -> None:
    factory = RetrievalRuntimeFactory()

    missing_path = tmp_path / "missing"

    config = RetrievalConfig(
        enabled=True,
        knowledge_path=str(missing_path),
        chunk_size=500,
        chunk_overlap=50,
        top_k=5,
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    )

    with pytest.raises(
        RuntimeError,
        match="Retrieval knowledge path does not exist",
    ):
        factory.create(config)
