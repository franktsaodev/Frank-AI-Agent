from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

from fastapi import FastAPI

Lifespan = Callable[
    [FastAPI],
    AbstractAsyncContextManager[None],
]
