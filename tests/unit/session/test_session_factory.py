from app.session.session_factory import (
    SessionFactory,
)


def test_create_should_generate_session_id() -> None:
    factory = SessionFactory()

    session = factory.create()

    assert session.value
