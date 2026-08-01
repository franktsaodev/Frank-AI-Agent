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