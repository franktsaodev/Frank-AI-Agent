import re

from app.extractors.base_fact_extractor import BaseFactExtractor


class RegexFactExtractor(BaseFactExtractor):
    _NAME_PATTERN = re.compile(
        r"\bmy name is\s+([A-Za-z][A-Za-z'-]*)\b",
        re.IGNORECASE,
    )

    def extract(
        self,
        user_message: str,
    ) -> dict[str, str]:
        if not isinstance(user_message, str):
            raise TypeError(
                "user_message must be a string, "
                f"but received {type(user_message).__name__}."
            )

        cleaned_message = user_message.strip()

        if not cleaned_message:
            return {}

        facts: dict[str, str] = {}

        name_match = self._NAME_PATTERN.search(cleaned_message)

        if name_match is not None:
            user_name = name_match.group(1).strip()

            facts["user_name"] = user_name

        return facts
