from app.models.message import Message
from app.models.message_role import MessageRole
from app.prompts.prompt_composer import PromptComposer
from app.retrieval.retrieved_context import RetrievedContext


def test_compose_returns_system_and_user_messages_without_history_or_facts() -> None:
    system_message = Message(
        role=MessageRole.SYSTEM,
        content="You are a helpful assistant.",
    )

    user_message = Message(
        role=MessageRole.USER,
        content="Hello.",
    )

    composer = PromptComposer()

    result = composer.compose(
        system_message=system_message,
        history_messages=[],
        facts={},
        user_message=user_message,
    )

    assert result == [
        system_message,
        user_message,
    ]


def test_compose_includes_history_messages_between_system_and_user() -> None:
    system_message = Message(
        role=MessageRole.SYSTEM,
        content="You are a helpful assistant.",
    )

    previous_user_message = Message(
        role=MessageRole.USER,
        content="What is Python?",
    )

    assistant_message = Message(
        role=MessageRole.ASSISTANT,
        content="Python is a programming language.",
    )

    user_message = Message(
        role=MessageRole.USER,
        content="Who created it?",
    )

    composer = PromptComposer()

    result = composer.compose(
        system_message=system_message,
        history_messages=[
            previous_user_message,
            assistant_message,
        ],
        facts={},
        user_message=user_message,
    )

    assert result == [
        system_message,
        previous_user_message,
        assistant_message,
        user_message,
    ]


def test_compose_appends_facts_to_system_message_when_facts_exist() -> None:
    system_message = Message(
        role=MessageRole.SYSTEM,
        content="You are a helpful assistant.",
    )

    user_message = Message(
        role=MessageRole.USER,
        content="Hello.",
    )

    facts = {
        "user_name": "Frank",
    }

    composer = PromptComposer()

    result = composer.compose(
        system_message=system_message,
        history_messages=[],
        facts=facts,
        user_message=user_message,
    )

    assert result[0].role == MessageRole.SYSTEM
    assert result[0].content == (
        "You are a helpful assistant.\n\nUser facts:\n- user_name: Frank"
    )

    assert result[1] == user_message


def test_compose_includes_facts_and_preserves_history_order() -> None:
    system_message = Message(
        role=MessageRole.SYSTEM,
        content="You are a helpful assistant.",
    )

    previous_user_message = Message(
        role=MessageRole.USER,
        content="What is my name?",
    )

    assistant_message = Message(
        role=MessageRole.ASSISTANT,
        content="Your name is Frank.",
    )

    user_message = Message(
        role=MessageRole.USER,
        content="What music do I like?",
    )

    facts = {
        "user_name": "Frank",
        "favorite_music": "Jazz",
    }

    composer = PromptComposer()

    result = composer.compose(
        system_message=system_message,
        history_messages=[
            previous_user_message,
            assistant_message,
        ],
        facts=facts,
        user_message=user_message,
    )

    assert result == [
        Message(
            role=MessageRole.SYSTEM,
            content=(
                "You are a helpful assistant.\n\n"
                "User facts:\n"
                "- user_name: Frank\n"
                "- favorite_music: Jazz"
            ),
        ),
        previous_user_message,
        assistant_message,
        user_message,
    ]


def test_compose_does_not_modify_original_system_message() -> None:
    system_message = Message(
        role=MessageRole.SYSTEM,
        content="You are a helpful assistant.",
    )

    original_system_message = Message(
        role=MessageRole.SYSTEM,
        content="You are a helpful assistant.",
    )

    user_message = Message(
        role=MessageRole.USER,
        content="Hello.",
    )

    composer = PromptComposer()

    composer.compose(
        system_message=system_message,
        history_messages=[],
        facts={
            "user_name": "Frank",
        },
        user_message=user_message,
    )

    assert system_message == original_system_message


def test_compose_includes_source_and_page_for_retrieved_context() -> None:
    system_message = Message(
        role=MessageRole.SYSTEM,
        content="You are a helpful assistant.",
    )

    user_message = Message(
        role=MessageRole.USER,
        content="Explain the architecture.",
    )

    composer = PromptComposer()

    result = composer.compose(
        system_message=system_message,
        history_messages=[],
        facts={},
        user_message=user_message,
        retrieved_contexts=[
            RetrievedContext(
                content="The application layer uses FastAPI.",
                source="architecture.pdf",
                page=2,
            ),
        ],
    )

    assert result[0].content == (
        "You are a helpful assistant.\n\n"
        "Retrieved knowledge:\n"
        "When using the retrieved knowledge, cite the provided source "
        "in your answer. Use only the source and page information shown "
        "below. Do not invent source names or page numbers.\n"
        "Source: architecture.pdf (page 2)\n"
        "The application layer uses FastAPI."
    )


def test_compose_includes_source_without_page_for_retrieved_context() -> None:
    system_message = Message(
        role=MessageRole.SYSTEM,
        content="You are a helpful assistant.",
    )

    user_message = Message(
        role=MessageRole.USER,
        content="How do sessions expire?",
    )

    composer = PromptComposer()

    result = composer.compose(
        system_message=system_message,
        history_messages=[],
        facts={},
        user_message=user_message,
        retrieved_contexts=[
            RetrievedContext(
                content="Sessions use sliding expiration.",
                source="session.md",
            ),
        ],
    )

    assert result[0].content == (
        "You are a helpful assistant.\n\n"
        "Retrieved knowledge:\n"
        "When using the retrieved knowledge, cite the provided source "
        "in your answer. Use only the source and page information shown "
        "below. Do not invent source names or page numbers.\n"
        "Source: session.md\n"
        "Sessions use sliding expiration."
    )


def test_compose_includes_retrieved_context_without_source() -> None:
    system_message = Message(
        role=MessageRole.SYSTEM,
        content="You are a helpful assistant.",
    )

    user_message = Message(
        role=MessageRole.USER,
        content="Tell me about the system.",
    )

    composer = PromptComposer()

    result = composer.compose(
        system_message=system_message,
        history_messages=[],
        facts={},
        user_message=user_message,
        retrieved_contexts=[
            RetrievedContext(
                content="Some retrieved knowledge.",
            ),
        ],
    )

    assert result[0].content == (
        "You are a helpful assistant.\n\n"
        "Retrieved knowledge:\n"
        "Some retrieved knowledge."
    )
