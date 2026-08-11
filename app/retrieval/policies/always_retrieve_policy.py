class AlwaysRetrievePolicy:
    def should_retrieve(self, query: str) -> bool:
        return True
