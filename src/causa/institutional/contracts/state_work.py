from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


STATE_WORK_EVIDENCE_SCHEMA_VERSION = "contracts.state-work-evidence.v0"
STATE_WORK_MAPPING_VERSION = "contracts-reviewed-state-work-to-facts-v0"
STATE_WORK_MODEL_VERSION = "contracts-state-work-articles-763-768-v0"


class StateWorkEvidencePredicate(str, Enum):
    # Основания выполнения работ и стороны контракта (статьи 763–765 ГК РФ).
    WORK_FOR_STATE_OR_MUNICIPAL_NEEDS = "work_for_state_or_municipal_needs"
    STATE_CONTRACT_NOT_CONCLUDED = "state_contract_not_concluded"
    CUSTOMER_NOT_AUTHORIZED_BUDGET_RECIPIENT = "customer_not_authorized_budget_recipient"
    CONTRACT_CONCLUSION_PROCEDURE_BREACHED = "contract_conclusion_procedure_breached"
    # Содержание государственного или муниципального контракта (статья 766 ГК РФ).
    SCOPE_OR_COST_TERMS_NOT_AGREED = "scope_or_cost_terms_not_agreed"
    START_OR_COMPLETION_DATES_NOT_AGREED = "start_or_completion_dates_not_agreed"
    FUNDING_AND_PAYMENT_TERMS_NOT_AGREED = "funding_and_payment_terms_not_agreed"
    PERFORMANCE_SECURITY_NOT_AGREED = "performance_security_not_agreed"
    # Изменение контракта при уменьшении бюджетных средств (статья 767 ГК РФ).
    BUDGET_REDUCED_WITHOUT_AGREED_NEW_TERMS = "budget_reduced_without_agreed_new_terms"
    CONTRACTOR_LOSSES_FROM_CHANGED_TERMS_NOT_COMPENSATED = (
        "contractor_losses_from_changed_terms_not_compensated"
    )


REQUIRED_STATE_WORK_PREDICATES = frozenset(StateWorkEvidencePredicate)


class StateWorkEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: StateWorkEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedStateWorkEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = STATE_WORK_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[StateWorkEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedStateWorkEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("State-work evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("State-work evidence contains duplicate legal source refs.")
        return self


class StateWorkFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    work_for_state_or_municipal_needs: bool
    state_contract_not_concluded: bool
    customer_not_authorized_budget_recipient: bool
    contract_conclusion_procedure_breached: bool
    scope_or_cost_terms_not_agreed: bool
    start_or_completion_dates_not_agreed: bool
    funding_and_payment_terms_not_agreed: bool
    performance_security_not_agreed: bool
    budget_reduced_without_agreed_new_terms: bool
    contractor_losses_from_changed_terms_not_compensated: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "StateWorkFactSet":
        if self.contractor_losses_from_changed_terms_not_compensated and not (
            self.budget_reduced_without_agreed_new_terms
        ):
            raise ValueError(
                "Невозмещение убытков, вызванных изменением сроков, относится только к случаю, "
                "когда уменьшение бюджетных средств без согласования новых условий установлено."
            )
        if self.state_contract_not_concluded and not self.work_for_state_or_municipal_needs:
            raise ValueError(
                "Отсутствие государственного или муниципального контракта относится только к "
                "работам, предназначенным для удовлетворения государственных или муниципальных "
                "нужд."
            )
        return self


class StateWorkFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class StateWorkEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: StateWorkFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[StateWorkFactProvenance] = Field(default_factory=list)


class StateWorkConstraintSet(BaseModel):
    id: str
    model_version: str = STATE_WORK_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class StateWorkEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    state_work_qualified: bool
    state_contract_requirement_breached: bool
    customer_status_invalid: bool
    conclusion_procedure_breached: bool
    scope_or_cost_terms_missing: bool
    schedule_terms_missing: bool
    funding_terms_missing: bool
    performance_security_missing: bool
    budget_reduction_terms_not_agreed: bool
    contractor_losses_compensation_due: bool
    requires_human_state_work_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_state_work_evidence(
    evidence: ReviewedStateWorkEvidence,
) -> StateWorkEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("State-work evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("State-work evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_STATE_WORK_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed state-work evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_STATE_WORK_PREDICATES
    }
    return StateWorkEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=STATE_WORK_MAPPING_VERSION,
        facts=StateWorkFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            StateWorkFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_STATE_WORK_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_state_work_constraint_set(
    mapping: StateWorkEvidenceMappingResult,
) -> StateWorkConstraintSet:
    return StateWorkConstraintSet(
        id=f"state-work-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "state_work_qualified == work_for_state_or_municipal_needs",
            "state_contract_requirement_breached == state_work_qualified AND state_contract_not_concluded",
            "customer_status_invalid == state_work_qualified AND customer_not_authorized_budget_recipient",
            "conclusion_procedure_breached == state_work_qualified AND contract_conclusion_procedure_breached",
            "scope_or_cost_terms_missing == state_work_qualified AND scope_or_cost_terms_not_agreed",
            "schedule_terms_missing == state_work_qualified AND start_or_completion_dates_not_agreed",
            "funding_terms_missing == state_work_qualified AND funding_and_payment_terms_not_agreed",
            "performance_security_missing == state_work_qualified AND performance_security_not_agreed",
            "budget_reduction_terms_not_agreed == state_work_qualified AND budget_reduced_without_agreed_new_terms",
            "contractor_losses_compensation_due == state_work_qualified AND budget_reduced_without_agreed_new_terms AND contractor_losses_from_changed_terms_not_compensated",
            "requires_human_state_work_assessment == state_contract_requirement_breached OR customer_status_invalid OR conclusion_procedure_breached OR scope_or_cost_terms_missing OR schedule_terms_missing OR funding_terms_missing OR performance_security_missing OR budget_reduction_terms_not_agreed",
        ],
    )


def evaluate_state_work_constraints(
    constraint_set: StateWorkConstraintSet,
    facts: StateWorkFactSet,
) -> StateWorkEvaluation:
    variables = {field_name: Bool(field_name) for field_name in StateWorkFactSet.model_fields}
    state_work_qualified = Bool("state_work_qualified")
    state_contract_requirement_breached = Bool("state_contract_requirement_breached")
    customer_status_invalid = Bool("customer_status_invalid")
    conclusion_procedure_breached = Bool("conclusion_procedure_breached")
    scope_or_cost_terms_missing = Bool("scope_or_cost_terms_missing")
    schedule_terms_missing = Bool("schedule_terms_missing")
    funding_terms_missing = Bool("funding_terms_missing")
    performance_security_missing = Bool("performance_security_missing")
    budget_reduction_terms_not_agreed = Bool("budget_reduction_terms_not_agreed")
    contractor_losses_compensation_due = Bool("contractor_losses_compensation_due")
    requires_human_state_work_assessment = Bool("requires_human_state_work_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(state_work_qualified == variables["work_for_state_or_municipal_needs"])
    solver.add(
        state_contract_requirement_breached
        == And(state_work_qualified, variables["state_contract_not_concluded"])
    )
    solver.add(
        customer_status_invalid
        == And(state_work_qualified, variables["customer_not_authorized_budget_recipient"])
    )
    solver.add(
        conclusion_procedure_breached
        == And(state_work_qualified, variables["contract_conclusion_procedure_breached"])
    )
    solver.add(
        scope_or_cost_terms_missing
        == And(state_work_qualified, variables["scope_or_cost_terms_not_agreed"])
    )
    solver.add(
        schedule_terms_missing
        == And(state_work_qualified, variables["start_or_completion_dates_not_agreed"])
    )
    solver.add(
        funding_terms_missing
        == And(state_work_qualified, variables["funding_and_payment_terms_not_agreed"])
    )
    solver.add(
        performance_security_missing
        == And(state_work_qualified, variables["performance_security_not_agreed"])
    )
    solver.add(
        budget_reduction_terms_not_agreed
        == And(state_work_qualified, variables["budget_reduced_without_agreed_new_terms"])
    )
    solver.add(
        contractor_losses_compensation_due
        == And(
            state_work_qualified,
            variables["budget_reduced_without_agreed_new_terms"],
            variables["contractor_losses_from_changed_terms_not_compensated"],
        )
    )
    solver.add(
        requires_human_state_work_assessment
        == Or(
            state_contract_requirement_breached,
            customer_status_invalid,
            conclusion_procedure_breached,
            scope_or_cost_terms_missing,
            schedule_terms_missing,
            funding_terms_missing,
            performance_security_missing,
            budget_reduction_terms_not_agreed,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return StateWorkEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            state_work_qualified=False,
            state_contract_requirement_breached=False,
            customer_status_invalid=False,
            conclusion_procedure_breached=False,
            scope_or_cost_terms_missing=False,
            schedule_terms_missing=False,
            funding_terms_missing=False,
            performance_security_missing=False,
            budget_reduction_terms_not_agreed=False,
            contractor_losses_compensation_due=False,
            requires_human_state_work_assessment=True,
            reasons_ru=["Набор фактов о подрядных работах для государственных нужд противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Отношения квалифицированы как подрядные работы для государственных или муниципальных "
            "нужд: строительные, проектные и изыскательские работы предназначены удовлетворять "
            "государственные или муниципальные нужды и финансируются за счёт соответствующих "
            "бюджетных средств (статья 763 ГК РФ)."
            if truth(state_work_qualified)
            else (
                "Отношения не квалифицированы как подрядные работы для государственных или "
                "муниципальных нужд."
            )
        ),
    ]
    if truth(state_contract_requirement_breached):
        reasons_ru.append(
            "Подрядные работы для государственных или муниципальных нужд осуществляются на основе "
            "государственного или муниципального контракта на выполнение подрядных работ "
            "(статья 763 ГК РФ)."
        )
    if truth(customer_status_invalid):
        reasons_ru.append(
            "Государственным или муниципальным заказчиком выступают государственные органы, "
            "органы управления государственными внебюджетными фондами, органы местного "
            "самоуправления, казённые учреждения и иные получатели бюджетных средств "
            "(статья 764 ГК РФ)."
        )
    if truth(conclusion_procedure_breached):
        reasons_ru.append(
            "Основания и порядок заключения государственного или муниципального контракта "
            "определяются по правилам о поставке товаров для государственных нужд "
            "(статья 765 ГК РФ со ссылкой на статьи 527 и 528 ГК РФ)."
        )
    if truth(scope_or_cost_terms_missing):
        reasons_ru.append(
            "Государственный или муниципальный контракт должен содержать условия об объёме и о "
            "стоимости подлежащей выполнению работы (статья 766 ГК РФ)."
        )
    if truth(schedule_terms_missing):
        reasons_ru.append(
            "Государственный или муниципальный контракт должен содержать условия о сроках начала "
            "и окончания работы (статья 766 ГК РФ)."
        )
    if truth(funding_terms_missing):
        reasons_ru.append(
            "Государственный или муниципальный контракт должен содержать условия о размере и "
            "порядке финансирования и оплаты работ (статья 766 ГК РФ)."
        )
    if truth(performance_security_missing):
        reasons_ru.append(
            "Государственный или муниципальный контракт должен содержать условия о способах "
            "обеспечения исполнения обязательств сторон (статья 766 ГК РФ)."
        )
    if truth(budget_reduction_terms_not_agreed):
        reasons_ru.append(
            "При уменьшении соответствующими государственными органами или органами местного "
            "самоуправления средств, выделенных для финансирования подрядных работ, стороны "
            "обязаны согласовать новые сроки и при необходимости другие условия выполнения работ "
            "(статья 767 ГК РФ)."
        )
    if truth(contractor_losses_compensation_due):
        reasons_ru.append(
            "Подрядчик вправе требовать возмещения убытков, причинённых изменением сроков "
            "выполнения работ вследствие уменьшения выделенных бюджетных средств "
            "(статья 767 ГК РФ)."
        )
    return StateWorkEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        state_work_qualified=truth(state_work_qualified),
        state_contract_requirement_breached=truth(state_contract_requirement_breached),
        customer_status_invalid=truth(customer_status_invalid),
        conclusion_procedure_breached=truth(conclusion_procedure_breached),
        scope_or_cost_terms_missing=truth(scope_or_cost_terms_missing),
        schedule_terms_missing=truth(schedule_terms_missing),
        funding_terms_missing=truth(funding_terms_missing),
        performance_security_missing=truth(performance_security_missing),
        budget_reduction_terms_not_agreed=truth(budget_reduction_terms_not_agreed),
        contractor_losses_compensation_due=truth(contractor_losses_compensation_due),
        requires_human_state_work_assessment=truth(requires_human_state_work_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о подрядных работах для государственных и "
            "муниципальных нужд и не заменяет судебную оценку.",
            "Достаточность бюджетного финансирования, соблюдение закупочных процедур и размер "
            "убытков подрядчика оцениваются экспертом и судом (статьи 765, 767 и 768 ГК РФ).",
        ],
    )
