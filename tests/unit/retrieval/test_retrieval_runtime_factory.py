import logging
from pathlib import Path

import pytest

from app.config_models.retrieval_config import RetrievalConfig
from app.retrieval.policies.keyword_retrieval_policy import (
    KeywordRetrievalPolicy,
)
from app.retrieval.policies.never_retrieve_policy import NeverRetrievePolicy
from app.retrieval.retrieval_runtime_factory import RetrievalRuntimeFactory
from app.retrieval.retrievers.no_op_retriever import NoOpRetriever
from app.retrieval.retrievers.vector_store_retriever import (
    VectorStoreRetriever,
)


def create_retrieval_config(
    *,
    enabled: bool = True,
    knowledge_path: str = "knowledge",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    top_k: int = 5,
    min_score: float = -1.0,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    trigger_keywords: frozenset[str] = frozenset(
        {
            "documentation",
            "manual",
            "session",
        }
    ),
) -> RetrievalConfig:
    return RetrievalConfig(
        enabled=enabled,
        knowledge_path=knowledge_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        top_k=top_k,
        min_score=min_score,
        embedding_model=embedding_model,
        trigger_keywords=trigger_keywords,
    )


def test_create_should_return_disabled_runtime_when_retrieval_is_disabled() -> None:
    factory = RetrievalRuntimeFactory()

    runtime = factory.create(
        create_retrieval_config(
            enabled=False,
        )
    )

    assert isinstance(runtime.retriever, NoOpRetriever)
    assert isinstance(runtime.retrieval_policy, NeverRetrievePolicy)


def test_create_should_fail_when_knowledge_path_does_not_exist(
    tmp_path: Path,
) -> None:
    factory = RetrievalRuntimeFactory()

    missing_path = tmp_path / "missing"

    with pytest.raises(
        RuntimeError,
        match="Retrieval knowledge path does not exist",
    ):
        factory.create(
            create_retrieval_config(
                knowledge_path=str(missing_path),
            )
        )


def test_create_should_fail_when_no_knowledge_documents_are_indexed(
    tmp_path: Path,
) -> None:
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()

    factory = RetrievalRuntimeFactory()

    with pytest.raises(
        RuntimeError,
        match="No supported knowledge documents were indexed",
    ):
        factory.create(
            create_retrieval_config(
                knowledge_path=str(knowledge_dir),
            )
        )


def test_create_should_log_when_retrieval_is_disabled(
    caplog: pytest.LogCaptureFixture,
) -> None:
    factory = RetrievalRuntimeFactory()

    with caplog.at_level(
        logging.INFO,
        logger="app.retrieval.retrieval_runtime_factory",
    ):
        factory.create(
            create_retrieval_config(
                enabled=False,
            )
        )

    assert "Retrieval is disabled" in caplog.text


def test_create_should_use_keyword_retrieval_policy_when_enabled(
    tmp_path: Path,
) -> None:
    knowledge_file = tmp_path / "knowledge.txt"
    knowledge_file.write_text(
        "Frank AI Agent session documentation.",
        encoding="utf-8",
    )

    factory = RetrievalRuntimeFactory()

    runtime = factory.create(
        create_retrieval_config(
            knowledge_path=str(knowledge_file),
            trigger_keywords=frozenset(
                {
                    "documentation",
                    "session",
                }
            ),
        )
    )

    assert isinstance(
        runtime.retrieval_policy,
        KeywordRetrievalPolicy,
    )

    assert runtime.retrieval_policy.should_retrieve("How do sessions expire?")

    assert not runtime.retrieval_policy.should_retrieve("Hello, how are you?")


def test_create_should_pass_min_score_to_vector_store_retriever(
    tmp_path: Path,
) -> None:
    knowledge_file = tmp_path / "knowledge.txt"
    knowledge_file.write_text(
        "Frank AI Agent retrieval documentation.",
        encoding="utf-8",
    )

    factory = RetrievalRuntimeFactory()

    runtime = factory.create(
        create_retrieval_config(
            knowledge_path=str(knowledge_file),
            min_score=0.65,
        )
    )

    assert isinstance(
        runtime.retriever,
        VectorStoreRetriever,
    )
    assert runtime.retriever._min_score == 0.65
