from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator

from app.types.json_types import JsonValue


class ChatRequest(BaseModel):
    message: Annotated[
        str,
        Field(
            min_length=1,
            max_length=10_000,
            description="The user's chat message.",
            examples=[
                "What is 125 * 8?",
            ],
        ),
    ]

    metadata: dict[str, JsonValue] = Field(
        default_factory=dict,
        description="Optional request metadata passed to the agent.",
        examples=[
            {
                "request_id": "request-123",
                "user_id": "frank",
                "source": "api",
            }
        ],
    )

    @field_validator(
        "message",
        mode="before",
    )
    @classmethod
    def validate_message(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            stripped_value = value.strip()

            if not stripped_value:
                raise ValueError("message must not be blank.")

            return stripped_value

        return value


class ChatResponse(BaseModel):
    response: str


class ErrorResponse(BaseModel):
    error: str
    message: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
