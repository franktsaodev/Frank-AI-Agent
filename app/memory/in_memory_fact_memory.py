from app.memory.base_fact_memory import BaseFactMemory


class InMemoryFactMemory(BaseFactMemory):
    def __init__(self) -> None:
        self._facts: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        self._facts[key] = value

    def get(self, key: str) -> str | None:
        return self._facts.get(key)

    def get_all(self) -> dict[str, str]:
        return self._facts.copy()

    def delete(self, key: str) -> None:
        self._facts.pop(key, None)

    def clear(self) -> None:
        self._facts.clear()
