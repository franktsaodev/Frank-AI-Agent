import os


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
