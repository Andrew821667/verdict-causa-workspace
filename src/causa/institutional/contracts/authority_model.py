from datetime import date
from enum import Enum

from pydantic import BaseModel, Field

from causa.core.models import LegalSource, SourceType
from causa.core.source_hierarchy import AuthorityLevel
from causa.core.temporal_validity import evaluate_source_applicability
from causa.localization.ru import AUTHORITY_LEVEL_LABELS_RU, label_ru


SOURCE_TYPE_AUTHORITY_LEVEL = {
    SourceType.STATUTE: AuthorityLevel.STATUTORY,
    SourceType.CASE_LAW: AuthorityLevel.JUDICIAL,
    SourceType.CONTRACT: AuthorityLevel.CONTRACTUAL,
    SourceType.FACT: AuthorityLevel.FACTUAL,
}

SPECIFICITY_RANK = {
    "general": 0,
    "special": 1,
}


class AuthorityPolicyReviewStatus(str, Enum):
    SYNTHETIC_REVIEWED = "synthetic_reviewed"


class ContractAuthorityPolicy(BaseModel):
    id: str
    review_status: AuthorityPolicyReviewStatus
    authority_order: list[AuthorityLevel] = Field(default_factory=list)
    scope_note: str
    scope_note_ru: str


CONTRACT_AUTHORITY_POLICY = ContractAuthorityPolicy(
    id="contracts-ru-authority-policy-v0",
    review_status=AuthorityPolicyReviewStatus.SYNTHETIC_REVIEWED,
    authority_order=[
        AuthorityLevel.CONSTITUTIONAL,
        AuthorityLevel.STATUTORY,
        AuthorityLevel.REGULATORY,
        AuthorityLevel.JUDICIAL,
        AuthorityLevel.CONTRACTUAL,
        AuthorityLevel.FACTUAL,
    ],
    scope_note=(
        "Synthetic Phase 0 ordering for test sources only; it is not a complete "
        "jurisdiction-specific authority policy."
    ),
    scope_note_ru=(
        "Синтетический порядок юридической силы используется только для тестов Этапа 0 "
        "и не является полной моделью системы источников российского права."
    ),
)

CONTRACT_AUTHORITY_ORDER = CONTRACT_AUTHORITY_POLICY.authority_order

AUTHORITY_RANK = {
    authority_level: len(CONTRACT_AUTHORITY_ORDER) - position
    for position, authority_level in enumerate(CONTRACT_AUTHORITY_ORDER)
}


class AuthorityResolutionRule(str, Enum):
    TEMPORAL_APPLICABILITY = "temporal_applicability"
    HIGHER_AUTHORITY = "higher_authority"
    LEX_SPECIALIS = "lex_specialis"
    UNRESOLVED_EQUAL_AUTHORITY = "unresolved_equal_authority"


class AuthorityEvaluation(BaseModel):
    selected_source_id: str | None = None
    selected_authority_level: AuthorityLevel | None = None
    candidate_source_ids: list[str] = Field(default_factory=list)
    applicable_source_ids: list[str] = Field(default_factory=list)
    excluded_source_ids: list[str] = Field(default_factory=list)
    applied_rules: list[AuthorityResolutionRule] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    reasons_ru: list[str] = Field(default_factory=list)


def authority_level_for_source(source: LegalSource) -> AuthorityLevel:
    metadata_level = source.metadata.get("authority_level")
    if metadata_level is not None:
        try:
            authority_level = AuthorityLevel(str(metadata_level))
        except ValueError as error:
            msg = f"Unknown authority level for source {source.id}: {metadata_level}"
            raise ValueError(msg) from error
    else:
        try:
            authority_level = SOURCE_TYPE_AUTHORITY_LEVEL[source.source_type]
        except KeyError as error:
            msg = (
                f"Source {source.id} requires metadata.authority_level for "
                f"source type {source.source_type.value}."
            )
            raise ValueError(msg) from error

    if authority_level not in AUTHORITY_RANK:
        msg = f"Authority level {authority_level.value} is not supported by contracts-ru-v0."
        raise ValueError(msg)
    return authority_level


def evaluate_source_authority(
    sources: list[LegalSource],
    moment: date | None = None,
) -> AuthorityEvaluation:
    if not sources:
        msg = "At least one source is required for authority evaluation."
        raise ValueError(msg)

    candidate_source_ids = [source.id for source in sources]
    applicable_sources: list[LegalSource] = []
    excluded_source_ids: list[str] = []
    reasons: list[str] = []
    reasons_ru: list[str] = []
    applied_rules: list[AuthorityResolutionRule] = []

    for source in sources:
        if moment is None:
            applicable_sources.append(source)
            continue

        applicability = evaluate_source_applicability(source, moment)
        if applicability.applicable:
            applicable_sources.append(source)
            continue

        excluded_source_ids.append(source.id)
        reasons.extend(
            f"Excluded {source.id}: {reason}" for reason in applicability.reasons
        )
        reasons_ru.extend(
            f"Источник {source.id} исключен: {reason}"
            for reason in applicability.reasons_ru
        )

    if excluded_source_ids:
        applied_rules.append(AuthorityResolutionRule.TEMPORAL_APPLICABILITY)

    if not applicable_sources:
        reasons.append("No candidate source is applicable at the evaluation date.")
        reasons_ru.append("На дату оценки отсутствуют применимые источники-кандидаты.")
        return AuthorityEvaluation(
            candidate_source_ids=candidate_source_ids,
            excluded_source_ids=excluded_source_ids,
            applied_rules=applied_rules,
            reasons=reasons,
            reasons_ru=reasons_ru,
        )

    authority_levels = {
        source.id: authority_level_for_source(source) for source in applicable_sources
    }
    highest_rank = max(AUTHORITY_RANK[authority_levels[source.id]] for source in applicable_sources)
    highest_sources = [
        source
        for source in applicable_sources
        if AUTHORITY_RANK[authority_levels[source.id]] == highest_rank
    ]
    highest_level = authority_levels[highest_sources[0].id]
    lower_sources = [source for source in applicable_sources if source not in highest_sources]

    if lower_sources:
        applied_rules.append(AuthorityResolutionRule.HIGHER_AUTHORITY)
        reasons.append(
            f"Sources at {highest_level.value} authority prevail over lower-authority sources."
        )
        reasons_ru.append(
            "Источники уровня «"
            f"{label_ru(highest_level, AUTHORITY_LEVEL_LABELS_RU)}"
            "» имеют приоритет перед источниками меньшей юридической силы."
        )

    highest_specificity = max(
        SPECIFICITY_RANK.get(str(source.metadata.get("specificity", "general")), 0)
        for source in highest_sources
    )
    preferred_sources = [
        source
        for source in highest_sources
        if SPECIFICITY_RANK.get(str(source.metadata.get("specificity", "general")), 0)
        == highest_specificity
    ]

    if len(preferred_sources) > 1:
        applied_rules.append(AuthorityResolutionRule.UNRESOLVED_EQUAL_AUTHORITY)
        reasons.append(
            "Candidate sources remain equal in authority and specificity; human resolution is required."
        )
        reasons_ru.append(
            "Источники-кандидаты равны по юридической силе и степени специальности; "
            "требуется разрешение экспертом."
        )
        return AuthorityEvaluation(
            selected_authority_level=highest_level,
            candidate_source_ids=candidate_source_ids,
            applicable_source_ids=[source.id for source in applicable_sources],
            excluded_source_ids=excluded_source_ids,
            applied_rules=applied_rules,
            reasons=reasons,
            reasons_ru=reasons_ru,
        )

    selected = preferred_sources[0]
    if len(highest_sources) > 1:
        applied_rules.append(AuthorityResolutionRule.LEX_SPECIALIS)
        reasons.append("Special source prevails over general source at the same authority level.")
        reasons_ru.append(
            "Специальный источник имеет приоритет перед общим источником "
            "того же уровня юридической силы."
        )

    reasons.insert(0, f"Selected {selected.id} at {highest_level.value} authority.")
    reasons_ru.insert(
        0,
        f"Выбран источник {selected.id}: {label_ru(highest_level, AUTHORITY_LEVEL_LABELS_RU)}.",
    )
    return AuthorityEvaluation(
        selected_source_id=selected.id,
        selected_authority_level=highest_level,
        candidate_source_ids=candidate_source_ids,
        applicable_source_ids=[source.id for source in applicable_sources],
        excluded_source_ids=excluded_source_ids,
        applied_rules=applied_rules,
        reasons=reasons,
        reasons_ru=reasons_ru,
    )


def evaluate_lex_specialis(sources: list[LegalSource]) -> AuthorityEvaluation:
    return evaluate_source_authority(sources)
