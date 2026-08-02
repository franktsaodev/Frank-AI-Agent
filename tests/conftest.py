from unittest.mock import MagicMock

import pytest

from app.tools.tool_registry import ToolRegistry
from app.tracing.base_tracer import BaseTracer
from app.tracing.trace_context import TraceContext


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
