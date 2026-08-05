from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def load_environment() -> None:
    load_dotenv(
        dotenv_path=ENV_FILE,
    )
