class NeverRetrievePolicy:
    def should_retrieve(self, query: str) -> bool:
        return False
