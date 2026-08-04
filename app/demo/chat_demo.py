from collections.abc import Iterable, Mapping

from app.agent.chat_agent import ChatAgent
from app.types.json_types import JsonValue

DEFAULT_MESSAGES = (
    "My name is Frank.",
    "What is my name?",
    "What is 125 * 8?",
)


def print_chat(
    agent: ChatAgent,
    message: str,
    *,
    metadata: Mapping[str, JsonValue] | None = None,
) -> None:
    print(f"\nYou: {message}")

    response = agent.chat(
        message,
        metadata=metadata,
    )

    print(f"Agent: {response}")


def run_fact_memory_demo(
    agent: ChatAgent,
) -> None:
    print_chat(
        agent,
        "My name is Frank.",
        metadata={
            "source": "fact_memory_demo",
            "user_id": "frank",
            "request_id": "fact-demo-1",
        },
    )

    print(f"Remembered user name: {agent.get_fact('user_name')}")

    print_chat(
        agent,
        "What is my name?",
        metadata={
            "source": "fact_memory_demo",
            "user_id": "frank",
            "request_id": "fact-demo-2",
        },
    )


def run_conversation_demo(
    agent: ChatAgent,
    messages: Iterable[str] = DEFAULT_MESSAGES,
) -> None:
    for index, message in enumerate(
        messages,
        start=1,
    ):
        print_chat(
            agent,
            message,
            metadata={
                "source": "conversation_demo",
                "user_id": "frank",
                "request_id": f"conversation-demo-{index}",
            },
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
