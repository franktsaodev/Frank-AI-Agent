import json

from app.clients.base_client import BaseClient
from app.extractors.base_fact_extractor import BaseFactExtractor
from app.models.message import Message
from app.models.message_role import MessageRole


class LLMFactExtractor(BaseFactExtractor):
    SYSTEM_PROMPT = """
You are a fact extraction assistant.

Extract stable and useful facts about the user from the message.

Return only a valid JSON object.

Rules:
- Use short snake_case keys.
- All values must be strings.
- Do not infer facts that were not explicitly stated.
- Ignore temporary information, questions, opinions, and greetings.
- If there are no useful facts, return {}.

Examples:

User message:
My name is Frank.

Output:
{"user_name": "Frank"}

User message:
I live in Hai Phong.

Output:
{"location": "Hai Phong"}

User message:
How are you?

Output:
{}
""".strip()

    def __init__(
        self,
        client: BaseClient,
    ) -> None:
        self.client = client

    def _build_messages(
        self,
        user_message: str,
    ) -> list[Message]:
        return [
            Message(
                role=MessageRole.SYSTEM,
                content=self.SYSTEM_PROMPT,
            ),
            Message(
                role=MessageRole.USER,
                content=user_message,
            ),
        ]

    def _clean_response(
        self,
        response: str,
    ) -> str:
        response = response.strip()

        response = response.removeprefix("```json")

        response = response.removeprefix("```")

        response = response.removesuffix("```")

        return response.strip()

    def _parse_response(
        self,
        response: str,
    ) -> dict[str, str]:
        parsed = json.loads(response)

        if not isinstance(parsed, dict):
            raise ValueError("Fact extraction response must be a JSON object.")  # noqa: TRY004

        for key, value in parsed.items():
            if not isinstance(key, str):
                raise ValueError("Fact keys must be strings.")  # noqa: TRY004

            if not isinstance(value, str):
                raise ValueError("Fact values must be strings.")  # noqa: TRY004

        return parsed

    def extract(
        self,
        user_message: str,
    ) -> dict[str, str]:
        messages = self._build_messages(
            user_message,
        )

        client_response = self.client.chat(messages)

        if client_response.content is None:
            raise ValueError("Fact extraction response does not contain text content.")

        cleaned_response = self._clean_response(
            client_response.content,
        )

        return self._parse_response(
            cleaned_response,
        )
