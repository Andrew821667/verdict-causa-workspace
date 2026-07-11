from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


LIABILITY_EVIDENCE_SCHEMA_VERSION = "contracts.liability-evidence.v0"
LIABILITY_MAPPING_VERSION = "contracts-reviewed-liability-to-facts-v0"
LIABILITY_MODEL_VERSION = "contracts-liability-articles-333-401-v0"


class LiabilityEvidencePredicate(str, Enum):
    BREACH_ESTABLISHED = "breach_established"
    DEBTOR_ACTING_IN_BUSINESS = "debtor_acting_in_business"
    FAULT_REBUTTAL_ASSERTED = "fault_rebuttal_asserted"
    REASONABLE_CARE_PROVEN = "reasonable_care_proven"
    ALL_REASONABLE_MEASURES_PROVEN = "all_reasonable_measures_proven"
    FORCE_MAJEURE_CLAIMED = "force_majeure_claimed"
    EXTRAORDINARY_EVENT_PROVEN = "extraordinary_event_proven"
    UNAVOIDABLE_EVENT_PROVEN = "unavoidable_event_proven"
    BEYOND_DEBTOR_CONTROL_PROVEN = "beyond_debtor_control_proven"
    FORCE_MAJEURE_CAUSAL_LINK_PROVEN = "force_majeure_causal_link_proven"
    EXCLUDED_COMMERCIAL_RISK_ONLY = "excluded_commercial_risk_only"
    NOTICE_AND_MITIGATION_PROVEN = "notice_and_mitigation_proven"
    INTENTIONAL_BREACH = "intentional_breach"
    ADVANCE_LIABILITY_EXCLUSION_CLAUSE = "advance_liability_exclusion_clause"
    PENALTY_CLAIMED = "penalty_claimed"
    CONTRACTUAL_PENALTY = "contractual_penalty"
    PENALTY_REDUCTION_REQUESTED = "penalty_reduction_requested"
    MANIFEST_DISPROPORTIONALITY_PROVEN = "manifest_disproportionality_proven"
    UNJUSTIFIED_BENEFIT_RISK_PROVEN = "unjustified_benefit_risk_proven"
    ONLY_EXCLUDED_REDUCTION_REASONS = "only_excluded_reduction_reasons"


REQUIRED_LIABILITY_PREDICATES = frozenset(LiabilityEvidencePredicate)


class LiabilityEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: LiabilityEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedLiabilityEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = LIABILITY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[LiabilityEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicate_predicates(self) -> "ReviewedLiabilityEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Liability evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Liability evidence contains duplicate legal source refs.")
        return self


class LiabilityFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    breach_established: bool
    debtor_acting_in_business: bool
    fault_rebuttal_asserted: bool
    reasonable_care_proven: bool
    all_reasonable_measures_proven: bool
    force_majeure_claimed: bool
    extraordinary_event_proven: bool
    unavoidable_event_proven: bool
    beyond_debtor_control_proven: bool
    force_majeure_causal_link_proven: bool
    excluded_commercial_risk_only: bool
    notice_and_mitigation_proven: bool
    intentional_breach: bool
    advance_liability_exclusion_clause: bool
    penalty_claimed: bool
    contractual_penalty: bool
    penalty_reduction_requested: bool
    manifest_disproportionality_proven: bool
    unjustified_benefit_risk_proven: bool
    only_excluded_reduction_reasons: bool

    @model_validator(mode="after")
    def validate_fact_consistency(self) -> "LiabilityFactSet":
        if self.intentional_breach and not self.breach_established:
            raise ValueError("Intentional breach requires an established breach.")
        if self.penalty_claimed and not self.breach_established:
            raise ValueError("A claimed penalty requires an established breach.")
        if self.penalty_reduction_requested and not self.penalty_claimed:
            raise ValueError("Penalty reduction cannot be requested without a claimed penalty.")
        return self


class LiabilityFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class LiabilityEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: LiabilityFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[LiabilityFactProvenance] = Field(default_factory=list)


class LiabilityConstraintSet(BaseModel):
    id: str
    model_version: str = LIABILITY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class LiabilityEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    fault_rebutted: bool
    force_majeure_qualified: bool
    exemption_prerequisites_satisfied: bool
    liability_issue: bool
    force_majeure_notice_gap: bool
    intentional_exclusion_invalid: bool
    penalty_reduction_procedurally_available: bool
    penalty_reduction_substantively_supported: bool
    penalty_reduction_prerequisites_satisfied: bool
    invalid_penalty_reduction_basis: bool
    liability_survives_penalty_reduction: bool
    requires_judicial_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_liability_evidence(
    evidence: ReviewedLiabilityEvidence,
) -> LiabilityEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Liability evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Liability evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_LIABILITY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed liability evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_LIABILITY_PREDICATES
    }
    return LiabilityEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=LIABILITY_MAPPING_VERSION,
        facts=LiabilityFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            LiabilityFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_LIABILITY_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_liability_constraint_set(
    mapping: LiabilityEvidenceMappingResult,
) -> LiabilityConstraintSet:
    return LiabilityConstraintSet(
        id=f"liability-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "fault_rebutted == fault_rebuttal_asserted AND reasonable_care_proven AND all_reasonable_measures_proven",
            "force_majeure_qualified == force_majeure_claimed AND extraordinary_event_proven AND unavoidable_event_proven AND beyond_debtor_control_proven AND force_majeure_causal_link_proven AND NOT excluded_commercial_risk_only AND NOT intentional_breach",
            "exemption_prerequisites_satisfied == breach_established AND ((NOT debtor_acting_in_business AND fault_rebutted) OR (debtor_acting_in_business AND force_majeure_qualified))",
            "liability_issue == breach_established AND NOT exemption_prerequisites_satisfied",
            "force_majeure_notice_gap == force_majeure_qualified AND NOT notice_and_mitigation_proven",
            "intentional_exclusion_invalid == intentional_breach AND advance_liability_exclusion_clause",
            "penalty_reduction_procedurally_available == penalty_claimed AND (NOT debtor_acting_in_business OR penalty_reduction_requested)",
            "penalty_reduction_substantively_supported == penalty_claimed AND manifest_disproportionality_proven AND NOT only_excluded_reduction_reasons AND (NOT (debtor_acting_in_business AND contractual_penalty) OR unjustified_benefit_risk_proven)",
            "penalty_reduction_prerequisites_satisfied == penalty_reduction_procedurally_available AND penalty_reduction_substantively_supported",
            "liability_survives_penalty_reduction == liability_issue AND penalty_reduction_prerequisites_satisfied",
        ],
    )


def evaluate_liability_constraints(
    constraint_set: LiabilityConstraintSet,
    facts: LiabilityFactSet,
) -> LiabilityEvaluation:
    variables = {field_name: Bool(field_name) for field_name in LiabilityFactSet.model_fields}
    fault_rebutted = Bool("fault_rebutted")
    force_majeure_qualified = Bool("force_majeure_qualified")
    exemption_prerequisites_satisfied = Bool("exemption_prerequisites_satisfied")
    liability_issue = Bool("liability_issue")
    force_majeure_notice_gap = Bool("force_majeure_notice_gap")
    intentional_exclusion_invalid = Bool("intentional_exclusion_invalid")
    penalty_reduction_procedurally_available = Bool(
        "penalty_reduction_procedurally_available"
    )
    penalty_reduction_substantively_supported = Bool(
        "penalty_reduction_substantively_supported"
    )
    penalty_reduction_prerequisites_satisfied = Bool(
        "penalty_reduction_prerequisites_satisfied"
    )
    invalid_penalty_reduction_basis = Bool("invalid_penalty_reduction_basis")
    liability_survives_penalty_reduction = Bool("liability_survives_penalty_reduction")
    requires_judicial_assessment = Bool("requires_judicial_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        fault_rebutted
        == And(
            variables["fault_rebuttal_asserted"],
            variables["reasonable_care_proven"],
            variables["all_reasonable_measures_proven"],
        )
    )
    solver.add(
        force_majeure_qualified
        == And(
            variables["force_majeure_claimed"],
            variables["extraordinary_event_proven"],
            variables["unavoidable_event_proven"],
            variables["beyond_debtor_control_proven"],
            variables["force_majeure_causal_link_proven"],
            Not(variables["excluded_commercial_risk_only"]),
            Not(variables["intentional_breach"]),
        )
    )
    solver.add(
        exemption_prerequisites_satisfied
        == And(
            variables["breach_established"],
            Or(
                And(Not(variables["debtor_acting_in_business"]), fault_rebutted),
                And(variables["debtor_acting_in_business"], force_majeure_qualified),
            ),
        )
    )
    solver.add(
        liability_issue
        == And(
            variables["breach_established"],
            Not(exemption_prerequisites_satisfied),
        )
    )
    solver.add(
        force_majeure_notice_gap
        == And(force_majeure_qualified, Not(variables["notice_and_mitigation_proven"]))
    )
    solver.add(
        intentional_exclusion_invalid
        == And(
            variables["intentional_breach"],
            variables["advance_liability_exclusion_clause"],
        )
    )
    solver.add(
        penalty_reduction_procedurally_available
        == And(
            variables["penalty_claimed"],
            Or(
                Not(variables["debtor_acting_in_business"]),
                variables["penalty_reduction_requested"],
            ),
        )
    )
    business_contractual_penalty = And(
        variables["debtor_acting_in_business"],
        variables["contractual_penalty"],
    )
    solver.add(
        penalty_reduction_substantively_supported
        == And(
            variables["penalty_claimed"],
            variables["manifest_disproportionality_proven"],
            Not(variables["only_excluded_reduction_reasons"]),
            Or(
                Not(business_contractual_penalty),
                variables["unjustified_benefit_risk_proven"],
            ),
        )
    )
    solver.add(
        penalty_reduction_prerequisites_satisfied
        == And(
            penalty_reduction_procedurally_available,
            penalty_reduction_substantively_supported,
        )
    )
    solver.add(
        invalid_penalty_reduction_basis
        == And(
            variables["penalty_claimed"],
            variables["only_excluded_reduction_reasons"],
        )
    )
    solver.add(
        liability_survives_penalty_reduction
        == And(liability_issue, penalty_reduction_prerequisites_satisfied)
    )
    solver.add(requires_judicial_assessment == variables["penalty_claimed"])

    satisfiable = solver.check() == sat
    if not satisfiable:
        return LiabilityEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            fault_rebutted=False,
            force_majeure_qualified=False,
            exemption_prerequisites_satisfied=False,
            liability_issue=False,
            force_majeure_notice_gap=False,
            intentional_exclusion_invalid=False,
            penalty_reduction_procedurally_available=False,
            penalty_reduction_substantively_supported=False,
            penalty_reduction_prerequisites_satisfied=False,
            invalid_penalty_reduction_basis=False,
            liability_survives_penalty_reduction=False,
            requires_judicial_assessment=False,
            reasons_ru=["Набор ограничений ответственности противоречив."],
            warnings_ru=["Требуется проверка модели и исходных данных."],
        )

    model = solver.model()
    values = {
        "fault_rebutted": bool(model.eval(fault_rebutted)),
        "force_majeure_qualified": bool(model.eval(force_majeure_qualified)),
        "exemption_prerequisites_satisfied": bool(
            model.eval(exemption_prerequisites_satisfied)
        ),
        "liability_issue": bool(model.eval(liability_issue)),
        "force_majeure_notice_gap": bool(model.eval(force_majeure_notice_gap)),
        "intentional_exclusion_invalid": bool(model.eval(intentional_exclusion_invalid)),
        "penalty_reduction_procedurally_available": bool(
            model.eval(penalty_reduction_procedurally_available)
        ),
        "penalty_reduction_substantively_supported": bool(
            model.eval(penalty_reduction_substantively_supported)
        ),
        "penalty_reduction_prerequisites_satisfied": bool(
            model.eval(penalty_reduction_prerequisites_satisfied)
        ),
        "invalid_penalty_reduction_basis": bool(
            model.eval(invalid_penalty_reduction_basis)
        ),
        "liability_survives_penalty_reduction": bool(
            model.eval(liability_survives_penalty_reduction)
        ),
        "requires_judicial_assessment": bool(model.eval(requires_judicial_assessment)),
    }
    reasons_ru = []
    if values["force_majeure_qualified"]:
        reasons_ru.append(
            "Формальные признаки чрезвычайности, непредотвратимости, внешнего характера "
            "и причинной связи для непреодолимой силы подтверждены."
        )
    if facts.excluded_commercial_risk_only:
        reasons_ru.append(
            "Указано только исключенное коммерческое обстоятельство; оно не признано "
            "непреодолимой силой в текущей модели."
        )
    if values["liability_issue"]:
        reasons_ru.append(
            "Нарушение установлено, а формальные предпосылки освобождения от ответственности "
            "не подтверждены."
        )
    if values["penalty_reduction_prerequisites_satisfied"]:
        reasons_ru.append(
            "Формальные предпосылки постановки вопроса о снижении неустойки подтверждены."
        )
    if values["invalid_penalty_reduction_basis"]:
        reasons_ru.append(
            "Для снижения указаны только обстоятельства, которые сами по себе не образуют "
            "надлежащего основания."
        )
    if values["intentional_exclusion_invalid"]:
        reasons_ru.append(
            "Заранее согласованное исключение ответственности за умышленное нарушение "
            "помечено как недопустимое."
        )
    warnings_ru = [
        "Модель проверяет только формальные предпосылки статей 333 и 401 ГК РФ.",
        "Квалификация доказательств, исключительность случая и размер снижения относятся к суду.",
        "Результат не является юридической консультацией.",
    ]
    return LiabilityEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        **values,
        reasons_ru=reasons_ru,
        warnings_ru=warnings_ru,
    )
