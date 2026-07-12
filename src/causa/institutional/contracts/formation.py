from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


FORMATION_EVIDENCE_SCHEMA_VERSION = "contracts.formation-evidence.v0"
FORMATION_MAPPING_VERSION = "contracts-reviewed-formation-to-facts-v0"
FORMATION_MODEL_VERSION = "contracts-formation-articles-432-443-v0"


class FormationEvidencePredicate(str, Enum):
    PROPOSAL_MADE = "proposal_made"
    PROPOSAL_ADDRESSED_TO_COUNTERPARTY = "proposal_addressed_to_counterparty"
    INTENT_TO_BE_BOUND = "intent_to_be_bound"
    SUBJECT_MATTER_DEFINED_IN_OFFER = "subject_matter_defined_in_offer"
    STATUTORY_ESSENTIAL_TERMS_DEFINED_IN_OFFER = "statutory_essential_terms_defined_in_offer"
    PARTY_DECLARED_ESSENTIAL_TERMS_DEFINED_IN_OFFER = (
        "party_declared_essential_terms_defined_in_offer"
    )
    REQUIRED_FORM_OBSERVED = "required_form_observed"
    ACCEPTANCE_RECEIVED = "acceptance_received"
    ACCEPTANCE_FULL_AND_UNCONDITIONAL = "acceptance_full_and_unconditional"
    ACCEPTANCE_WITHIN_PERIOD = "acceptance_within_period"
    ACCEPTANCE_BY_CONDUCT = "acceptance_by_conduct"
    PERFORMANCE_CONDUCT_STARTED_IN_TIME = "performance_conduct_started_in_time"
    SILENCE_ONLY = "silence_only"
    SILENCE_ACCEPTANCE_BASIS_EXISTS = "silence_acceptance_basis_exists"
    ACCEPTANCE_ON_OTHER_TERMS = "acceptance_on_other_terms"
    PERFORMANCE_ACCEPTED_WITHOUT_OBJECTION = "performance_accepted_without_objection"
    BAD_FAITH_NON_CONCLUSION_OBJECTION = "bad_faith_non_conclusion_objection"


REQUIRED_FORMATION_PREDICATES = frozenset(FormationEvidencePredicate)


class FormationEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: FormationEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedFormationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = FORMATION_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[FormationEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedFormationEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Formation evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Formation evidence contains duplicate legal source refs.")
        return self


class FormationFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_made: bool
    proposal_addressed_to_counterparty: bool
    intent_to_be_bound: bool
    subject_matter_defined_in_offer: bool
    statutory_essential_terms_defined_in_offer: bool
    party_declared_essential_terms_defined_in_offer: bool
    required_form_observed: bool
    acceptance_received: bool
    acceptance_full_and_unconditional: bool
    acceptance_within_period: bool
    acceptance_by_conduct: bool
    performance_conduct_started_in_time: bool
    silence_only: bool
    silence_acceptance_basis_exists: bool
    acceptance_on_other_terms: bool
    performance_accepted_without_objection: bool
    bad_faith_non_conclusion_objection: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "FormationFactSet":
        if self.acceptance_on_other_terms and self.acceptance_full_and_unconditional:
            raise ValueError("Acceptance cannot be unconditional and on other terms.")
        if self.performance_conduct_started_in_time and not self.acceptance_by_conduct:
            raise ValueError("Timed performance conduct requires acceptance by conduct.")
        if self.silence_only and (self.acceptance_received or self.acceptance_by_conduct):
            raise ValueError("Silence-only evidence cannot include express or conduct acceptance.")
        if (
            self.bad_faith_non_conclusion_objection
            and not self.performance_accepted_without_objection
        ):
            raise ValueError("Bad-faith non-conclusion objection requires accepted performance.")
        return self


class FormationFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class FormationEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: FormationFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[FormationFactProvenance] = Field(default_factory=list)


class FormationConstraintSet(BaseModel):
    id: str
    model_version: str = FORMATION_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class FormationEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    essential_terms_defined_in_offer: bool
    essential_terms_agreed: bool
    valid_offer: bool
    express_acceptance_valid: bool
    conduct_acceptance_valid: bool
    silence_acceptance_valid: bool
    counteroffer_detected: bool
    contract_concluded_prerequisites: bool
    formation_evidence_gap: bool
    non_conclusion_objection_barred: bool
    requires_human_formation_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_formation_evidence(
    evidence: ReviewedFormationEvidence,
) -> FormationEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Formation evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Formation evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_FORMATION_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed formation evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_FORMATION_PREDICATES
    }
    return FormationEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=FORMATION_MAPPING_VERSION,
        facts=FormationFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            FormationFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_FORMATION_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_formation_constraint_set(
    mapping: FormationEvidenceMappingResult,
) -> FormationConstraintSet:
    return FormationConstraintSet(
        id=f"formation-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "essential_terms_defined_in_offer == subject_matter_defined_in_offer AND statutory_essential_terms_defined_in_offer AND party_declared_essential_terms_defined_in_offer",
            "valid_offer == proposal_made AND proposal_addressed_to_counterparty AND intent_to_be_bound AND essential_terms_defined_in_offer",
            "express_acceptance_valid == valid_offer AND acceptance_received AND acceptance_full_and_unconditional AND acceptance_within_period AND NOT acceptance_on_other_terms",
            "conduct_acceptance_valid == valid_offer AND acceptance_by_conduct AND performance_conduct_started_in_time AND NOT acceptance_on_other_terms",
            "silence_acceptance_valid == valid_offer AND silence_only AND silence_acceptance_basis_exists AND acceptance_within_period",
            "counteroffer_detected == acceptance_on_other_terms",
            "essential_terms_agreed == valid_offer AND (express_acceptance_valid OR conduct_acceptance_valid OR silence_acceptance_valid)",
            "contract_concluded_prerequisites == required_form_observed AND essential_terms_agreed",
            "non_conclusion_objection_barred == performance_accepted_without_objection AND bad_faith_non_conclusion_objection",
        ],
    )


def evaluate_formation_constraints(
    constraint_set: FormationConstraintSet,
    facts: FormationFactSet,
) -> FormationEvaluation:
    variables = {field_name: Bool(field_name) for field_name in FormationFactSet.model_fields}
    essential_terms_defined_in_offer = Bool("essential_terms_defined_in_offer")
    essential_terms_agreed = Bool("essential_terms_agreed")
    valid_offer = Bool("valid_offer")
    express_acceptance_valid = Bool("express_acceptance_valid")
    conduct_acceptance_valid = Bool("conduct_acceptance_valid")
    silence_acceptance_valid = Bool("silence_acceptance_valid")
    counteroffer_detected = Bool("counteroffer_detected")
    contract_concluded_prerequisites = Bool("contract_concluded_prerequisites")
    formation_evidence_gap = Bool("formation_evidence_gap")
    non_conclusion_objection_barred = Bool("non_conclusion_objection_barred")
    requires_human_formation_assessment = Bool("requires_human_formation_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        essential_terms_defined_in_offer
        == And(
            variables["subject_matter_defined_in_offer"],
            variables["statutory_essential_terms_defined_in_offer"],
            variables["party_declared_essential_terms_defined_in_offer"],
        )
    )
    solver.add(
        valid_offer
        == And(
            variables["proposal_made"],
            variables["proposal_addressed_to_counterparty"],
            variables["intent_to_be_bound"],
            essential_terms_defined_in_offer,
        )
    )
    solver.add(
        express_acceptance_valid
        == And(
            valid_offer,
            variables["acceptance_received"],
            variables["acceptance_full_and_unconditional"],
            variables["acceptance_within_period"],
            Not(variables["acceptance_on_other_terms"]),
        )
    )
    solver.add(
        conduct_acceptance_valid
        == And(
            valid_offer,
            variables["acceptance_by_conduct"],
            variables["performance_conduct_started_in_time"],
            Not(variables["acceptance_on_other_terms"]),
        )
    )
    solver.add(
        silence_acceptance_valid
        == And(
            valid_offer,
            variables["silence_only"],
            variables["silence_acceptance_basis_exists"],
            variables["acceptance_within_period"],
        )
    )
    solver.add(counteroffer_detected == variables["acceptance_on_other_terms"])
    solver.add(
        essential_terms_agreed
        == And(
            valid_offer,
            Or(express_acceptance_valid, conduct_acceptance_valid, silence_acceptance_valid),
        )
    )
    solver.add(
        contract_concluded_prerequisites
        == And(
            variables["required_form_observed"],
            essential_terms_agreed,
        )
    )
    solver.add(
        formation_evidence_gap
        == And(
            variables["proposal_made"],
            Not(contract_concluded_prerequisites),
        )
    )
    solver.add(
        non_conclusion_objection_barred
        == And(
            variables["performance_accepted_without_objection"],
            variables["bad_faith_non_conclusion_objection"],
        )
    )
    solver.add(
        requires_human_formation_assessment
        == Or(formation_evidence_gap, counteroffer_detected, non_conclusion_objection_barred)
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return FormationEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            essential_terms_defined_in_offer=False,
            essential_terms_agreed=False,
            valid_offer=False,
            express_acceptance_valid=False,
            conduct_acceptance_valid=False,
            silence_acceptance_valid=False,
            counteroffer_detected=False,
            contract_concluded_prerequisites=False,
            formation_evidence_gap=True,
            non_conclusion_objection_barred=False,
            requires_human_formation_assessment=True,
            reasons_ru=["Набор фактов о заключении договора противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    concluded = truth(contract_concluded_prerequisites)
    reasons_ru = [
        (
            "Формальные предпосылки заключения договора подтверждены."
            if concluded
            else "Полный набор формальных предпосылок заключения договора не подтвержден."
        ),
        (
            "Акцепт подтвержден действиями по исполнению в установленный срок."
            if truth(conduct_acceptance_valid)
            else "Акцепт действиями в установленный срок не подтвержден."
        ),
    ]
    if truth(counteroffer_detected):
        reasons_ru.append("Ответ на иных условиях квалифицирован как встречная оферта.")
    if truth(non_conclusion_objection_barred):
        reasons_ru.append(
            "Зафиксированы формальные предпосылки для отклонения недобросовестного возражения о незаключенности."
        )
    return FormationEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        essential_terms_defined_in_offer=truth(essential_terms_defined_in_offer),
        essential_terms_agreed=truth(essential_terms_agreed),
        valid_offer=truth(valid_offer),
        express_acceptance_valid=truth(express_acceptance_valid),
        conduct_acceptance_valid=truth(conduct_acceptance_valid),
        silence_acceptance_valid=truth(silence_acceptance_valid),
        counteroffer_detected=truth(counteroffer_detected),
        contract_concluded_prerequisites=concluded,
        formation_evidence_gap=truth(formation_evidence_gap),
        non_conclusion_objection_barred=truth(non_conclusion_objection_barred),
        requires_human_formation_assessment=truth(requires_human_formation_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные предпосылки и не устанавливает судебный факт заключения договора.",
            "Содержание переписки, поведение сторон и соблюдение формы оцениваются экспертом.",
        ],
    )
