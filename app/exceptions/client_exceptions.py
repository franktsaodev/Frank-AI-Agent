class AIClientError(Exception):
    """Base exception for AI client errors."""


class ClientAuthenticationError(AIClientError):
    """Raised when AI client authentication fails."""


class ClientConnectionError(AIClientError):
    """Raised when the AI service cannot be reached."""


class ClientTimeoutError(AIClientError):
    """Raised when an AI client request times out."""


class ClientRateLimitError(Exception):
    """Raised when the AI service rate limit remains exceeded."""


class ClientInvalidResponseError(AIClientError):
    """Raised when the AI service repeatedly returns invalid content."""
