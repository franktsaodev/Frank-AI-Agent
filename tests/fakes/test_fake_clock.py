import pytest

from tests.fakes.fake_clock import FakeClock


def test_now_should_return_configured_times_in_order() -> None:
    clock = FakeClock(
        times=[
            10.0,
            10.25,
        ],
    )

    assert clock.now() == 10.0
    assert clock.now() == 10.25


def test_init_should_reject_empty_times() -> None:
    with pytest.raises(
        ValueError,
        match="FakeClock requires at least one time value",
    ):
        FakeClock(
            times=[],
        )


def test_now_should_raise_when_no_times_remain() -> None:
    clock = FakeClock(
        times=[
            10.0,
        ],
    )

    assert clock.now() == 10.0

    with pytest.raises(
        RuntimeError,
        match="FakeClock has no more configured time values",
    ):
        clock.now()


def test_for_duration_should_create_two_time_values() -> None:
    clock = FakeClock.for_duration(
        0.25,
        start_time=10.0,
    )

    assert clock.now() == 10.0
    assert clock.now() == 10.25


def test_for_duration_should_use_zero_as_default_start_time() -> None:
    clock = FakeClock.for_duration(
        1.5,
    )

    assert clock.now() == 0.0
    assert clock.now() == 1.5


def test_for_duration_should_reject_negative_duration() -> None:
    with pytest.raises(
        ValueError,
        match="duration_seconds cannot be negative",
    ):
        FakeClock.for_duration(
            -1.0,
        )