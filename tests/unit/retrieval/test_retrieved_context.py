from app.models.message import Message
from app.models.message_role import MessageRole
from app.prompts.prompt_composer import PromptComposer
from app.retrieval.retrieved_context import RetrievedContext


def test_should_store_content_and_source() -> None:
    context = RetrievedContext(
        content="Session TTL is 3600 seconds.",
        source="README.md",
    )

    assert context.content == "Session TTL is 3600 seconds."
    assert context.source == "README.md"


def test_should_include_retrieved_contexts_in_prompt() -> None:
    composer = PromptComposer()

    messages = composer.compose(
        system_message=Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant.",
        ),
        history_messages=[],
        facts={},
        retrieved_contexts=[
            RetrievedContext(
                content="Session TTL is 3600 seconds.",
                source="README.md",
            ),
            RetrievedContext(
                content="Sessions use sliding expiration.",
                source="architecture.md",
            ),
        ],
        user_message=Message(
            role=MessageRole.USER,
            content="How do sessions expire?",
        ),
    )

    system_message = messages[0]

    assert system_message.content is not None
    assert "Retrieved knowledge:" in system_message.content
    assert "Source: README.md" in system_message.content
    assert "Session TTL is 3600 seconds." in system_message.content
    assert "Source: architecture.md" in system_message.content
    assert "Sessions use sliding expiration." in system_message.content


def test_should_omit_retrieved_section_when_context_is_empty() -> None:
    composer = PromptComposer()

    messages = composer.compose(
        system_message=Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant.",
        ),
        history_messages=[],
        facts={},
        retrieved_contexts=[],
        user_message=Message(
            role=MessageRole.USER,
            content="Hello",
        ),
    )

    system_message = messages[0]

    assert system_message.content is not None
    assert "Retrieved knowledge:" not in system_message.content


def test_should_include_context_without_source() -> None:
    composer = PromptComposer()

    messages = composer.compose(
        system_message=Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant.",
        ),
        history_messages=[],
        facts={},
        retrieved_contexts=[
            RetrievedContext(
                content="Session TTL is 3600 seconds.",
            )
        ],
        user_message=Message(
            role=MessageRole.USER,
            content="What is the session TTL?",
        ),
    )

    system_message = messages[0]

    assert system_message.content is not None
    assert "Retrieved knowledge:" in system_message.content
    assert "Session TTL is 3600 seconds." in system_message.content
    assert "Source: None" not in system_message.content
