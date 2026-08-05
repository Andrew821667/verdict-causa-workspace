from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


INSURANCE_SETTLEMENT_EVIDENCE_SCHEMA_VERSION = "contracts.insurance-settlement-evidence.v0"
INSURANCE_SETTLEMENT_MAPPING_VERSION = "contracts-reviewed-insurance-settlement-to-facts-v0"
INSURANCE_SETTLEMENT_MODEL_VERSION = "contracts-insurance-settlement-articles-944-970-v0"


class InsuranceSettlementEvidencePredicate(str, Enum):
    # Исполнение страхового обязательства и сведения при заключении договора (статья 944 ГК РФ).
    INSURED_EVENT_SETTLEMENT_STARTED = "insured_event_settlement_started"
    MATERIAL_INFORMATION_NOT_DISCLOSED = "material_information_not_disclosed"
    # Страховая сумма и страховая премия (статьи 947–951, 954 и 957 ГК РФ).
    INSURED_SUM_RULES_BREACHED = "insured_sum_rules_breached"
    PREMIUM_PAYMENT_RULES_BREACHED = "premium_payment_rules_breached"
    # Увеличение страхового риска и досрочное прекращение (статьи 958 и 959 ГК РФ).
    RISK_INCREASE_OR_EARLY_TERMINATION_BREACHED = "risk_increase_or_early_termination_breached"
    # Уведомление о страховом случае (статья 961 ГК РФ).
    INSURED_EVENT_NOTICE_NOT_GIVEN = "insured_event_notice_not_given"
    NOTICE_DELAY_CONSEQUENCES_NOT_APPLIED = "notice_delay_consequences_not_applied"
    # Уменьшение убытков и освобождение страховщика (статьи 962–964 ГК РФ).
    LOSS_MITIGATION_DUTY_BREACHED = "loss_mitigation_duty_breached"
    INSURER_RELEASE_GROUNDS_MISAPPLIED = "insurer_release_grounds_misapplied"
    # Суброгация и исковая давность (статьи 965 и 966 ГК РФ).
    SUBROGATION_OR_LIMITATION_RULES_BREACHED = "subrogation_or_limitation_rules_breached"


REQUIRED_INSURANCE_SETTLEMENT_PREDICATES = frozenset(InsuranceSettlementEvidencePredicate)


class InsuranceSettlementEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: InsuranceSettlementEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedInsuranceSettlementEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = INSURANCE_SETTLEMENT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[InsuranceSettlementEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedInsuranceSettlementEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Insurance-settlement evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Insurance-settlement evidence contains duplicate legal source refs.")
        return self


class InsuranceSettlementFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    insured_event_settlement_started: bool
    material_information_not_disclosed: bool
    insured_sum_rules_breached: bool
    premium_payment_rules_breached: bool
    risk_increase_or_early_termination_breached: bool
    insured_event_notice_not_given: bool
    notice_delay_consequences_not_applied: bool
    loss_mitigation_duty_breached: bool
    insurer_release_grounds_misapplied: bool
    subrogation_or_limitation_rules_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "InsuranceSettlementFactSet":
        if self.notice_delay_consequences_not_applied and not self.insured_event_notice_not_given:
            raise ValueError(
                "Неприменение последствий несвоевременного уведомления относится только к случаю, "
                "когда нарушение уведомления о страховом случае установлено."
            )
        if self.material_information_not_disclosed and not self.insured_event_settlement_started:
            raise ValueError(
                "Несообщение существенных сведений относится только к исполнению страхового "
                "обязательства."
            )
        return self


class InsuranceSettlementFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class InsuranceSettlementEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: InsuranceSettlementFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[InsuranceSettlementFactProvenance] = Field(default_factory=list)


class InsuranceSettlementConstraintSet(BaseModel):
    id: str
    model_version: str = INSURANCE_SETTLEMENT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class InsuranceSettlementEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    insurance_settlement_qualified: bool
    disclosure_duty_breached: bool
    insured_sum_duty_breached: bool
    premium_duty_breached: bool
    risk_and_termination_duty_breached: bool
    insured_event_notice_duty_breached: bool
    notice_delay_consequences_breached: bool
    loss_mitigation_breached: bool
    insurer_release_duty_breached: bool
    subrogation_and_limitation_breached: bool
    requires_human_insurance_settlement_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_insurance_settlement_evidence(
    evidence: ReviewedInsuranceSettlementEvidence,
) -> InsuranceSettlementEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Insurance-settlement evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Insurance-settlement evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value
        for predicate in REQUIRED_INSURANCE_SETTLEMENT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed insurance-settlement evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_INSURANCE_SETTLEMENT_PREDICATES
    }
    return InsuranceSettlementEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=INSURANCE_SETTLEMENT_MAPPING_VERSION,
        facts=InsuranceSettlementFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            InsuranceSettlementFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_INSURANCE_SETTLEMENT_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_insurance_settlement_constraint_set(
    mapping: InsuranceSettlementEvidenceMappingResult,
) -> InsuranceSettlementConstraintSet:
    return InsuranceSettlementConstraintSet(
        id=f"insurance-settlement-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "insurance_settlement_qualified == insured_event_settlement_started",
            "disclosure_duty_breached == insurance_settlement_qualified AND material_information_not_disclosed",
            "insured_sum_duty_breached == insurance_settlement_qualified AND insured_sum_rules_breached",
            "premium_duty_breached == insurance_settlement_qualified AND premium_payment_rules_breached",
            "risk_and_termination_duty_breached == insurance_settlement_qualified AND risk_increase_or_early_termination_breached",
            "insured_event_notice_duty_breached == insurance_settlement_qualified AND insured_event_notice_not_given",
            "notice_delay_consequences_breached == insurance_settlement_qualified AND insured_event_notice_not_given AND notice_delay_consequences_not_applied",
            "loss_mitigation_breached == insurance_settlement_qualified AND loss_mitigation_duty_breached",
            "insurer_release_duty_breached == insurance_settlement_qualified AND insurer_release_grounds_misapplied",
            "subrogation_and_limitation_breached == insurance_settlement_qualified AND subrogation_or_limitation_rules_breached",
            "requires_human_insurance_settlement_assessment == disclosure_duty_breached OR insured_sum_duty_breached OR premium_duty_breached OR risk_and_termination_duty_breached OR insured_event_notice_duty_breached OR loss_mitigation_breached OR insurer_release_duty_breached OR subrogation_and_limitation_breached",
        ],
    )


def evaluate_insurance_settlement_constraints(
    constraint_set: InsuranceSettlementConstraintSet,
    facts: InsuranceSettlementFactSet,
) -> InsuranceSettlementEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in InsuranceSettlementFactSet.model_fields
    }
    insurance_settlement_qualified = Bool("insurance_settlement_qualified")
    disclosure_duty_breached = Bool("disclosure_duty_breached")
    insured_sum_duty_breached = Bool("insured_sum_duty_breached")
    premium_duty_breached = Bool("premium_duty_breached")
    risk_and_termination_duty_breached = Bool("risk_and_termination_duty_breached")
    insured_event_notice_duty_breached = Bool("insured_event_notice_duty_breached")
    notice_delay_consequences_breached = Bool("notice_delay_consequences_breached")
    loss_mitigation_breached = Bool("loss_mitigation_breached")
    insurer_release_duty_breached = Bool("insurer_release_duty_breached")
    subrogation_and_limitation_breached = Bool("subrogation_and_limitation_breached")
    requires_human_insurance_settlement_assessment = Bool(
        "requires_human_insurance_settlement_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(insurance_settlement_qualified == variables["insured_event_settlement_started"])
    solver.add(
        disclosure_duty_breached
        == And(insurance_settlement_qualified, variables["material_information_not_disclosed"])
    )
    solver.add(
        insured_sum_duty_breached
        == And(insurance_settlement_qualified, variables["insured_sum_rules_breached"])
    )
    solver.add(
        premium_duty_breached
        == And(insurance_settlement_qualified, variables["premium_payment_rules_breached"])
    )
    solver.add(
        risk_and_termination_duty_breached
        == And(
            insurance_settlement_qualified,
            variables["risk_increase_or_early_termination_breached"],
        )
    )
    solver.add(
        insured_event_notice_duty_breached
        == And(insurance_settlement_qualified, variables["insured_event_notice_not_given"])
    )
    solver.add(
        notice_delay_consequences_breached
        == And(
            insurance_settlement_qualified,
            variables["insured_event_notice_not_given"],
            variables["notice_delay_consequences_not_applied"],
        )
    )
    solver.add(
        loss_mitigation_breached
        == And(insurance_settlement_qualified, variables["loss_mitigation_duty_breached"])
    )
    solver.add(
        insurer_release_duty_breached
        == And(insurance_settlement_qualified, variables["insurer_release_grounds_misapplied"])
    )
    solver.add(
        subrogation_and_limitation_breached
        == And(
            insurance_settlement_qualified,
            variables["subrogation_or_limitation_rules_breached"],
        )
    )
    solver.add(
        requires_human_insurance_settlement_assessment
        == Or(
            disclosure_duty_breached,
            insured_sum_duty_breached,
            premium_duty_breached,
            risk_and_termination_duty_breached,
            insured_event_notice_duty_breached,
            loss_mitigation_breached,
            insurer_release_duty_breached,
            subrogation_and_limitation_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return InsuranceSettlementEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            insurance_settlement_qualified=False,
            disclosure_duty_breached=False,
            insured_sum_duty_breached=False,
            premium_duty_breached=False,
            risk_and_termination_duty_breached=False,
            insured_event_notice_duty_breached=False,
            notice_delay_consequences_breached=False,
            loss_mitigation_breached=False,
            insurer_release_duty_breached=False,
            subrogation_and_limitation_breached=False,
            requires_human_insurance_settlement_assessment=True,
            reasons_ru=["Набор фактов об исполнении страхового обязательства противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Установлено исполнение страхового обязательства: наступил страховой случай и "
            "рассматриваются права и обязанности сторон договора страхования "
            "(статьи 944–970 ГК РФ)."
            if truth(insurance_settlement_qualified)
            else "Исполнение страхового обязательства по спорным отношениям не установлено."
        ),
    ]
    if truth(disclosure_duty_breached):
        reasons_ru.append(
            "При заключении договора страхователь обязан сообщить страховщику известные ему "
            "обстоятельства, имеющие существенное значение для определения вероятности "
            "наступления страхового случая и размера возможных убытков (статья 944 ГК РФ)."
        )
    if truth(insured_sum_duty_breached):
        reasons_ru.append(
            "Страховая сумма определяется соглашением сторон и по имущественному страхованию не "
            "должна превышать страховую стоимость; последствия страхования сверх страховой "
            "стоимости и неполного имущественного страхования определяются статьями 947–951 "
            "ГК РФ."
        )
    if truth(premium_duty_breached):
        reasons_ru.append(
            "Страховая премия уплачивается в порядке и сроки, предусмотренные договором; договор "
            "страхования вступает в силу в момент уплаты премии или первого взноса, если "
            "договором не предусмотрено иное (статьи 954 и 957 ГК РФ)."
        )
    if truth(risk_and_termination_duty_breached):
        reasons_ru.append(
            "Страхователь обязан незамедлительно сообщать страховщику о ставших ему известными "
            "значительных изменениях в обстоятельствах, влекущих увеличение страхового риска, а "
            "досрочное прекращение договора страхования подчиняется правилам статей 958 и 959 "
            "ГК РФ."
        )
    if truth(insured_event_notice_duty_breached):
        reasons_ru.append(
            "Страхователь обязан незамедлительно уведомить страховщика или его представителя о "
            "наступлении страхового случая в предусмотренный договором срок и способом "
            "(статья 961 ГК РФ)."
        )
    if truth(notice_delay_consequences_breached):
        reasons_ru.append(
            "Неисполнение обязанности уведомить о страховом случае даёт страховщику право "
            "отказать в выплате, если не будет доказано, что страховщик своевременно узнал о "
            "страховом случае либо что отсутствие сведений не могло сказаться на его обязанности "
            "произвести выплату (статья 961 ГК РФ)."
        )
    if truth(loss_mitigation_breached):
        reasons_ru.append(
            "При наступлении страхового случая страхователь обязан принять разумные и доступные "
            "в сложившихся обстоятельствах меры, чтобы уменьшить возможные убытки; необходимые "
            "расходы возмещаются страховщиком (статья 962 ГК РФ)."
        )
    if truth(insurer_release_duty_breached):
        reasons_ru.append(
            "Освобождение страховщика от выплаты допускается по основаниям, предусмотренным "
            "законом, в том числе при умысле страхователя и при наступлении страхового случая "
            "вследствие обстоятельств, указанных в статье 964 ГК РФ (статьи 963 и 964 ГК РФ)."
        )
    if truth(subrogation_and_limitation_breached):
        reasons_ru.append(
            "К страховщику, выплатившему страховое возмещение, переходит в пределах выплаченной "
            "суммы право требования к лицу, ответственному за убытки, а срок исковой давности по "
            "требованиям из договора страхования определяется статьёй 966 ГК РФ "
            "(статьи 965 и 966 ГК РФ)."
        )
    return InsuranceSettlementEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        insurance_settlement_qualified=truth(insurance_settlement_qualified),
        disclosure_duty_breached=truth(disclosure_duty_breached),
        insured_sum_duty_breached=truth(insured_sum_duty_breached),
        premium_duty_breached=truth(premium_duty_breached),
        risk_and_termination_duty_breached=truth(risk_and_termination_duty_breached),
        insured_event_notice_duty_breached=truth(insured_event_notice_duty_breached),
        notice_delay_consequences_breached=truth(notice_delay_consequences_breached),
        loss_mitigation_breached=truth(loss_mitigation_breached),
        insurer_release_duty_breached=truth(insurer_release_duty_breached),
        subrogation_and_limitation_breached=truth(subrogation_and_limitation_breached),
        requires_human_insurance_settlement_assessment=truth(
            requires_human_insurance_settlement_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только правила об исполнении страхового обязательства и не заменяет "
            "судебную оценку.",
            "Существенность несообщённых сведений, разумность мер по уменьшению убытков и наличие "
            "оснований освобождения страховщика оцениваются экспертом и судом "
            "(статьи 944, 962 и 963 ГК РФ).",
        ],
    )
