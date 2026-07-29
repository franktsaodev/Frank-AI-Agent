import pytest

from app.agent.chat_agent import ChatAgent
from app.config_models.prompt_config import PromptConfig
from app.extractors.regex_fact_extractor import RegexFactExtractor
from app.memory.in_memory_fact_memory import InMemoryFactMemory
from app.memory.sliding_window_memory import SlidingWindowMemory
from app.models.client_response import ClientResponse
from app.policies.simple_memory_policy import SimpleMemoryPolicy
from app.prompts.prompt_composer import PromptComposer
from app.prompts.prompt_template import PromptTemplate
from app.tools.tool_call import ToolCall
from tests.fakes.fake_client import FakeClient
from tests.fakes.fake_tool_executor import FakeToolExecutor


@pytest.fixture
def create_agent():
    def _create_agent(
        client_response: ClientResponse,
        tool_executor: FakeToolExecutor,
    ) -> ChatAgent:
        return ChatAgent(
            prompt_template=PromptTemplate(
                config=PromptConfig(
                    prompt_name="system_prompt.txt",
                    user_name="Frank",
                    language="Traditional Chinese",
                ),
            ),
            client=FakeClient(
                response=client_response,
            ),
            tool_executor=tool_executor,
            memory=SlidingWindowMemory(
                max_rounds=10,
            ),
            fact_memory=InMemoryFactMemory(),
            fact_extractor=RegexFactExtractor(),
            memory_policy=SimpleMemoryPolicy(),
            prompt_composer=PromptComposer(),
        )

    return _create_agent


def test_chat_executes_tool_calls_returned_by_client(
    create_agent,
) -> None:
    tool_call = ToolCall(
        call_id="call_123",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    tool_executor = FakeToolExecutor(
        result=3,
    )

    agent = create_agent(
        client_response=ClientResponse(
            tool_calls=(tool_call,),
        ),
        tool_executor=tool_executor,
    )

    result = agent.chat("What is 1 + 2?")

    assert tool_executor.received_tool_calls == [
        tool_call,
    ]

    assert result == "3"


def test_chat_executes_all_tool_calls_returned_by_client(
    create_agent,
) -> None:
    first_call = ToolCall(
        call_id="call_1",
        name="calculator",
        arguments={
            "expression": "1 + 2",
        },
    )

    second_call = ToolCall(
        call_id="call_2",
        name="calculator",
        arguments={
            "expression": "3 + 4",
        },
    )

    tool_executor = FakeToolExecutor(
        result=7,
    )

    agent = create_agent(
        client_response=ClientResponse(
            tool_calls=(
                first_call,
                second_call,
            ),
        ),
        tool_executor=tool_executor,
    )

    agent.chat("Calculate these.")

    assert tool_executor.received_tool_calls == [
        first_call,
        second_call,
    ]
