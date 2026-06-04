from enum import Enum


class CandidateType(str, Enum):
    META_PRINCIPLE = "meta_principle"
    CALIBRATION_RULE = "calibration_rule"
    GAP_HEURISTIC = "gap_heuristic"
    CONFLICT_RESOLUTION_PATTERN = "conflict_resolution_pattern"
    COUNTERFACTUAL_SENSITIVITY_PATTERN = "counterfactual_sensitivity_pattern"
    ARGUMENT_TEMPLATE = "argument_template"
    TRANSLATION_PATTERN = "translation_pattern"
