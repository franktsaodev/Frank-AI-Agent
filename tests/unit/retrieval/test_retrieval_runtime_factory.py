import logging
from pathlib import Path

import pytest

from app.config_models.retrieval_config import RetrievalConfig
from app.retrieval.policies.never_retrieve_policy import NeverRetrievePolicy
from app.retrieval.retrieval_runtime_factory import RetrievalRuntimeFactory
from app.retrieval.retrievers.no_op_retriever import NoOpRetriever


def create_retrieval_config(
    *,
    enabled: bool = True,
    knowledge_path: str = "knowledge",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    top_k: int = 5,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> RetrievalConfig:
    return RetrievalConfig(
        enabled=enabled,
        knowledge_path=knowledge_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        top_k=top_k,
        embedding_model=embedding_model,
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
