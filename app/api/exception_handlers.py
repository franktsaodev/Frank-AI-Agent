import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

from app.exceptions.client_exceptions import (
    AIClientError,
    ClientAuthenticationError,
    ClientConnectionError,
    ClientRateLimitError,
    ClientTimeoutError,
)
from app.session.session_expired_error import (
    SessionExpiredError,
)
from app.session.session_not_found_error import (
    SessionNotFoundError,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(
    app: FastAPI,
) -> None:
    @app.exception_handler(ClientAuthenticationError)
    async def handle_client_authentication_error(
        request: Request,
        error: ClientAuthenticationError,
    ) -> JSONResponse:
        del request

        logger.warning(
            "AI client authentication failed: %s",
            error,
        )

        return JSONResponse(
            status_code=502,
            content={
                "error": "client_authentication_error",
                "message": ("The AI service authentication failed."),
            },
        )

    @app.exception_handler(ClientTimeoutError)
    async def handle_client_timeout_error(
        request: Request,
        error: ClientTimeoutError,
    ) -> JSONResponse:
        del request

        logger.warning(
            "AI client request timed out: %s",
            error,
        )

        return JSONResponse(
            status_code=504,
            content={
                "error": "client_timeout",
                "message": ("The AI service took too long to respond."),
            },
        )

    @app.exception_handler(ClientConnectionError)
    async def handle_client_connection_error(
        request: Request,
        error: ClientConnectionError,
    ) -> JSONResponse:
        del request

        logger.warning(
            "AI client connection failed: %s",
            error,
        )

        return JSONResponse(
            status_code=503,
            content={
                "error": "client_connection_error",
                "message": ("Unable to connect to the AI service."),
            },
        )

    @app.exception_handler(ClientRateLimitError)
    async def handle_client_rate_limit_error(
        request: Request,
        error: ClientRateLimitError,
    ) -> JSONResponse:
        del request

        logger.warning(
            "AI client rate limit exceeded: %s",
            error,
        )

        return JSONResponse(
            status_code=503,
            content={
                "error": "client_rate_limit",
                "message": (
                    "The AI service is temporarily rate limited. "
                    "Please try again later."
                ),
            },
        )

    @app.exception_handler(AIClientError)
    async def handle_ai_client_error(
        request: Request,
        error: AIClientError,
    ) -> JSONResponse:
        del request

        logger.error(
            "Unexpected AI client error: %s",
            error,
        )

        return JSONResponse(
            status_code=502,
            content={
                "error": "ai_client_error",
                "message": ("The AI service returned an error."),
            },
        )

    @app.exception_handler(SessionNotFoundError)
    async def handle_session_not_found_error(
        request: Request,
        error: SessionNotFoundError,
    ) -> JSONResponse:
        del request

        logger.info(
            "Session not found: %s",
            error.session_id.value,
        )

        return JSONResponse(
            status_code=404,
            content={
                "error": "session_not_found",
                "message": "Session not found.",
            },
        )

    @app.exception_handler(SessionExpiredError)
    async def handle_session_expired_error(
        request: Request,
        error: SessionExpiredError,
    ) -> JSONResponse:
        del request

        logger.info(
            "Session expired: %s",
            error.session_id.value,
        )

        return JSONResponse(
            status_code=404,
            content={
                "error": "session_expired",
                "message": ("The session has expired."),
            },
        )

    @app.exception_handler(RedisError)
    async def handle_redis_error(
        request: Request,
        error: RedisError,
    ) -> JSONResponse:
        del request

        logger.warning(
            "Redis session storage unavailable: %s",
            type(error).__name__,
        )

        return JSONResponse(
            status_code=503,
            content={
                "error": "session_storage_unavailable",
                "message": "Session storage is temporarily unavailable.",
            },
        )
