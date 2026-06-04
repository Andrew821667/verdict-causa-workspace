from enum import Enum


class RiskTier(str, Enum):
    T1_REFERENCE = "t1_reference"
    T2_INTERNAL_MEMO = "t2_internal_memo"
    T3_DRAFT_LETTER = "t3_draft_letter"
    T4_PROCEDURAL_DRAFT = "t4_procedural_draft"
    T5_HIGH_STAKES_RECOMMENDATION = "t5_high_stakes_recommendation"
    T6_READY_TO_FILE_DOCUMENT = "t6_ready_to_file_document"
