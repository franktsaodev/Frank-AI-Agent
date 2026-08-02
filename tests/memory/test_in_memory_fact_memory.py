from app.memory.in_memory_fact_memory import InMemoryFactMemory


def test_set_and_get_fact() -> None:
    memory = InMemoryFactMemory()

    memory.set("user_name", "Frank")

    assert memory.get("user_name") == "Frank"


def test_get_returns_none_when_fact_does_not_exist() -> None:
    memory = InMemoryFactMemory()

    result = memory.get("user_name")

    assert result is None


def test_set_updates_existing_fact() -> None:
    memory = InMemoryFactMemory()

    memory.set("location", "Taipei")
    memory.set("location", "Hai Phong")

    assert memory.get("location") == "Hai Phong"


def test_get_all_returns_all_facts() -> None:
    memory = InMemoryFactMemory()

    memory.set("user_name", "Frank")
    memory.set("location", "Hai Phong")

    assert memory.get_all() == {
        "user_name": "Frank",
        "location": "Hai Phong",
    }


def test_get_all_returns_copy() -> None:
    memory = InMemoryFactMemory()
    memory.set("user_name", "Frank")

    facts = memory.get_all()
    facts["user_name"] = "John"

    assert memory.get("user_name") == "Frank"


def test_delete_removes_fact() -> None:
    memory = InMemoryFactMemory()
    memory.set("user_name", "Frank")

    memory.delete("user_name")

    assert memory.get("user_name") is None


def test_delete_missing_fact_does_not_raise_error() -> None:
    memory = InMemoryFactMemory()

    memory.delete("missing_key")

    assert memory.get_all() == {}


def test_clear_removes_all_facts() -> None:
    memory = InMemoryFactMemory()

    memory.set("user_name", "Frank")
    memory.set("location", "Hai Phong")

    memory.clear()

    assert memory.get_all() == {}
