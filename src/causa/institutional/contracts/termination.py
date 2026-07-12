from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


TERMINATION_EVIDENCE_SCHEMA_VERSION = "contracts.termination-evidence.v0"
TERMINATION_MAPPING_VERSION = "contracts-reviewed-termination-to-facts-v0"
TERMINATION_MODEL_VERSION = "contracts-change-termination-articles-450-453-v0"


class TerminationEvidencePredicate(str, Enum):
    CONTRACT_FORMED = "contract_formed"
    MUTUAL_AGREEMENT_REACHED = "mutual_agreement_reached"
    AGREEMENT_TARGETS_MODIFICATION = "agreement_targets_modification"
    AGREEMENT_TARGETS_TERMINATION = "agreement_targets_termination"
    AGREEMENT_FORM_OBSERVED = "agreement_form_observed"
    AGREEMENT_EFFECTIVE_DATE_REACHED = "agreement_effective_date_reached"
    JUDICIAL_REQUEST_MADE = "judicial_request_made"
    JUDICIAL_REQUEST_TARGETS_MODIFICATION = "judicial_request_targets_modification"
    JUDICIAL_REQUEST_TARGETS_TERMINATION = "judicial_request_targets_termination"
    SUBSTANTIAL_BREACH_CLAIMED = "substantial_breach_claimed"
    SUBSTANTIAL_BREACH_PROVEN = "substantial_breach_proven"
    EXPECTATION_DEPRIVATION_PROVEN = "expectation_deprivation_proven"
    OTHER_LEGAL_OR_CONTRACTUAL_GROUND_PROVEN = "other_legal_or_contractual_ground_proven"
    PRETRIAL_PROPOSAL_DELIVERED = "pretrial_proposal_delivered"
    PRETRIAL_REFUSAL_RECEIVED = "pretrial_refusal_received"
    PRETRIAL_RESPONSE_PERIOD_EXPIRED = "pretrial_response_period_expired"
    COURT_DECISION_ENTERED_INTO_FORCE = "court_decision_entered_into_force"
    UNILATERAL_ACTION_DECLARED = "unilateral_action_declared"
    UNILATERAL_ACTION_TARGETS_MODIFICATION = "unilateral_action_targets_modification"
    UNILATERAL_ACTION_TARGETS_TERMINATION = "unilateral_action_targets_termination"
    UNILATERAL_RIGHT_EXISTS = "unilateral_right_exists"
    UNILATERAL_NOTICE_DELIVERED = "unilateral_notice_delivered"
    UNILATERAL_REQUIREMENTS_OBSERVED = "unilateral_requirements_observed"
    UNILATERAL_EXERCISE_GOOD_FAITH = "unilateral_exercise_good_faith"
    SAME_GROUND_PREVIOUSLY_WAIVED = "same_ground_previously_waived"
    CIRCUMSTANCES_SUBSTANTIALLY_CHANGED = "circumstances_substantially_changed"
    CHANGE_UNFORESEEABLE_AT_CONCLUSION = "change_unforeseeable_at_conclusion"
    CAUSES_NOT_OVERCOME_WITH_DUE_CARE = "causes_not_overcome_with_due_care"
    CONTINUED_PERFORMANCE_UPSETS_BALANCE = "continued_performance_upsets_balance"
    CHANGED_CIRCUMSTANCES_RISK_NOT_ASSUMED = "changed_circumstances_risk_not_assumed"
    ADJUSTMENT_NEGOTIATIONS_FAILED = "adjustment_negotiations_failed"
    EXCEPTIONAL_MODIFICATION_PREFERRED = "exceptional_modification_preferred"
    ACCRUED_CLAIMS_EXIST = "accrued_claims_exist"
    COUNTERPERFORMANCE_IMBALANCE_PROVEN = "counterperformance_imbalance_proven"
    TERMINATION_LOSSES_CLAIMED = "termination_losses_claimed"
    TERMINATION_LOSSES_CAUSALLY_LINKED = "termination_losses_causally_linked"


REQUIRED_TERMINATION_PREDICATES = frozenset(TerminationEvidencePredicate)


class TerminationEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: TerminationEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedTerminationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = TERMINATION_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[TerminationEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedTerminationEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Termination evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Termination evidence contains duplicate legal source refs.")
        return self


class TerminationFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_formed: bool
    mutual_agreement_reached: bool
    agreement_targets_modification: bool
    agreement_targets_termination: bool
    agreement_form_observed: bool
    agreement_effective_date_reached: bool
    judicial_request_made: bool
    judicial_request_targets_modification: bool
    judicial_request_targets_termination: bool
    substantial_breach_claimed: bool
    substantial_breach_proven: bool
    expectation_deprivation_proven: bool
    other_legal_or_contractual_ground_proven: bool
    pretrial_proposal_delivered: bool
    pretrial_refusal_received: bool
    pretrial_response_period_expired: bool
    court_decision_entered_into_force: bool
    unilateral_action_declared: bool
    unilateral_action_targets_modification: bool
    unilateral_action_targets_termination: bool
    unilateral_right_exists: bool
    unilateral_notice_delivered: bool
    unilateral_requirements_observed: bool
    unilateral_exercise_good_faith: bool
    same_ground_previously_waived: bool
    circumstances_substantially_changed: bool
    change_unforeseeable_at_conclusion: bool
    causes_not_overcome_with_due_care: bool
    continued_performance_upsets_balance: bool
    changed_circumstances_risk_not_assumed: bool
    adjustment_negotiations_failed: bool
    exceptional_modification_preferred: bool
    accrued_claims_exist: bool
    counterperformance_imbalance_proven: bool
    termination_losses_claimed: bool
    termination_losses_causally_linked: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "TerminationFactSet":
        self._validate_target_pair(
            self.mutual_agreement_reached,
            self.agreement_targets_modification,
            self.agreement_targets_termination,
            "Mutual agreement",
        )
        self._validate_target_pair(
            self.judicial_request_made,
            self.judicial_request_targets_modification,
            self.judicial_request_targets_termination,
            "Judicial request",
        )
        self._validate_target_pair(
            self.unilateral_action_declared,
            self.unilateral_action_targets_modification,
            self.unilateral_action_targets_termination,
            "Unilateral action",
        )
        if self.agreement_effective_date_reached and not self.mutual_agreement_reached:
            raise ValueError("Agreement effective date requires a mutual agreement.")
        if self.substantial_breach_proven and not (
            self.substantial_breach_claimed and self.expectation_deprivation_proven
        ):
            raise ValueError(
                "Proven substantial breach requires a claim and expectation deprivation."
            )
        if self.expectation_deprivation_proven and not self.substantial_breach_claimed:
            raise ValueError("Expectation deprivation requires a substantial-breach claim.")
        if (self.pretrial_refusal_received or self.pretrial_response_period_expired) and not (
            self.pretrial_proposal_delivered
        ):
            raise ValueError("Pretrial response facts require a delivered proposal.")
        if self.court_decision_entered_into_force and not self.judicial_request_made:
            raise ValueError("An effective court decision requires a judicial request.")
        if self.unilateral_notice_delivered and not self.unilateral_action_declared:
            raise ValueError("Delivered unilateral notice requires a declared action.")
        if self.same_ground_previously_waived and not self.unilateral_action_declared:
            raise ValueError("Waiver on the same ground requires a unilateral action.")
        if self.exceptional_modification_preferred and not (
            self.circumstances_substantially_changed
        ):
            raise ValueError("Exceptional modification requires changed circumstances.")
        if self.termination_losses_causally_linked and not self.termination_losses_claimed:
            raise ValueError("Causally linked termination losses require a losses claim.")
        return self

    @staticmethod
    def _validate_target_pair(
        trigger: bool,
        modification: bool,
        termination: bool,
        label: str,
    ) -> None:
        if trigger and modification == termination:
            raise ValueError(f"{label} must target exactly one legal effect.")
        if not trigger and (modification or termination):
            raise ValueError(f"{label} target requires its triggering action.")


class TerminationFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class TerminationEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: TerminationFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[TerminationFactProvenance] = Field(default_factory=list)


class TerminationConstraintSet(BaseModel):
    id: str
    model_version: str = TERMINATION_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class TerminationEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    substantial_breach_ground_satisfied: bool
    changed_circumstances_ground_satisfied: bool
    pretrial_order_satisfied: bool
    mutual_modification_effective: bool
    mutual_termination_effective: bool
    judicial_modification_prerequisites: bool
    judicial_termination_prerequisites: bool
    judicial_modification_effective: bool
    judicial_termination_effective: bool
    unilateral_modification_effective: bool
    unilateral_termination_effective: bool
    invalid_unilateral_action: bool
    effective_modification: bool
    effective_termination: bool
    competing_effective_paths: bool
    contract_continues_unchanged: bool
    future_obligations_terminated: bool
    accrued_claims_preserved: bool
    restitution_issue: bool
    termination_losses_issue: bool
    requires_human_termination_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_termination_evidence(
    evidence: ReviewedTerminationEvidence,
) -> TerminationEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Termination evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Termination evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_TERMINATION_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed termination evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_TERMINATION_PREDICATES
    }
    return TerminationEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=TERMINATION_MAPPING_VERSION,
        facts=TerminationFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            TerminationFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_TERMINATION_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_termination_constraint_set(
    mapping: TerminationEvidenceMappingResult,
) -> TerminationConstraintSet:
    return TerminationConstraintSet(
        id=f"termination-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "substantial_breach_ground_satisfied == substantial_breach_claimed AND substantial_breach_proven AND expectation_deprivation_proven",
            "changed_circumstances_ground_satisfied == circumstances_substantially_changed AND change_unforeseeable_at_conclusion AND causes_not_overcome_with_due_care AND continued_performance_upsets_balance AND changed_circumstances_risk_not_assumed AND adjustment_negotiations_failed",
            "pretrial_order_satisfied == pretrial_proposal_delivered AND (pretrial_refusal_received OR pretrial_response_period_expired)",
            "mutual_effect == contract_formed AND mutual_agreement_reached AND agreement_form_observed AND agreement_effective_date_reached",
            "judicial_ground == substantial_breach_ground_satisfied OR other_legal_or_contractual_ground_proven OR changed_circumstances_ground_satisfied",
            "judicial_modification_prerequisites == contract_formed AND judicial_request_targets_modification AND pretrial_order_satisfied AND (substantial_breach_ground_satisfied OR other_legal_or_contractual_ground_proven OR (changed_circumstances_ground_satisfied AND exceptional_modification_preferred))",
            "judicial_termination_prerequisites == contract_formed AND judicial_request_targets_termination AND pretrial_order_satisfied AND judicial_ground",
            "judicial_effect == judicial_prerequisites AND court_decision_entered_into_force",
            "unilateral_effect == contract_formed AND unilateral_right_exists AND unilateral_notice_delivered AND unilateral_requirements_observed AND unilateral_exercise_good_faith AND NOT same_ground_previously_waived",
            "invalid_unilateral_action == unilateral_action_declared AND NOT (unilateral_modification_effective OR unilateral_termination_effective)",
            "effective_modification == mutual_modification_effective OR judicial_modification_effective OR unilateral_modification_effective",
            "effective_termination == mutual_termination_effective OR judicial_termination_effective OR unilateral_termination_effective",
            "contract_continues_unchanged == contract_formed AND NOT effective_modification AND NOT effective_termination",
            "accrued_claims_preserved == effective_termination AND accrued_claims_exist",
            "restitution_issue == effective_termination AND counterperformance_imbalance_proven",
            "termination_losses_issue == effective_termination AND substantial_breach_ground_satisfied AND termination_losses_claimed AND termination_losses_causally_linked",
        ],
    )


def evaluate_termination_constraints(
    constraint_set: TerminationConstraintSet,
    facts: TerminationFactSet,
) -> TerminationEvaluation:
    variables = {field_name: Bool(field_name) for field_name in TerminationFactSet.model_fields}
    outputs = {
        field_name: Bool(field_name)
        for field_name in TerminationEvaluation.model_fields
        if field_name
        not in {
            "constraint_set_id",
            "satisfiable",
            "reasons_ru",
            "warnings_ru",
        }
    }
    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    breach_ground = outputs["substantial_breach_ground_satisfied"]
    changed_ground = outputs["changed_circumstances_ground_satisfied"]
    pretrial = outputs["pretrial_order_satisfied"]
    solver.add(
        breach_ground
        == And(
            variables["substantial_breach_claimed"],
            variables["substantial_breach_proven"],
            variables["expectation_deprivation_proven"],
        )
    )
    solver.add(
        changed_ground
        == And(
            variables["circumstances_substantially_changed"],
            variables["change_unforeseeable_at_conclusion"],
            variables["causes_not_overcome_with_due_care"],
            variables["continued_performance_upsets_balance"],
            variables["changed_circumstances_risk_not_assumed"],
            variables["adjustment_negotiations_failed"],
        )
    )
    solver.add(
        pretrial
        == And(
            variables["pretrial_proposal_delivered"],
            Or(
                variables["pretrial_refusal_received"],
                variables["pretrial_response_period_expired"],
            ),
        )
    )
    mutual_common = And(
        variables["contract_formed"],
        variables["mutual_agreement_reached"],
        variables["agreement_form_observed"],
        variables["agreement_effective_date_reached"],
    )
    solver.add(
        outputs["mutual_modification_effective"]
        == And(mutual_common, variables["agreement_targets_modification"])
    )
    solver.add(
        outputs["mutual_termination_effective"]
        == And(mutual_common, variables["agreement_targets_termination"])
    )
    judicial_ground = Or(
        breach_ground,
        variables["other_legal_or_contractual_ground_proven"],
        changed_ground,
    )
    solver.add(
        outputs["judicial_modification_prerequisites"]
        == And(
            variables["contract_formed"],
            variables["judicial_request_made"],
            variables["judicial_request_targets_modification"],
            pretrial,
            Or(
                breach_ground,
                variables["other_legal_or_contractual_ground_proven"],
                And(changed_ground, variables["exceptional_modification_preferred"]),
            ),
        )
    )
    solver.add(
        outputs["judicial_termination_prerequisites"]
        == And(
            variables["contract_formed"],
            variables["judicial_request_made"],
            variables["judicial_request_targets_termination"],
            pretrial,
            judicial_ground,
        )
    )
    solver.add(
        outputs["judicial_modification_effective"]
        == And(
            outputs["judicial_modification_prerequisites"],
            variables["court_decision_entered_into_force"],
        )
    )
    solver.add(
        outputs["judicial_termination_effective"]
        == And(
            outputs["judicial_termination_prerequisites"],
            variables["court_decision_entered_into_force"],
        )
    )
    unilateral_common = And(
        variables["contract_formed"],
        variables["unilateral_action_declared"],
        variables["unilateral_right_exists"],
        variables["unilateral_notice_delivered"],
        variables["unilateral_requirements_observed"],
        variables["unilateral_exercise_good_faith"],
        Not(variables["same_ground_previously_waived"]),
    )
    solver.add(
        outputs["unilateral_modification_effective"]
        == And(unilateral_common, variables["unilateral_action_targets_modification"])
    )
    solver.add(
        outputs["unilateral_termination_effective"]
        == And(unilateral_common, variables["unilateral_action_targets_termination"])
    )
    solver.add(
        outputs["invalid_unilateral_action"]
        == And(
            variables["unilateral_action_declared"],
            Not(
                Or(
                    outputs["unilateral_modification_effective"],
                    outputs["unilateral_termination_effective"],
                )
            ),
        )
    )
    solver.add(
        outputs["effective_modification"]
        == Or(
            outputs["mutual_modification_effective"],
            outputs["judicial_modification_effective"],
            outputs["unilateral_modification_effective"],
        )
    )
    solver.add(
        outputs["effective_termination"]
        == Or(
            outputs["mutual_termination_effective"],
            outputs["judicial_termination_effective"],
            outputs["unilateral_termination_effective"],
        )
    )
    solver.add(
        outputs["competing_effective_paths"]
        == And(outputs["effective_modification"], outputs["effective_termination"])
    )
    solver.add(
        outputs["contract_continues_unchanged"]
        == And(
            variables["contract_formed"],
            Not(outputs["effective_modification"]),
            Not(outputs["effective_termination"]),
        )
    )
    solver.add(outputs["future_obligations_terminated"] == outputs["effective_termination"])
    solver.add(
        outputs["accrued_claims_preserved"]
        == And(outputs["effective_termination"], variables["accrued_claims_exist"])
    )
    solver.add(
        outputs["restitution_issue"]
        == And(
            outputs["effective_termination"],
            variables["counterperformance_imbalance_proven"],
        )
    )
    solver.add(
        outputs["termination_losses_issue"]
        == And(
            outputs["effective_termination"],
            breach_ground,
            variables["termination_losses_claimed"],
            variables["termination_losses_causally_linked"],
        )
    )
    mutual_gap = And(
        variables["mutual_agreement_reached"],
        Not(
            Or(
                outputs["mutual_modification_effective"],
                outputs["mutual_termination_effective"],
            )
        ),
    )
    solver.add(
        outputs["requires_human_termination_assessment"]
        == Or(
            variables["judicial_request_made"],
            variables["circumstances_substantially_changed"],
            outputs["invalid_unilateral_action"],
            mutual_gap,
            outputs["effective_modification"],
            outputs["effective_termination"],
            outputs["competing_effective_paths"],
            outputs["restitution_issue"],
            outputs["termination_losses_issue"],
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return TerminationEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            **{
                field_name: False
                for field_name in outputs
                if field_name != "requires_human_termination_assessment"
            },
            requires_human_termination_assessment=True,
            reasons_ru=["Набор фактов об изменении или расторжении договора противоречив."],
            warnings_ru=["Требуется повторная проверка исходных данных юристом."],
        )
    model = solver.model()
    values = {
        field_name: bool(model.eval(variable, model_completion=True))
        for field_name, variable in outputs.items()
    }
    reasons_ru = [
        (
            "Договор прекращен по подтвержденному формальному пути."
            if values["effective_termination"]
            else "Состоявшееся прекращение договора формальной моделью не установлено."
        ),
        (
            "Установлено вступившее в силу изменение договора."
            if values["effective_modification"]
            else "Вступившее в силу изменение договора не установлено."
        ),
    ]
    if values["judicial_termination_prerequisites"]:
        reasons_ru.append(
            "Подтвержден узкий набор предпосылок для судебного требования о расторжении."
        )
    if values["invalid_unilateral_action"]:
        reasons_ru.append(
            "Одностороннее действие не прошло проверку права, уведомления, требований или добросовестности."
        )
    if values["contract_continues_unchanged"]:
        reasons_ru.append("Договор продолжает действовать без подтвержденного изменения.")
    return TerminationEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        **values,
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель не подменяет судебную оценку существенности нарушения и изменения обстоятельств.",
            "Специальные правила отдельных видов договоров должны проверяться отдельно.",
            "Момент доставки уведомления и вступления решения в силу устанавливается по доказательствам.",
        ],
    )
