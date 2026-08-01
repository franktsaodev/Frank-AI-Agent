from app.clock.system_clock import SystemClock


def test_now_should_return_monotonic_time() -> None:
    clock = SystemClock()

    first_time = clock.now()
    second_time = clock.now()

    assert isinstance(first_time, float)
    assert second_time >= first_time