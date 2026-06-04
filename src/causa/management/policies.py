from dataclasses import dataclass

from causa.management.risk_tiers import RiskTier
from causa.management.sla_modes import SLAMode


@dataclass(frozen=True)
class GovernancePolicy:
    require_expert_review: bool = True
    allow_auto_activation: bool = False


@dataclass(frozen=True)
class CasePolicy:
    mode: SLAMode
    risk_tier: RiskTier
    require_replayable_trace: bool = True
    require_complete_provenance: bool = True
