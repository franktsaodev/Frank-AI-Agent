import logging

logger = logging.getLogger(__name__)


class KeywordRetrievalPolicy:
    def __init__(
        self,
        *,
        keywords: set[str],
    ) -> None:
        self._keywords = {keyword.casefold() for keyword in keywords}

    def should_retrieve(
        self,
        query: str,
    ) -> bool:
        normalized_query = query.casefold()

        should_retrieve = any(keyword in normalized_query for keyword in self._keywords)

        logger.debug(
            "Retrieval policy decision: should_retrieve=%s",
            should_retrieve,
        )

        return should_retrieve
