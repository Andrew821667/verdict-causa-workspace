from dataclasses import dataclass


@dataclass(frozen=True)
class CostBudget:
    max_requests: int
    max_tokens: int | None = None
