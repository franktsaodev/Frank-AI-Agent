from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.config_models.session_config import SessionConfig
from app.tools.tool_registry import ToolRegistry
from app.tracing.base_tracer import BaseTracer
from app.tracing.trace_context import TraceContext
from tests.fakes.fake_session_clock import FakeSessionClock


@pytest.fixture
def tracer() -> MagicMock:
    return MagicMock(spec=BaseTracer)


@pytest.fixture
def registry() -> ToolRegistry:
    return ToolRegistry()


@pytest.fixture
def trace_context() -> TraceContext:
    return TraceContext(
        trace_id="test-trace-id",
        span_id="agent-span-id",
    )


@pytest.fixture
def session_timestamp() -> datetime:
    return datetime(
        2026,
        8,
        6,
        3,
        0,
        tzinfo=UTC,
    )


@pytest.fixture
def session_clock(
    session_timestamp: datetime,
) -> FakeSessionClock:
    return FakeSessionClock(
        current_time=session_timestamp,
    )


@pytest.fixture
def session_config() -> SessionConfig:
    return SessionConfig(
        ttl_seconds=3600,
        cleanup_interval_seconds=300,
    )
