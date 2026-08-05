from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


COMMISSION_EVIDENCE_SCHEMA_VERSION = "contracts.commission-evidence.v0"
COMMISSION_MAPPING_VERSION = "contracts-reviewed-commission-to-facts-v0"
COMMISSION_MODEL_VERSION = "contracts-commission-articles-990-1004-v0"


class CommissionEvidencePredicate(str, Enum):
    # Договор комиссии и комиссионное вознаграждение (статьи 990 и 991 ГК РФ).
    COMMISSION_CONTRACT_CONCLUDED = "commission_contract_concluded"
    COMMISSION_REMUNERATION_RULES_BREACHED = "commission_remuneration_rules_breached"
    # Исполнение комиссионного поручения и отступление от указаний (статьи 992 и 995 ГК РФ).
    COMMISSION_INSTRUCTIONS_NOT_FOLLOWED = "commission_instructions_not_followed"
    DEVIATION_NOTICE_NOT_GIVEN = "deviation_notice_not_given"
    # Ответственность за третье лицо и субкомиссия (статьи 993 и 994 ГК РФ).
    THIRD_PARTY_TRANSACTION_RULES_BREACHED = "third_party_transaction_rules_breached"
    SUBCOMMISSION_RULES_BREACHED = "subcommission_rules_breached"
    # Права на вещи и удовлетворение требований комиссионера (статьи 996–998 ГК РФ).
    PRINCIPAL_PROPERTY_RIGHTS_DISREGARDED = "principal_property_rights_disregarded"
    # Отчёт комиссионера и обязанности комитента (статьи 999–1001 ГК РФ).
    COMMISSION_REPORT_OR_TRANSFER_BREACHED = "commission_report_or_transfer_breached"
    PRINCIPAL_ACCEPTANCE_AND_EXPENSES_BREACHED = "principal_acceptance_and_expenses_breached"
    # Прекращение договора комиссии (статьи 1002–1004 ГК РФ).
    COMMISSION_TERMINATION_RULES_BREACHED = "commission_termination_rules_breached"


REQUIRED_COMMISSION_PREDICATES = frozenset(CommissionEvidencePredicate)


class CommissionEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: CommissionEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedCommissionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = COMMISSION_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[CommissionEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedCommissionEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Commission evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Commission evidence contains duplicate legal source refs.")
        return self


class CommissionFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    commission_contract_concluded: bool
    commission_remuneration_rules_breached: bool
    commission_instructions_not_followed: bool
    deviation_notice_not_given: bool
    third_party_transaction_rules_breached: bool
    subcommission_rules_breached: bool
    principal_property_rights_disregarded: bool
    commission_report_or_transfer_breached: bool
    principal_acceptance_and_expenses_breached: bool
    commission_termination_rules_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "CommissionFactSet":
        if self.deviation_notice_not_given and not self.commission_instructions_not_followed:
            raise ValueError(
                "Неуведомление об отступлении от указаний относится только к случаю, когда "
                "отступление комиссионера от указаний комитента установлено."
            )
        if self.commission_remuneration_rules_breached and not self.commission_contract_concluded:
            raise ValueError(
                "Нарушение правил о комиссионном вознаграждении относится только к договору "
                "комиссии."
            )
        return self


class CommissionFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class CommissionEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: CommissionFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[CommissionFactProvenance] = Field(default_factory=list)


class CommissionConstraintSet(BaseModel):
    id: str
    model_version: str = COMMISSION_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class CommissionEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    commission_qualified: bool
    remuneration_duty_breached: bool
    instructions_duty_breached: bool
    deviation_notice_duty_breached: bool
    third_party_transaction_duty_breached: bool
    subcommission_duty_breached: bool
    principal_property_rights_breached: bool
    report_and_transfer_duty_breached: bool
    principal_acceptance_duty_breached: bool
    termination_duty_breached: bool
    requires_human_commission_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_commission_evidence(
    evidence: ReviewedCommissionEvidence,
) -> CommissionEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Commission evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Commission evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_COMMISSION_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed commission evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_COMMISSION_PREDICATES
    }
    return CommissionEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=COMMISSION_MAPPING_VERSION,
        facts=CommissionFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            CommissionFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_COMMISSION_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_commission_constraint_set(
    mapping: CommissionEvidenceMappingResult,
) -> CommissionConstraintSet:
    return CommissionConstraintSet(
        id=f"commission-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "commission_qualified == commission_contract_concluded",
            "remuneration_duty_breached == commission_qualified AND commission_remuneration_rules_breached",
            "instructions_duty_breached == commission_qualified AND commission_instructions_not_followed",
            "deviation_notice_duty_breached == commission_qualified AND commission_instructions_not_followed AND deviation_notice_not_given",
            "third_party_transaction_duty_breached == commission_qualified AND third_party_transaction_rules_breached",
            "subcommission_duty_breached == commission_qualified AND subcommission_rules_breached",
            "principal_property_rights_breached == commission_qualified AND principal_property_rights_disregarded",
            "report_and_transfer_duty_breached == commission_qualified AND commission_report_or_transfer_breached",
            "principal_acceptance_duty_breached == commission_qualified AND principal_acceptance_and_expenses_breached",
            "termination_duty_breached == commission_qualified AND commission_termination_rules_breached",
            "requires_human_commission_assessment == remuneration_duty_breached OR instructions_duty_breached OR third_party_transaction_duty_breached OR subcommission_duty_breached OR principal_property_rights_breached OR report_and_transfer_duty_breached OR principal_acceptance_duty_breached OR termination_duty_breached",
        ],
    )


def evaluate_commission_constraints(
    constraint_set: CommissionConstraintSet,
    facts: CommissionFactSet,
) -> CommissionEvaluation:
    variables = {field_name: Bool(field_name) for field_name in CommissionFactSet.model_fields}
    commission_qualified = Bool("commission_qualified")
    remuneration_duty_breached = Bool("remuneration_duty_breached")
    instructions_duty_breached = Bool("instructions_duty_breached")
    deviation_notice_duty_breached = Bool("deviation_notice_duty_breached")
    third_party_transaction_duty_breached = Bool("third_party_transaction_duty_breached")
    subcommission_duty_breached = Bool("subcommission_duty_breached")
    principal_property_rights_breached = Bool("principal_property_rights_breached")
    report_and_transfer_duty_breached = Bool("report_and_transfer_duty_breached")
    principal_acceptance_duty_breached = Bool("principal_acceptance_duty_breached")
    termination_duty_breached = Bool("termination_duty_breached")
    requires_human_commission_assessment = Bool("requires_human_commission_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(commission_qualified == variables["commission_contract_concluded"])
    solver.add(
        remuneration_duty_breached
        == And(commission_qualified, variables["commission_remuneration_rules_breached"])
    )
    solver.add(
        instructions_duty_breached
        == And(commission_qualified, variables["commission_instructions_not_followed"])
    )
    solver.add(
        deviation_notice_duty_breached
        == And(
            commission_qualified,
            variables["commission_instructions_not_followed"],
            variables["deviation_notice_not_given"],
        )
    )
    solver.add(
        third_party_transaction_duty_breached
        == And(commission_qualified, variables["third_party_transaction_rules_breached"])
    )
    solver.add(
        subcommission_duty_breached
        == And(commission_qualified, variables["subcommission_rules_breached"])
    )
    solver.add(
        principal_property_rights_breached
        == And(commission_qualified, variables["principal_property_rights_disregarded"])
    )
    solver.add(
        report_and_transfer_duty_breached
        == And(commission_qualified, variables["commission_report_or_transfer_breached"])
    )
    solver.add(
        principal_acceptance_duty_breached
        == And(commission_qualified, variables["principal_acceptance_and_expenses_breached"])
    )
    solver.add(
        termination_duty_breached
        == And(commission_qualified, variables["commission_termination_rules_breached"])
    )
    solver.add(
        requires_human_commission_assessment
        == Or(
            remuneration_duty_breached,
            instructions_duty_breached,
            third_party_transaction_duty_breached,
            subcommission_duty_breached,
            principal_property_rights_breached,
            report_and_transfer_duty_breached,
            principal_acceptance_duty_breached,
            termination_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return CommissionEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            commission_qualified=False,
            remuneration_duty_breached=False,
            instructions_duty_breached=False,
            deviation_notice_duty_breached=False,
            third_party_transaction_duty_breached=False,
            subcommission_duty_breached=False,
            principal_property_rights_breached=False,
            report_and_transfer_duty_breached=False,
            principal_acceptance_duty_breached=False,
            termination_duty_breached=False,
            requires_human_commission_assessment=True,
            reasons_ru=["Набор фактов о комиссии противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как договор комиссии: комиссионер обязуется по поручению "
            "комитента за вознаграждение совершить одну или несколько сделок от своего имени, но "
            "за счёт комитента (статья 990 ГК РФ)."
            if truth(commission_qualified)
            else "Отношения не квалифицированы как договор комиссии."
        ),
    ]
    if truth(remuneration_duty_breached):
        reasons_ru.append(
            "Комитент обязан уплатить комиссионеру вознаграждение, а при принятии ручательства за "
            "исполнение сделки третьим лицом — также дополнительное вознаграждение за делькредере "
            "(статья 991 ГК РФ)."
        )
    if truth(instructions_duty_breached):
        reasons_ru.append(
            "Комиссионер обязан исполнить принятое поручение на наиболее выгодных для комитента "
            "условиях в соответствии с его указаниями, а отступление от указаний допускается лишь "
            "в предусмотренных законом случаях (статьи 992 и 995 ГК РФ)."
        )
    if truth(deviation_notice_duty_breached):
        reasons_ru.append(
            "Комиссионер, отступивший от указаний комитента, обязан уведомить его о допущенных "
            "отступлениях, как только уведомление стало возможным (статья 995 ГК РФ)."
        )
    if truth(third_party_transaction_duty_breached):
        reasons_ru.append(
            "Комиссионер не отвечает перед комитентом за неисполнение сделки третьим лицом, кроме "
            "случаев отсутствия необходимой осмотрительности при его выборе и принятия "
            "ручательства (делькредере); при неисполнении комиссионер обязан сообщить комитенту и "
            "передать права по сделке (статья 993 ГК РФ)."
        )
    if truth(subcommission_duty_breached):
        reasons_ru.append(
            "Комиссионер вправе заключить договор субкомиссии, если иное не предусмотрено "
            "договором, оставаясь ответственным перед комитентом за действия субкомиссионера "
            "(статья 994 ГК РФ)."
        )
    if truth(principal_property_rights_breached):
        reasons_ru.append(
            "Вещи, поступившие к комиссионеру от комитента либо приобретённые за счёт комитента, "
            "являются собственностью комитента; комиссионер вправе удерживать их и удовлетворять "
            "свои требования из поступивших сумм в предусмотренном порядке "
            "(статьи 996–998 ГК РФ)."
        )
    if truth(report_and_transfer_duty_breached):
        reasons_ru.append(
            "По исполнении поручения комиссионер обязан представить комитенту отчёт и передать "
            "ему всё полученное по договору комиссии (статья 999 ГК РФ)."
        )
    if truth(principal_acceptance_duty_breached):
        reasons_ru.append(
            "Комитент обязан принять от комиссионера всё исполненное по договору, осмотреть "
            "имущество и известить о недостатках, освободить комиссионера от обязательств перед "
            "третьим лицом, а также возместить израсходованные на исполнение поручения суммы "
            "(статьи 1000 и 1001 ГК РФ)."
        )
    if truth(termination_duty_breached):
        reasons_ru.append(
            "Договор комиссии прекращается по основаниям, предусмотренным законом; отмена "
            "поручения комитентом и отказ комиссионера от исполнения подчиняются правилам "
            "статей 1002–1004 ГК РФ."
        )
    return CommissionEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        commission_qualified=truth(commission_qualified),
        remuneration_duty_breached=truth(remuneration_duty_breached),
        instructions_duty_breached=truth(instructions_duty_breached),
        deviation_notice_duty_breached=truth(deviation_notice_duty_breached),
        third_party_transaction_duty_breached=truth(third_party_transaction_duty_breached),
        subcommission_duty_breached=truth(subcommission_duty_breached),
        principal_property_rights_breached=truth(principal_property_rights_breached),
        report_and_transfer_duty_breached=truth(report_and_transfer_duty_breached),
        principal_acceptance_duty_breached=truth(principal_acceptance_duty_breached),
        termination_duty_breached=truth(termination_duty_breached),
        requires_human_commission_assessment=truth(requires_human_commission_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о комиссии и не заменяет судебную оценку.",
            "Выгодность условий сделки, необходимая осмотрительность при выборе третьего лица и "
            "обоснованность отступления от указаний оцениваются экспертом и судом "
            "(статьи 992, 993 и 995 ГК РФ).",
        ],
    )
