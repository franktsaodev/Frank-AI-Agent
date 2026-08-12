import logging

from app.agent.agent_runner import AgentRunner
from app.agent.chat_agent import ChatAgent
from app.agent.chat_agent_dependencies import (
    ChatAgentDependencies,
)
from app.agent.chat_agent_factory import ChatAgentFactory
from app.clients.base_client import BaseClient
from app.clients.groq_client import GroqClient
from app.clock.base_clock import BaseClock
from app.clock.system_clock import SystemClock
from app.config import load_environment
from app.config_loaders.agent_config_loader import (
    AgentConfigLoader,
)
from app.config_loaders.environment_reader import EnvironmentReader
from app.config_loaders.groq_config_loader import (
    GroqConfigLoader,
)
from app.config_loaders.memory_config_loader import (
    MemoryConfigLoader,
)
from app.config_loaders.memory_policy_config_loader import (
    MemoryPolicyConfigLoader,
)
from app.config_loaders.prompt_config_loader import (
    PromptConfigLoader,
)
from app.config_loaders.retrieval_config_loader import RetrievalConfigLoader
from app.config_loaders.retry_config_loader import (
    RetryConfigLoader,
)
from app.config_loaders.tool_plugin_config_loader import (
    ToolPluginConfigLoader,
)
from app.config_loaders.tracing_config_loader import (
    TracingConfigLoader,
)
from app.config_models.agent_config import AgentConfig
from app.config_models.groq_config import GroqConfig
from app.config_models.memory_config import MemoryConfig
from app.config_models.memory_policy_config import MemoryPolicyConfig
from app.config_models.prompt_config import PromptConfig
from app.config_models.retry_config import RetryConfig
from app.config_models.tool_plugin_config import ToolPluginConfig
from app.config_models.tracing_config import TracingConfig
from app.extractors.regex_fact_extractor import RegexFactExtractor
from app.memory.sliding_window_memory import SlidingWindowMemory
from app.policies.simple_memory_policy import SimpleMemoryPolicy
from app.prompts.prompt_composer import PromptComposer
from app.prompts.prompt_template import PromptTemplate
from app.retrieval.retrieval_runtime_factory import RetrievalRuntimeFactory
from app.tools.plugins.tool_plugin_factory import ToolPluginFactory
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
    return create_chat_agent_factory().create()


def create_chat_agent_factory() -> ChatAgentFactory:
    load_environment()

    environment_reader = EnvironmentReader()

    tracing_config = TracingConfigLoader().load()
    tool_plugin_config = ToolPluginConfigLoader().load()
    groq_config = GroqConfigLoader().load()
    retry_config = RetryConfigLoader().load()
    agent_config = AgentConfigLoader().load()
    memory_config = MemoryConfigLoader().load()
    memory_policy_config = MemoryPolicyConfigLoader().load()
    prompt_config = PromptConfigLoader().load()
    retrieval_config = RetrievalConfigLoader(
        environment_reader=environment_reader,
    ).load()

    clock = SystemClock()

    tracer = _create_tracer(
        config=tracing_config,
    )

    registry = ToolRegistry()

    _load_tool_plugins(
        registry=registry,
        config=tool_plugin_config,
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
        groq_config=groq_config,
        retry_config=retry_config,
        tool_provider=tool_provider,
        tracer=tracer,
        clock=clock,
    )

    agent_runner = _create_agent_runner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
        clock=clock,
        agent_config=agent_config,
    )

    memory_policy = _create_memory_policy(
        config=memory_policy_config,
    )

    prompt_template = _create_prompt_template(
        config=prompt_config,
    )

    retrieval_runtime = RetrievalRuntimeFactory().create(
        retrieval_config,
    )

    dependencies = ChatAgentDependencies(
        prompt_template=prompt_template,
        agent_runner=agent_runner,
        memory_config=memory_config,
        fact_extractor=RegexFactExtractor(),
        memory_policy=memory_policy,
        prompt_composer=PromptComposer(),
        retriever=retrieval_runtime.retriever,
        retrieval_policy=retrieval_runtime.retrieval_policy,
    )

    return ChatAgentFactory(
        dependencies=dependencies,
    )


def _create_tracer(
    config: TracingConfig,
) -> BaseTracer:
    trace_exporter = TraceExporterFactory().create(
        config=config,
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
    groq_config: GroqConfig,
    retry_config: RetryConfig,
    tool_provider: ToolProvider,
    tracer: BaseTracer,
    clock: BaseClock,
) -> GroqClient:
    return GroqClient(
        groq_config=groq_config,
        retry_config=retry_config,
        tool_provider=tool_provider,
        tracer=tracer,
        clock=clock,
    )


def _create_agent_runner(
    client: BaseClient,
    tool_executor: ToolExecutor,
    tracer: BaseTracer,
    clock: BaseClock,
    agent_config: AgentConfig,
) -> AgentRunner:
    return AgentRunner(
        client=client,
        tool_executor=tool_executor,
        tracer=tracer,
        clock=clock,
        config=agent_config,
    )


def _create_prompt_template(
    config: PromptConfig,
) -> PromptTemplate:
    return PromptTemplate(
        config=config,
    )


def _create_memory(
    config: MemoryConfig,
) -> SlidingWindowMemory:
    return SlidingWindowMemory(
        config=config,
    )


def _create_memory_policy(
    config: MemoryPolicyConfig,
) -> SimpleMemoryPolicy:
    return SimpleMemoryPolicy(
        config=config,
    )


def _load_tool_plugins(
    registry: ToolRegistry,
    config: ToolPluginConfig,
) -> None:
    plugins = ToolPluginFactory().create_all(
        config.enabled_plugins,
    )

    result = ToolPluginLoader(
        registry=registry,
    ).load(
        plugins=plugins,
    )

    tool_names = ", ".join(result.tool_names) if result.tool_names else "none"

    logger.info(
        "Loaded %d tool plugin(s) with %d tool(s): %s",
        result.plugin_count,
        result.tool_count,
        tool_names,
    )
