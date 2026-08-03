import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(
    dotenv_path=ENV_FILE,
)


def get_required_env(
    name: str,
) -> str:
    value = os.getenv(name)

    if value is None or not value.strip():
        raise RuntimeError(f"Required environment variable is missing: {name}")

    return value


GROQ_API_KEY: str = get_required_env(
    "GROQ_API_KEY",
)

GROQ_MODEL: str = get_required_env(
    "GROQ_MODEL",
)
