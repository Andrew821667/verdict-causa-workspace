from enum import Enum


class FailureType(str, Enum):
    HALLUCINATED_SOURCE_GROUNDING = "hallucinated_source_grounding"
    BAD_FORMALIZATION = "bad_formalization"
    WRONG_TEMPORAL_APPLICABILITY = "wrong_temporal_applicability"
    WRONG_AUTHORITY_RANKING = "wrong_authority_ranking"
    OVERBROAD_CANDIDATE_PRINCIPLE = "overbroad_candidate_principle"
    TRANSLATION_DISTORTION = "translation_distortion"
    ESCALATION_FAILURE = "escalation_failure"
    FALSE_CONFIDENCE_INFLATION = "false_confidence_inflation"
    PRIVACY_LEAKAGE_RISK = "privacy_leakage_risk"
    BENCHMARK_OVERFITTING = "benchmark_overfitting"
