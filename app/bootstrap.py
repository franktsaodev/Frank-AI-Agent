from app.agent.chat_agent import ChatAgent
from app.clients.groq_client import GroqClient
from app.config import GROQ_API_KEY, GROQ_MODEL
from app.config_models.groq_config import GroqConfig
from app.config_models.memory_config import MemoryConfig
from app.config_models.prompt_config import PromptConfig
from app.config_models.retry_config import RetryConfig
from app.extractors.regex_fact_extractor import RegexFactExtractor
from app.memory.in_memory_fact_memory import InMemoryFactMemory
from app.memory.sliding_window_memory import SlidingWindowMemory
from app.policies.simple_memory_policy import SimpleMemoryPolicy
from app.prompts.prompt_composer import PromptComposer
from app.prompts.prompt_template import PromptTemplate


def create_chat_agent() -> ChatAgent:
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
    )

    prompt_config = PromptConfig(
        prompt_name="system_prompt.txt",
        user_name="Frank",
        language="Traditional Chinese",
    )

    prompt_template = PromptTemplate(
        config=prompt_config,
    )

    memory_config = MemoryConfig(
        max_history_rounds=2,
    )

    memory = SlidingWindowMemory(
        max_rounds=memory_config.max_history_rounds,
    )

    fact_memory = InMemoryFactMemory()

    fact_extractor = RegexFactExtractor()

    memory_policy = SimpleMemoryPolicy()

    prompt_composer = PromptComposer()

    return ChatAgent(
        prompt_template=prompt_template,
        client=client,
        memory=memory,
        fact_memory=fact_memory,
        fact_extractor=fact_extractor,
        memory_policy=memory_policy,
        prompt_composer=prompt_composer,
    )
