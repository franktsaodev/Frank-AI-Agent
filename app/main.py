from app.bootstrap import create_chat_agent
from app.config import load_environment
from app.config_loaders.environment_reader import EnvironmentReader
from app.config_loaders.logging_config_loader import LoggingConfigLoader
from app.core.logging_config import configure_logging
from app.demo.chat_demo import run_chat_demo
from app.exceptions.client_exceptions import (
    AIClientError,
    ClientAuthenticationError,
    ClientConnectionError,
    ClientTimeoutError,
)


def main() -> None:
    load_environment()

    environment_reader = EnvironmentReader()

    logging_config = LoggingConfigLoader(
        environment_reader=environment_reader,
    ).load()

    configure_logging(
        config=logging_config,
    )

    try:
        agent = create_chat_agent()
        run_chat_demo(agent)
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
