from collections.abc import Iterable

from app.agent.chat_agent import ChatAgent

DEFAULT_MESSAGES = (
    "How are you?",
    "What are you doing?",
    "Tell me something interesting.",
    "What is my name?",
)


def print_chat(
    agent: ChatAgent,
    message: str,
) -> None:
    print(f"\nYou: {message}")

    response = agent.chat(message)

    print(f"Agent: {response}")


def run_fact_memory_demo(
    agent: ChatAgent,
) -> None:
    print_chat(
        agent,
        "My name is Frank.",
    )

    print(f"Remembered user name: {agent.get_fact('user_name')}")

    print_chat(
        agent,
        "What is my name?",
    )


def run_conversation_demo(
    agent: ChatAgent,
    messages: Iterable[str] = DEFAULT_MESSAGES,
) -> None:
    for message in messages:
        print_chat(
            agent,
            message,
        )


def print_history(
    agent: ChatAgent,
) -> None:
    history = agent.get_history()

    print("\nConversation history:")

    for message in history:
        print(f"- {message.role.value}: {message.content}")

    print(f"Stored messages: {len(history)}")


def run_chat_demo(
    agent: ChatAgent,
) -> None:
    run_fact_memory_demo(agent)

    run_conversation_demo(agent)

    print_history(agent)

    agent.clear_history()

    print(f"\nStored messages after clear: {len(agent.get_history())}")
