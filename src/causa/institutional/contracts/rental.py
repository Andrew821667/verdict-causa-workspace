from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


RENTAL_EVIDENCE_SCHEMA_VERSION = "contracts.rental-evidence.v0"
RENTAL_MAPPING_VERSION = "contracts-reviewed-rental-to-facts-v0"
RENTAL_MODEL_VERSION = "contracts-rental-articles-626-631-v0"


class RentalEvidencePredicate(str, Enum):
    # Понятие, форма и срок проката (статьи 626 и 627 ГК РФ).
    MOVABLE_PROPERTY_RENTED_BY_PROFESSIONAL_LESSOR = (
        "movable_property_rented_by_professional_lessor"
    )
    WRITTEN_FORM_MISSING = "written_form_missing"
    LEASE_TERM_EXCEEDS_ONE_YEAR = "lease_term_exceeds_one_year"
    RENEWAL_OR_PRIORITY_RIGHT_CLAIMED = "renewal_or_priority_right_claimed"
    # Недостатки предмета проката (статьи 628 и 629 ГК РФ).
    DEFECT_PRESENT = "defect_present"
    DEFECT_FROM_TENANT_MISUSE = "defect_from_tenant_misuse"
    LESSOR_FAILED_TO_REMEDY_DEFECT = "lessor_failed_to_remedy_defect"
    # Плата, ремонт и распоряжение (статьи 630 и 631 ГК РФ).
    EARLY_RETURN_REFUND_DENIED = "early_return_refund_denied"
    REPAIR_OBLIGATION_NEGLECTED = "repair_obligation_neglected"
    SUBLEASE_OR_RIGHTS_TRANSFER_ATTEMPTED = "sublease_or_rights_transfer_attempted"


REQUIRED_RENTAL_PREDICATES = frozenset(RentalEvidencePredicate)


class RentalEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: RentalEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedRentalEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = RENTAL_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[RentalEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedRentalEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Rental evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Rental evidence contains duplicate legal source refs.")
        return self


class RentalFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    movable_property_rented_by_professional_lessor: bool
    written_form_missing: bool
    lease_term_exceeds_one_year: bool
    renewal_or_priority_right_claimed: bool
    defect_present: bool
    defect_from_tenant_misuse: bool
    lessor_failed_to_remedy_defect: bool
    early_return_refund_denied: bool
    repair_obligation_neglected: bool
    sublease_or_rights_transfer_attempted: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "RentalFactSet":
        if self.defect_from_tenant_misuse and not self.defect_present:
            raise ValueError(
                "Нарушение арендатором правил эксплуатации относится только к обнаруженным "
                "недостаткам предмета проката."
            )
        if self.lessor_failed_to_remedy_defect and not self.defect_present:
            raise ValueError(
                "Неустранение недостатка арендодателем относится только к обнаруженным "
                "недостаткам предмета проката."
            )
        if self.lessor_failed_to_remedy_defect and self.defect_from_tenant_misuse:
            raise ValueError(
                "Устранение недостатка за счёт арендодателя не применяется, если недостаток "
                "вызван нарушением арендатором правил эксплуатации."
            )
        return self


class RentalFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class RentalEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: RentalFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[RentalFactProvenance] = Field(default_factory=list)


class RentalConstraintSet(BaseModel):
    id: str
    model_version: str = RENTAL_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class RentalEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    rental_qualified: bool
    form_requirement_violated: bool
    term_limit_exceeded: bool
    renewal_right_not_available: bool
    tenant_bears_defect_cost: bool
    defect_remedy_overdue: bool
    early_return_refund_due: bool
    repair_obligation_breached: bool
    transfer_restriction_violated: bool
    requires_human_rental_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_rental_evidence(
    evidence: ReviewedRentalEvidence,
) -> RentalEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Rental evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Rental evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_RENTAL_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed rental evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_RENTAL_PREDICATES
    }
    return RentalEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=RENTAL_MAPPING_VERSION,
        facts=RentalFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            RentalFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_RENTAL_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_rental_constraint_set(
    mapping: RentalEvidenceMappingResult,
) -> RentalConstraintSet:
    return RentalConstraintSet(
        id=f"rental-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "rental_qualified == movable_property_rented_by_professional_lessor",
            "form_requirement_violated == rental_qualified AND written_form_missing",
            "term_limit_exceeded == rental_qualified AND lease_term_exceeds_one_year",
            "renewal_right_not_available == rental_qualified AND renewal_or_priority_right_claimed",
            "tenant_bears_defect_cost == rental_qualified AND defect_present AND defect_from_tenant_misuse",
            "defect_remedy_overdue == rental_qualified AND defect_present AND lessor_failed_to_remedy_defect",
            "early_return_refund_due == rental_qualified AND early_return_refund_denied",
            "repair_obligation_breached == rental_qualified AND repair_obligation_neglected",
            "transfer_restriction_violated == rental_qualified AND sublease_or_rights_transfer_attempted",
            "requires_human_rental_assessment == form_requirement_violated OR term_limit_exceeded OR renewal_right_not_available OR tenant_bears_defect_cost OR defect_remedy_overdue OR early_return_refund_due OR repair_obligation_breached OR transfer_restriction_violated",
        ],
    )


def evaluate_rental_constraints(
    constraint_set: RentalConstraintSet,
    facts: RentalFactSet,
) -> RentalEvaluation:
    variables = {field_name: Bool(field_name) for field_name in RentalFactSet.model_fields}
    rental_qualified = Bool("rental_qualified")
    form_requirement_violated = Bool("form_requirement_violated")
    term_limit_exceeded = Bool("term_limit_exceeded")
    renewal_right_not_available = Bool("renewal_right_not_available")
    tenant_bears_defect_cost = Bool("tenant_bears_defect_cost")
    defect_remedy_overdue = Bool("defect_remedy_overdue")
    early_return_refund_due = Bool("early_return_refund_due")
    repair_obligation_breached = Bool("repair_obligation_breached")
    transfer_restriction_violated = Bool("transfer_restriction_violated")
    requires_human_rental_assessment = Bool("requires_human_rental_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(rental_qualified == variables["movable_property_rented_by_professional_lessor"])
    solver.add(
        form_requirement_violated == And(rental_qualified, variables["written_form_missing"])
    )
    solver.add(
        term_limit_exceeded == And(rental_qualified, variables["lease_term_exceeds_one_year"])
    )
    solver.add(
        renewal_right_not_available
        == And(rental_qualified, variables["renewal_or_priority_right_claimed"])
    )
    solver.add(
        tenant_bears_defect_cost
        == And(
            rental_qualified,
            variables["defect_present"],
            variables["defect_from_tenant_misuse"],
        )
    )
    solver.add(
        defect_remedy_overdue
        == And(
            rental_qualified,
            variables["defect_present"],
            variables["lessor_failed_to_remedy_defect"],
        )
    )
    solver.add(
        early_return_refund_due == And(rental_qualified, variables["early_return_refund_denied"])
    )
    solver.add(
        repair_obligation_breached
        == And(rental_qualified, variables["repair_obligation_neglected"])
    )
    solver.add(
        transfer_restriction_violated
        == And(rental_qualified, variables["sublease_or_rights_transfer_attempted"])
    )
    solver.add(
        requires_human_rental_assessment
        == Or(
            form_requirement_violated,
            term_limit_exceeded,
            renewal_right_not_available,
            tenant_bears_defect_cost,
            defect_remedy_overdue,
            early_return_refund_due,
            repair_obligation_breached,
            transfer_restriction_violated,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return RentalEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            rental_qualified=False,
            form_requirement_violated=False,
            term_limit_exceeded=False,
            renewal_right_not_available=False,
            tenant_bears_defect_cost=False,
            defect_remedy_overdue=False,
            early_return_refund_due=False,
            repair_obligation_breached=False,
            transfer_restriction_violated=False,
            requires_human_rental_assessment=True,
            reasons_ru=["Набор фактов о прокате противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как прокат: арендодатель, сдающий имущество в аренду как "
            "постоянную предпринимательскую деятельность, предоставил арендатору движимое "
            "имущество за плату во временное владение и пользование (статья 626 ГК РФ)."
            if truth(rental_qualified)
            else "Отношения не квалифицированы как договор проката."
        ),
    ]
    if truth(form_requirement_violated):
        reasons_ru.append(
            "Договор проката должен быть заключён в письменной форме; требование формы нарушено "
            "(статья 626 ГК РФ)."
        )
    if truth(term_limit_exceeded):
        reasons_ru.append(
            "Договор проката заключается на срок до одного года; согласованный срок превышает "
            "предельный (статья 627 ГК РФ)."
        )
    if truth(renewal_right_not_available):
        reasons_ru.append(
            "К договору проката не применяются правила о преимущественном праве на возобновление "
            "и о возобновлении на неопределённый срок (статья 627 ГК РФ)."
        )
    if truth(tenant_bears_defect_cost):
        reasons_ru.append(
            "Недостатки возникли вследствие нарушения арендатором правил эксплуатации; арендатор "
            "оплачивает стоимость ремонта и транспортировки имущества (статья 629 ГК РФ)."
        )
    if truth(defect_remedy_overdue):
        reasons_ru.append(
            "Арендодатель не устранил недостатки и не заменил имущество в десятидневный срок со "
            "дня заявления арендатора о недостатках (статья 629 ГК РФ)."
        )
    if truth(early_return_refund_due):
        reasons_ru.append(
            "При досрочном возврате имущества арендодатель обязан возвратить арендатору "
            "соответствующую часть внесённой арендной платы (статья 630 ГК РФ)."
        )
    if truth(repair_obligation_breached):
        reasons_ru.append(
            "Капитальный и текущий ремонт сданного в прокат имущества являются обязанностью "
            "арендодателя (статья 631 ГК РФ)."
        )
    if truth(transfer_restriction_violated):
        reasons_ru.append(
            "Сдача имущества в субаренду, передача прав по договору проката, залог и внесение "
            "его в качестве вклада не допускаются (статья 631 ГК РФ)."
        )
    return RentalEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        rental_qualified=truth(rental_qualified),
        form_requirement_violated=truth(form_requirement_violated),
        term_limit_exceeded=truth(term_limit_exceeded),
        renewal_right_not_available=truth(renewal_right_not_available),
        tenant_bears_defect_cost=truth(tenant_bears_defect_cost),
        defect_remedy_overdue=truth(defect_remedy_overdue),
        early_return_refund_due=truth(early_return_refund_due),
        repair_obligation_breached=truth(repair_obligation_breached),
        transfer_restriction_violated=truth(transfer_restriction_violated),
        requires_human_rental_assessment=truth(requires_human_rental_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о прокате и не заменяет судебную оценку.",
            "Размер арендной платы, характер недостатков и объём возврата платы оцениваются "
            "экспертом и судом (статьи 629 и 630 ГК РФ).",
        ],
    )
