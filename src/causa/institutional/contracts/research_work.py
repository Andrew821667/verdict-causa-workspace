from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


RESEARCH_WORK_EVIDENCE_SCHEMA_VERSION = "contracts.research-work-evidence.v0"
RESEARCH_WORK_MAPPING_VERSION = "contracts-reviewed-research-work-to-facts-v0"
RESEARCH_WORK_MODEL_VERSION = "contracts-research-work-articles-769-778-v0"


class ResearchWorkEvidencePredicate(str, Enum):
    # Понятие договоров на НИР и ОКР и личное исполнение (статьи 769 и 770 ГК РФ).
    RESEARCH_OR_DEVELOPMENT_WORK_PERFORMED_FOR_FEE = (
        "research_or_development_work_performed_for_fee"
    )
    THIRD_PARTY_ENGAGED_WITHOUT_CONSENT_IN_RESEARCH = (
        "third_party_engaged_without_consent_in_research"
    )
    # Конфиденциальность и права на результаты работ (статьи 771 и 772 ГК РФ).
    CONFIDENTIALITY_OR_PUBLICATION_DUTY_BREACHED = "confidentiality_or_publication_duty_breached"
    RESULT_USE_RIGHTS_NOT_AGREED = "result_use_rights_not_agreed"
    # Обязанности исполнителя и заказчика (статьи 773 и 774 ГК РФ).
    THIRD_PARTY_EXCLUSIVE_RIGHTS_INFRINGED = "third_party_exclusive_rights_infringed"
    IMPOSSIBILITY_NOT_REPORTED_IMMEDIATELY = "impossibility_not_reported_immediately"
    CUSTOMER_INFORMATION_OR_ACCEPTANCE_DUTY_UNMET = "customer_information_or_acceptance_duty_unmet"
    # Невозможность достижения результата и расчёты (статьи 775 и 776 ГК РФ).
    RESULT_UNACHIEVABLE_WITHOUT_PERFORMER_FAULT = "result_unachievable_without_performer_fault"
    PRE_IMPOSSIBILITY_COSTS_NOT_PAID = "pre_impossibility_costs_not_paid"
    # Ответственность исполнителя за нарушение договора (статья 777 ГК РФ).
    PERFORMER_BREACH_WITHOUT_PROOF_OF_ABSENT_FAULT = (
        "performer_breach_without_proof_of_absent_fault"
    )


REQUIRED_RESEARCH_WORK_PREDICATES = frozenset(ResearchWorkEvidencePredicate)


class ResearchWorkEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ResearchWorkEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedResearchWorkEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = RESEARCH_WORK_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ResearchWorkEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedResearchWorkEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Research-work evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Research-work evidence contains duplicate legal source refs.")
        return self


class ResearchWorkFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    research_or_development_work_performed_for_fee: bool
    third_party_engaged_without_consent_in_research: bool
    confidentiality_or_publication_duty_breached: bool
    result_use_rights_not_agreed: bool
    third_party_exclusive_rights_infringed: bool
    impossibility_not_reported_immediately: bool
    customer_information_or_acceptance_duty_unmet: bool
    result_unachievable_without_performer_fault: bool
    pre_impossibility_costs_not_paid: bool
    performer_breach_without_proof_of_absent_fault: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ResearchWorkFactSet":
        if self.pre_impossibility_costs_not_paid and not (
            self.result_unachievable_without_performer_fault
        ):
            raise ValueError(
                "Неоплата работ и затрат, понесённых до выявления невозможности, относится только "
                "к случаю, когда невозможность достижения результата по не зависящим от "
                "исполнителя обстоятельствам установлена."
            )
        if self.third_party_engaged_without_consent_in_research and not (
            self.research_or_development_work_performed_for_fee
        ):
            raise ValueError(
                "Привлечение третьих лиц к научным исследованиям без согласия заказчика "
                "относится только к договору на выполнение научно-исследовательских, "
                "опытно-конструкторских и технологических работ."
            )
        return self


class ResearchWorkFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ResearchWorkEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ResearchWorkFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ResearchWorkFactProvenance] = Field(default_factory=list)


class ResearchWorkConstraintSet(BaseModel):
    id: str
    model_version: str = RESEARCH_WORK_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ResearchWorkEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    research_work_qualified: bool
    personal_performance_duty_breached: bool
    confidentiality_duty_breached: bool
    result_use_rights_missing: bool
    third_party_rights_guarantee_breached: bool
    impossibility_notice_duty_breached: bool
    customer_duties_breached: bool
    impossibility_without_fault_established: bool
    pre_impossibility_payment_due: bool
    performer_liability_established: bool
    requires_human_research_work_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_research_work_evidence(
    evidence: ReviewedResearchWorkEvidence,
) -> ResearchWorkEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Research-work evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Research-work evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_RESEARCH_WORK_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed research-work evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_RESEARCH_WORK_PREDICATES
    }
    return ResearchWorkEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=RESEARCH_WORK_MAPPING_VERSION,
        facts=ResearchWorkFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ResearchWorkFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_RESEARCH_WORK_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_research_work_constraint_set(
    mapping: ResearchWorkEvidenceMappingResult,
) -> ResearchWorkConstraintSet:
    return ResearchWorkConstraintSet(
        id=f"research-work-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "research_work_qualified == research_or_development_work_performed_for_fee",
            "personal_performance_duty_breached == research_work_qualified AND third_party_engaged_without_consent_in_research",
            "confidentiality_duty_breached == research_work_qualified AND confidentiality_or_publication_duty_breached",
            "result_use_rights_missing == research_work_qualified AND result_use_rights_not_agreed",
            "third_party_rights_guarantee_breached == research_work_qualified AND third_party_exclusive_rights_infringed",
            "impossibility_notice_duty_breached == research_work_qualified AND impossibility_not_reported_immediately",
            "customer_duties_breached == research_work_qualified AND customer_information_or_acceptance_duty_unmet",
            "impossibility_without_fault_established == research_work_qualified AND result_unachievable_without_performer_fault",
            "pre_impossibility_payment_due == research_work_qualified AND result_unachievable_without_performer_fault AND pre_impossibility_costs_not_paid",
            "performer_liability_established == research_work_qualified AND performer_breach_without_proof_of_absent_fault",
            "requires_human_research_work_assessment == personal_performance_duty_breached OR confidentiality_duty_breached OR result_use_rights_missing OR third_party_rights_guarantee_breached OR impossibility_notice_duty_breached OR customer_duties_breached OR impossibility_without_fault_established OR performer_liability_established",
        ],
    )


def evaluate_research_work_constraints(
    constraint_set: ResearchWorkConstraintSet,
    facts: ResearchWorkFactSet,
) -> ResearchWorkEvaluation:
    variables = {field_name: Bool(field_name) for field_name in ResearchWorkFactSet.model_fields}
    research_work_qualified = Bool("research_work_qualified")
    personal_performance_duty_breached = Bool("personal_performance_duty_breached")
    confidentiality_duty_breached = Bool("confidentiality_duty_breached")
    result_use_rights_missing = Bool("result_use_rights_missing")
    third_party_rights_guarantee_breached = Bool("third_party_rights_guarantee_breached")
    impossibility_notice_duty_breached = Bool("impossibility_notice_duty_breached")
    customer_duties_breached = Bool("customer_duties_breached")
    impossibility_without_fault_established = Bool("impossibility_without_fault_established")
    pre_impossibility_payment_due = Bool("pre_impossibility_payment_due")
    performer_liability_established = Bool("performer_liability_established")
    requires_human_research_work_assessment = Bool("requires_human_research_work_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        research_work_qualified == variables["research_or_development_work_performed_for_fee"]
    )
    solver.add(
        personal_performance_duty_breached
        == And(
            research_work_qualified,
            variables["third_party_engaged_without_consent_in_research"],
        )
    )
    solver.add(
        confidentiality_duty_breached
        == And(research_work_qualified, variables["confidentiality_or_publication_duty_breached"])
    )
    solver.add(
        result_use_rights_missing
        == And(research_work_qualified, variables["result_use_rights_not_agreed"])
    )
    solver.add(
        third_party_rights_guarantee_breached
        == And(research_work_qualified, variables["third_party_exclusive_rights_infringed"])
    )
    solver.add(
        impossibility_notice_duty_breached
        == And(research_work_qualified, variables["impossibility_not_reported_immediately"])
    )
    solver.add(
        customer_duties_breached
        == And(research_work_qualified, variables["customer_information_or_acceptance_duty_unmet"])
    )
    solver.add(
        impossibility_without_fault_established
        == And(research_work_qualified, variables["result_unachievable_without_performer_fault"])
    )
    solver.add(
        pre_impossibility_payment_due
        == And(
            research_work_qualified,
            variables["result_unachievable_without_performer_fault"],
            variables["pre_impossibility_costs_not_paid"],
        )
    )
    solver.add(
        performer_liability_established
        == And(
            research_work_qualified,
            variables["performer_breach_without_proof_of_absent_fault"],
        )
    )
    solver.add(
        requires_human_research_work_assessment
        == Or(
            personal_performance_duty_breached,
            confidentiality_duty_breached,
            result_use_rights_missing,
            third_party_rights_guarantee_breached,
            impossibility_notice_duty_breached,
            customer_duties_breached,
            impossibility_without_fault_established,
            performer_liability_established,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ResearchWorkEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            research_work_qualified=False,
            personal_performance_duty_breached=False,
            confidentiality_duty_breached=False,
            result_use_rights_missing=False,
            third_party_rights_guarantee_breached=False,
            impossibility_notice_duty_breached=False,
            customer_duties_breached=False,
            impossibility_without_fault_established=False,
            pre_impossibility_payment_due=False,
            performer_liability_established=False,
            requires_human_research_work_assessment=True,
            reasons_ru=[
                "Набор фактов о научно-исследовательских и опытно-конструкторских работах "
                "противоречив."
            ],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как договор на выполнение научно-исследовательских, "
            "опытно-конструкторских или технологических работ: исполнитель обязуется провести "
            "обусловленные техническим заданием заказчика научные исследования либо разработать "
            "образец нового изделия, конструкторскую документацию на него или новую технологию, "
            "а заказчик — принять работу и оплатить её (статья 769 ГК РФ)."
            if truth(research_work_qualified)
            else (
                "Отношения не квалифицированы как договор на выполнение "
                "научно-исследовательских, опытно-конструкторских и технологических работ."
            )
        ),
    ]
    if truth(personal_performance_duty_breached):
        reasons_ru.append(
            "Исполнитель обязан провести научные исследования лично и вправе привлекать к "
            "исполнению договора третьих лиц только с согласия заказчика (статья 770 ГК РФ)."
        )
    if truth(confidentiality_duty_breached):
        reasons_ru.append(
            "Стороны обязаны обеспечить конфиденциальность сведений, касающихся предмета "
            "договора, хода его исполнения и полученных результатов; публикация допускается "
            "только с согласия другой стороны (статья 771 ГК РФ)."
        )
    if truth(result_use_rights_missing):
        reasons_ru.append(
            "Стороны имеют право использовать результаты работ, в том числе способные к правовой "
            "охране, в пределах и на условиях, предусмотренных договором (статья 772 ГК РФ)."
        )
    if truth(third_party_rights_guarantee_breached):
        reasons_ru.append(
            "Исполнитель обязан гарантировать заказчику передачу полученных результатов, не "
            "нарушающих исключительных прав других лиц (статья 773 ГК РФ)."
        )
    if truth(impossibility_notice_duty_breached):
        reasons_ru.append(
            "Исполнитель обязан незамедлительно информировать заказчика об обнаруженной "
            "невозможности получить ожидаемые результаты или о нецелесообразности продолжения "
            "работы (статья 773 ГК РФ)."
        )
    if truth(customer_duties_breached):
        reasons_ru.append(
            "Заказчик обязан передавать исполнителю необходимую для выполнения работы информацию, "
            "принять результаты выполненных работ и оплатить их (статья 774 ГК РФ)."
        )
    if truth(impossibility_without_fault_established):
        reasons_ru.append(
            "Обнаружена невозможность достижения результатов вследствие обстоятельств, не "
            "зависящих от исполнителя, что влечёт особые правила расчётов сторон "
            "(статьи 775 и 776 ГК РФ)."
        )
    if truth(pre_impossibility_payment_due):
        reasons_ru.append(
            "Заказчик обязан оплатить стоимость работ, проведённых до выявления невозможности "
            "получить результат, но не свыше соответствующей части цены, а при "
            "опытно-конструкторских и технологических работах — понесённые исполнителем затраты "
            "(статьи 775 и 776 ГК РФ)."
        )
    if truth(performer_liability_established):
        reasons_ru.append(
            "Исполнитель несёт ответственность за нарушение договора, поскольку не доказал, что "
            "нарушение произошло не по его вине; убытки возмещаются в пределах стоимости работ, "
            "если договором не предусмотрено иное (статья 777 ГК РФ)."
        )
    return ResearchWorkEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        research_work_qualified=truth(research_work_qualified),
        personal_performance_duty_breached=truth(personal_performance_duty_breached),
        confidentiality_duty_breached=truth(confidentiality_duty_breached),
        result_use_rights_missing=truth(result_use_rights_missing),
        third_party_rights_guarantee_breached=truth(third_party_rights_guarantee_breached),
        impossibility_notice_duty_breached=truth(impossibility_notice_duty_breached),
        customer_duties_breached=truth(customer_duties_breached),
        impossibility_without_fault_established=truth(impossibility_without_fault_established),
        pre_impossibility_payment_due=truth(pre_impossibility_payment_due),
        performer_liability_established=truth(performer_liability_established),
        requires_human_research_work_assessment=truth(requires_human_research_work_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о научно-исследовательских, "
            "опытно-конструкторских и технологических работах и не заменяет судебную оценку.",
            "Достижимость научного результата, наличие вины исполнителя и размер понесённых "
            "затрат оцениваются экспертом и судом (статьи 775, 776 и 777 ГК РФ).",
        ],
    )
