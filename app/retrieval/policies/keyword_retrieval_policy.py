class KeywordRetrievalPolicy:
    def __init__(
        self,
        *,
        keywords: set[str],
    ) -> None:
        self._keywords = {keyword.casefold() for keyword in keywords}

    def should_retrieve(self, query: str) -> bool:
        normalized_query = query.casefold()

        return any(keyword in normalized_query for keyword in self._keywords)
