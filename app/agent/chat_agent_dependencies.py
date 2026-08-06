from dataclasses import dataclass

from app.agent.agent_runner_protocol import (
    AgentRunnerProtocol,
)
from app.config_models.memory_config import MemoryConfig
from app.extractors.base_fact_extractor import (
    BaseFactExtractor,
)
from app.policies.base_memory_policy import (
    BaseMemoryPolicy,
)
from app.prompts.base_prompt_template import (
    BasePromptTemplate,
)
from app.prompts.prompt_composer_protocol import (
    PromptComposerProtocol,
)


@dataclass(frozen=True)
class ChatAgentDependencies:
    prompt_template: BasePromptTemplate
    agent_runner: AgentRunnerProtocol
    memory_config: MemoryConfig
    fact_extractor: BaseFactExtractor
    memory_policy: BaseMemoryPolicy
    prompt_composer: PromptComposerProtocol
