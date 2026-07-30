class MaxIterationsExceededError(RuntimeError):
    """Raised when the agent exceeds the allowed number of iterations."""

    def __init__(
        self,
        max_iterations: int,
    ) -> None:
        self.max_iterations = max_iterations

        super().__init__(
            f"Agent exceeded the maximum number of iterations: {max_iterations}."
        )
