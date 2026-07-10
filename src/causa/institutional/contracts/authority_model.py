from pydantic import BaseModel, Field

from causa.core.models import LegalSource
from causa.core.source_hierarchy import AuthorityLevel


CONTRACT_AUTHORITY_ORDER = [
    AuthorityLevel.STATUTORY,
    AuthorityLevel.JUDICIAL,
    AuthorityLevel.CONTRACTUAL,
    AuthorityLevel.FACTUAL,
]


SPECIFICITY_RANK = {
    "general": 0,
    "special": 1,
}


class AuthorityEvaluation(BaseModel):
    selected_source_id: str
    candidate_source_ids: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


def evaluate_lex_specialis(sources: list[LegalSource]) -> AuthorityEvaluation:
    if not sources:
        msg = "At least one source is required for authority evaluation."
        raise ValueError(msg)

    selected = max(
        sources,
        key=lambda source: SPECIFICITY_RANK.get(str(source.metadata.get("specificity", "general")), 0),
    )
    reasons = [f"Selected {selected.id}."]
    if selected.metadata.get("specificity") == "special":
        reasons.append("Special source prevails over general source.")
    else:
        reasons.append("No more specific contractual source was available.")

    return AuthorityEvaluation(
        selected_source_id=selected.id,
        candidate_source_ids=[source.id for source in sources],
        reasons=reasons,
    )
