from enum import Enum


class TraceEventType(str, Enum):
    AGENT_STARTED = "agent_started"
    AGENT_FINISHED = "agent_finished"
    AGENT_FAILED = "agent_failed"

    LLM_STARTED = "llm_started"
    LLM_FINISHED = "llm_finished"
    LLM_FAILED = "llm_failed"

    TOOL_STARTED = "tool_started"
    TOOL_FINISHED = "tool_finished"
    TOOL_FAILED = "tool_failed"
