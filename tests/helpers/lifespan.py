from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def empty_lifespan(
    app: FastAPI,
) -> AsyncGenerator[None]:
    del app

    yield
