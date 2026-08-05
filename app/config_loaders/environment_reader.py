import os


class EnvironmentReader:
    def get_required(
        self,
        name: str,
    ) -> str:
        value = os.getenv(name)

        if value is None or not value.strip():
            raise RuntimeError(f"Required environment variable is missing: {name}")

        return value

    def get_str(
        self,
        *,
        name: str,
        default: str,
    ) -> str:
        value = os.getenv(name)

        if value is None or not value.strip():
            return default

        return value

    def get_int(
        self,
        *,
        name: str,
        default: int,
    ) -> int:
        value = os.getenv(name)

        if value is None or not value.strip():
            return default

        try:
            return int(value)
        except ValueError as error:
            raise RuntimeError(
                f"Environment variable {name} must be an integer."
            ) from error

    def get_float(
        self,
        *,
        name: str,
        default: float,
    ) -> float:
        value = os.getenv(name)

        if value is None or not value.strip():
            return default

        try:
            return float(value)
        except ValueError as error:
            raise RuntimeError(
                f"Environment variable {name} must be a number."
            ) from error

    def get_bool(
        self,
        *,
        name: str,
        default: bool,
    ) -> bool:
        value = os.getenv(name)

        if value is None or not value.strip():
            return default

        normalized_value = value.strip().lower()

        if normalized_value in {
            "true",
            "1",
            "yes",
            "on",
        }:
            return True

        if normalized_value in {
            "false",
            "0",
            "no",
            "off",
        }:
            return False

        raise RuntimeError(f"Environment variable {name} must be a boolean.")
