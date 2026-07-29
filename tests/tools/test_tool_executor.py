import pytest

from app.tools.tool_call import ToolCall
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_registry import ToolRegistry
from tests.fakes.failing_tool import FailingTool
from tests.fakes.fake_tool import FakeTool


def test_execute_calls_tool_with_arguments() -> None:
    registry = ToolRegistry()
    fake_tool = FakeTool()
    registry.register(fake_tool)
    executor = ToolExecutor(registry)

    tool_call = ToolCall(
        call_id="",
        name="fake",
        arguments={
            "message": "hello",
            "count": 3,
        },
    )

    result = executor.execute(tool_call)

    assert result == "fake result"
    assert fake_tool.received_arguments == {
        "message": "hello",
        "count": 3,
    }


def test_execute_raises_error_when_tool_does_not_exist() -> None:
    registry = ToolRegistry()
    executor = ToolExecutor(registry)

    with pytest.raises(
        KeyError,
        match="Tool not found: weather",
    ):
        executor.execute(
            ToolCall(
                call_id="",
                name="weather",
                arguments={},
            )
        )


def test_execute_propagates_tool_error() -> None:
    registry = ToolRegistry()
    registry.register(FailingTool())
    executor = ToolExecutor(registry)

    with pytest.raises(
        RuntimeError,
        match="Tool execution failed",
    ):
        executor.execute(
            ToolCall(
                call_id="",
                name="failing",
                arguments={},
            )
        )
