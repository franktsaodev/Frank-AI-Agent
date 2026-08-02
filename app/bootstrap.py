from pathlib import Path

from app.agent.agent_runner import AgentRunner
from app.agent.chat_agent import ChatAgent
from app.clients.groq_client import GroqClient
from app.clock.system_clock import SystemClock
from app.config import GROQ_API_KEY, GROQ_MODEL
from app.config_models.agent_config import AgentConfig
from app.config_models.groq_config import GroqConfig
from app.config_models.memory_config import MemoryConfig
from app.config_models.memory_policy_config import (
    MemoryPolicyConfig,
)
from app.config_models.prompt_config import PromptConfig
from app.config_models.retry_config import RetryConfig
from app.config_models.tracing_config import TracingConfig
from app.extractors.regex_fact_extractor import RegexFactExtractor
from app.memory.in_memory_fact_memory import InMemoryFactMemory
from app.memory.sliding_window_memory import SlidingWindowMemory
from app.policies.simple_memory_policy import SimpleMemoryPolicy
from app.prompts.prompt_composer import PromptComposer
from app.prompts.prompt_template import PromptTemplate
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_provider import ToolProvider
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_schema_adapter import ToolSchemaAdapter
from app.tracing.exporter_tracer import ExporterTracer
from app.tracing.trace_exporter_factory import TraceExporterFactory


def create_chat_agent() -> ChatAgent:
    clock = SystemClock()

    tracing_config = TracingConfig(
        enable_logging=True,
        json_file_path=Path(
            "logs/traces.jsonl",
        ),
    )

    trace_exporter = TraceExporterFactory().create(
        config=tracing_config,
    )

    tracer = ExporterTracer(
        exporter=trace_exporter,
    )

    registry = ToolRegistry()

    tool_provider = ToolProvider(
        registry=registry,
        adapter=ToolSchemaAdapter(),
    )

    tool_executor = ToolExecutor(
        registry=registry,
        tracer=tracer,
        clock=clock,
    )

    groq_config = GroqConfig(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
    )

    retry_config = RetryConfig(
        max_attempts=3,
        initial_delay_seconds=1,
        backoff_multiplier=2.0,
    )

    client = GroqClient(
        groq_config=groq_config,
        retry_config=retry_config,
        tool_provider=tool_provider,
        tracer=tracer,
        clock=clock,
    )

    agent_config = AgentConfig(
        max_iterations=10,
    )

    agent_runner = AgentRunner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
        clock=clock,
        config=agent_config,
    )

    prompt_template = PromptTemplate(
        config=PromptConfig(
            prompt_name="system_prompt.txt",
            user_name="Frank",
            language="Traditional Chinese",
        ),
    )

    memory_config = MemoryConfig(
        max_history_rounds=2,
    )

    memory = SlidingWindowMemory(
        config=memory_config,
    )

    memory_policy_config = MemoryPolicyConfig(
        allowed_keys=frozenset(
            {
                "user_name",
                "favorite_music",
                "occupation",
            }
        ),
    )

    return ChatAgent(
        prompt_template=prompt_template,
        agent_runner=agent_runner,
        memory=memory,
        fact_memory=InMemoryFactMemory(),
        fact_extractor=RegexFactExtractor(),
        memory_policy=SimpleMemoryPolicy(
            config=memory_policy_config,
        ),
        prompt_composer=PromptComposer(),
    )
