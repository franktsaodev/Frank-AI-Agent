from app.models.client_response import ClientResponse
from app.tools.tool_call import ToolCall


def test_text_response_has_no_tool_calls() -> None:
    response = ClientResponse(
        content="你好",
    )

    assert response.content == "你好"
    assert response.tool_calls == ()
    assert response.has_tool_calls is False


def test_response_reports_when_tool_calls_exist() -> None:
    tool_call = ToolCall(
        call_id="",
        name="calculator",
        arguments={
            "expression": "2 + 3",
        },
    )

    response = ClientResponse(
        tool_calls=(tool_call,),
    )

    assert response.content is None
    assert response.tool_calls == (tool_call,)
    assert response.has_tool_calls is True
