import re
from collections.abc import Sequence
from re import Match

from app.retrieval.citations.invalid_citation_error import (
    InvalidCitationError,
)
from app.retrieval.retrieved_context import RetrievedContext


class CitationGuard:
    _citation_pattern = re.compile(
        r"(?:"
        r"\[source[:：](?P<ascii_number>\d+)\]"
        r"|"
        r"【source[:：](?P<localized_number>\d+)】"
        r")"
    )
    _citation_like_pattern = re.compile(
        r"(?:"
        r"\[source[:：][^\]]*\]"
        r"|"
        r"【source[:：][^】]*】"
        r")",
        flags=re.IGNORECASE,
    )
    _direct_source_pattern = re.compile(
        r"^\s*source\s*:",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    def apply(
        self,
        response: str,
        contexts: Sequence[RetrievedContext],
    ) -> str:
        self._reject_untrusted_citation_formats(response)

        citeable_contexts = [
            context for context in contexts if context.source is not None
        ]

        def replace_citation(
            match: Match[str],
        ) -> str:
            citation_number_text = match.group("ascii_number") or match.group(
                "localized_number"
            )

            if citation_number_text is None:
                raise AssertionError("Matched citation does not contain a number.")

            citation_number = int(citation_number_text)
            context_index = citation_number - 1

            if context_index < 0 or context_index >= len(citeable_contexts):
                raise InvalidCitationError(
                    f"Unknown citation token: source:{citation_number}"
                )

            context = citeable_contexts[context_index]

            return self._format_citation(context)

        return self._citation_pattern.sub(
            replace_citation,
            response,
        )

    def _format_citation(
        self,
        context: RetrievedContext,
    ) -> str:
        if context.source is None:
            raise ValueError("Citation context must contain a source.")

        if context.page is not None:
            return f"[Source: {context.source} (page {context.page})]"

        return f"[Source: {context.source}]"

    def _reject_untrusted_citation_formats(
        self,
        response: str,
    ) -> None:
        for match in self._citation_like_pattern.finditer(response):
            citation = match.group(0)

            if self._citation_pattern.fullmatch(citation) is None:
                raise InvalidCitationError(f"Untrusted citation format: {citation}")

        if self._direct_source_pattern.search(response) is not None:
            raise InvalidCitationError("Untrusted citation format: direct source label")
