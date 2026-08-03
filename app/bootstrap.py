import logging
from pathlib import Path

from app.agent.agent_runner import AgentRunner
from app.agent.chat_agent import ChatAgent
from app.clients.base_client import BaseClient
from app.clients.groq_client import GroqClient
from app.clock.base_clock import BaseClock
from app.clock.system_clock import SystemClock
from app.config import GROQ_API_KEY, GROQ_MODEL
from app.config_models.agent_config import AgentConfig
from app.config_models.groq_config import GroqConfig
from app.config_models.memory_config import MemoryConfig
from app.config_models.memory_policy_config import MemoryPolicyConfig
from app.config_models.prompt_config import PromptConfig
from app.config_models.retry_config import RetryConfig
from app.config_models.tracing_config import TracingConfig
from app.extractors.regex_fact_extractor import RegexFactExtractor
from app.memory.in_memory_fact_memory import InMemoryFactMemory
from app.memory.sliding_window_memory import SlidingWindowMemory
from app.policies.simple_memory_policy import SimpleMemoryPolicy
from app.prompts.prompt_composer import PromptComposer
from app.prompts.prompt_template import PromptTemplate
from app.tools.plugins.core_tool_plugin import CoreToolPlugin
from app.tools.plugins.tool_plugin_loader import ToolPluginLoader
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_provider import ToolProvider
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_schema_adapter import ToolSchemaAdapter
from app.tracing.base_tracer import BaseTracer
from app.tracing.exporter_tracer import ExporterTracer
from app.tracing.trace_exporter_factory import TraceExporterFactory

logger = logging.getLogger(__name__)


def create_chat_agent() -> ChatAgent:
    clock = SystemClock()
    tracer = _create_tracer()

    registry = ToolRegistry()

    _load_tool_plugins(
        registry=registry,
    )

    tool_provider = _create_tool_provider(
        registry=registry,
    )

    tool_executor = _create_tool_executor(
        registry=registry,
        tracer=tracer,
        clock=clock,
    )

    client = _create_groq_client(
        tool_provider=tool_provider,
        tracer=tracer,
        clock=clock,
    )

    agent_runner = _create_agent_runner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
        clock=clock,
    )

    return ChatAgent(
        prompt_template=_create_prompt_template(),
        agent_runner=agent_runner,
        memory=_create_memory(),
        fact_memory=InMemoryFactMemory(),
        fact_extractor=RegexFactExtractor(),
        memory_policy=_create_memory_policy(),
        prompt_composer=PromptComposer(),
    )


def _create_tracer() -> BaseTracer:
    tracing_config = TracingConfig(
        enable_logging=True,
        json_file_path=Path(
            "logs/traces.jsonl",
        ),
    )

    trace_exporter = TraceExporterFactory().create(
        config=tracing_config,
    )

    return ExporterTracer(
        exporter=trace_exporter,
    )


def _create_tool_provider(
    registry: ToolRegistry,
) -> ToolProvider:
    return ToolProvider(
        registry=registry,
        adapter=ToolSchemaAdapter(),
    )


def _create_tool_executor(
    registry: ToolRegistry,
    tracer: BaseTracer,
    clock: BaseClock,
) -> ToolExecutor:
    return ToolExecutor(
        registry=registry,
        tracer=tracer,
        clock=clock,
    )


def _create_groq_client(
    tool_provider: ToolProvider,
    tracer: BaseTracer,
    clock: BaseClock,
) -> GroqClient:
    return GroqClient(
        groq_config=GroqConfig(
            api_key=GROQ_API_KEY,
            model=GROQ_MODEL,
        ),
        retry_config=RetryConfig(
            max_attempts=3,
            initial_delay_seconds=1,
            backoff_multiplier=2.0,
        ),
        tool_provider=tool_provider,
        tracer=tracer,
        clock=clock,
    )


def _create_agent_runner(
    client: BaseClient,
    tool_executor: ToolExecutor,
    tracer: BaseTracer,
    clock: BaseClock,
) -> AgentRunner:
    return AgentRunner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
        clock=clock,
        config=AgentConfig(
            max_iterations=10,
        ),
    )


def _create_prompt_template() -> PromptTemplate:
    return PromptTemplate(
        config=PromptConfig(
            prompt_name="system_prompt.txt",
            user_name="Frank",
            language="Traditional Chinese",
        ),
    )


def _create_memory() -> SlidingWindowMemory:
    return SlidingWindowMemory(
        config=MemoryConfig(
            max_history_rounds=2,
        ),
    )


def _create_memory_policy() -> SimpleMemoryPolicy:
    return SimpleMemoryPolicy(
        config=MemoryPolicyConfig(
            allowed_keys=frozenset(
                {
                    "user_name",
                    "favorite_music",
                    "occupation",
                }
            ),
        ),
    )


def _load_tool_plugins(
    registry: ToolRegistry,
) -> None:
    loader = ToolPluginLoader(
        registry=registry,
    )

    result = loader.load(
        plugins=(CoreToolPlugin(),),
    )

    tool_names = ", ".join(result.tool_names) if result.tool_names else "none"

    logger.info(
        "Loaded %d tool plugin(s) with %d tool(s): %s",
        result.plugin_count,
        result.tool_count,
        tool_names,
    )
