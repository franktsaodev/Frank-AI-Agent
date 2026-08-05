import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.client_exceptions import (
    AIClientError,
    ClientAuthenticationError,
    ClientConnectionError,
    ClientTimeoutError,
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

    @app.exception_handler(AIClientError)
    async def handle_ai_client_error(
        request: Request,
        error: AIClientError,
    ) -> JSONResponse:
        del request

        logger.exception(
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
