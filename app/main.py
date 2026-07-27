from app.agent.chat_agent import ChatAgent
from app.bootstrap import create_chat_agent
from app.core.logging_config import configure_logging
from app.exceptions.client_exceptions import (
    AIClientError,
    ClientAuthenticationError,
    ClientConnectionError,
    ClientTimeoutError,
)


def run_demo(agent: ChatAgent) -> None:
    print(agent.chat("My name is Frank."))
    print(agent.get_fact("user_name"))
    print(agent.chat("What is my name?"))

    messages = [
        "How are you?",
        "What are you doing?",
        "Tell me something interesting.",
        "What is my name?",
    ]

    for message in messages:
        response = agent.chat(message)
        print(response)

    print(agent.memory.get_messages())
    print(len(agent.memory.get_messages()))

    agent.memory.clear()
    print(agent.memory.get_messages())


def main() -> None:
    configure_logging()

    try:
        agent = create_chat_agent()
        run_demo(agent)
    except ClientAuthenticationError:
        print("Authentication failed. Please check the API configuration.")
    except ClientTimeoutError:
        print("The AI service took too long to respond.")
    except ClientConnectionError:
        print("Unable to connect to the AI service.")
    except AIClientError as error:
        print(f"AI service error: {error}")


if __name__ == "__main__":
    main()
