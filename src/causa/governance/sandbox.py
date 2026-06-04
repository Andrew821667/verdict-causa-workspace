from dataclasses import dataclass


@dataclass(frozen=True)
class SandboxActivation:
    candidate_id: str
    enabled: bool = False
