from app.config_models.memory_config import MemoryConfig
from app.memory.sliding_window_memory import SlidingWindowMemory
from app.models.message import Message
from app.models.message_role import MessageRole


def create_memory(
    *,
    max_history_rounds: int = 2,
) -> SlidingWindowMemory:
    return SlidingWindowMemory(
        config=MemoryConfig(
            max_history_rounds=max_history_rounds,
        ),
    )


def create_turn(
    user_content: str,
    assistant_content: str,
) -> tuple[Message, Message]:
    return (
        Message(
            role=MessageRole.USER,
            content=user_content,
        ),
        Message(
            role=MessageRole.ASSISTANT,
            content=assistant_content,
        ),
    )


def test_add_turn_should_store_user_and_assistant_messages() -> None:
    memory = create_memory()

    user_message, assistant_message = create_turn(
        "Hello",
        "Hi",
    )

    memory.add_turn(
        user_message=user_message,
        assistant_message=assistant_message,
    )

    assert memory.get_messages() == (
        user_message,
        assistant_message,
    )


def test_should_keep_only_latest_rounds() -> None:
    memory = create_memory(
        max_history_rounds=2,
    )

    first_turn = create_turn(
        "Question 1",
        "Answer 1",
    )

    second_turn = create_turn(
        "Question 2",
        "Answer 2",
    )

    third_turn = create_turn(
        "Question 3",
        "Answer 3",
    )

    for user_message, assistant_message in (
        first_turn,
        second_turn,
        third_turn,
    ):
        memory.add_turn(
            user_message=user_message,
            assistant_message=assistant_message,
        )

    assert memory.get_messages() == (
        second_turn[0],
        second_turn[1],
        third_turn[0],
        third_turn[1],
    )


def test_clear_should_remove_all_messages() -> None:
    memory = create_memory()

    user_message, assistant_message = create_turn(
        "Hello",
        "Hi",
    )

    memory.add_turn(
        user_message=user_message,
        assistant_message=assistant_message,
    )

    memory.clear()

    assert memory.get_messages() == ()
