from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


FORWARDING_EVIDENCE_SCHEMA_VERSION = "contracts.forwarding-evidence.v0"
FORWARDING_MAPPING_VERSION = "contracts-reviewed-forwarding-to-facts-v0"
FORWARDING_MODEL_VERSION = "contracts-forwarding-articles-801-806-v0"


class ForwardingEvidencePredicate(str, Enum):
    # Понятие транспортной экспедиции и форма договора (статьи 801 и 802 ГК РФ).
    FORWARDING_SERVICES_FOR_FEE_AT_CLIENT_EXPENSE = "forwarding_services_for_fee_at_client_expense"
    WRITTEN_FORM_OR_POWER_OF_ATTORNEY_MISSING = "written_form_or_power_of_attorney_missing"
    FORWARDER_FAILED_TO_PERFORM_AGREED_SERVICES = "forwarder_failed_to_perform_agreed_services"
    # Ответственность экспедитора и связь с договором перевозки (статья 803 ГК РФ).
    CARRIER_BREACH_CAUSED_FORWARDER_LIABILITY = "carrier_breach_caused_forwarder_liability"
    # Документы и информация о грузе (статья 804 ГК РФ).
    CLIENT_DOCUMENTS_OR_INFORMATION_NOT_PROVIDED = "client_documents_or_information_not_provided"
    FORWARDER_DID_NOT_REPORT_INCOMPLETE_INFORMATION = (
        "forwarder_did_not_report_incomplete_information"
    )
    # Исполнение обязанностей третьим лицом (статья 805 ГК РФ).
    THIRD_PARTY_ENGAGED_DESPITE_PERSONAL_DUTY = "third_party_engaged_despite_personal_duty"
    # Односторонний отказ от исполнения договора (статья 806 ГК РФ).
    WITHDRAWAL_WITHOUT_REASONABLE_NOTICE = "withdrawal_without_reasonable_notice"
    WITHDRAWAL_LOSSES_NOT_COMPENSATED = "withdrawal_losses_not_compensated"
    STATUTORY_PENALTY_NOT_PAID_ON_WITHDRAWAL = "statutory_penalty_not_paid_on_withdrawal"


REQUIRED_FORWARDING_PREDICATES = frozenset(ForwardingEvidencePredicate)


class ForwardingEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ForwardingEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedForwardingEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = FORWARDING_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ForwardingEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedForwardingEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Forwarding evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Forwarding evidence contains duplicate legal source refs.")
        return self


class ForwardingFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    forwarding_services_for_fee_at_client_expense: bool
    written_form_or_power_of_attorney_missing: bool
    forwarder_failed_to_perform_agreed_services: bool
    carrier_breach_caused_forwarder_liability: bool
    client_documents_or_information_not_provided: bool
    forwarder_did_not_report_incomplete_information: bool
    third_party_engaged_despite_personal_duty: bool
    withdrawal_without_reasonable_notice: bool
    withdrawal_losses_not_compensated: bool
    statutory_penalty_not_paid_on_withdrawal: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ForwardingFactSet":
        if self.forwarder_did_not_report_incomplete_information and not (
            self.client_documents_or_information_not_provided
        ):
            raise ValueError(
                "Несообщение экспедитора о неполноте сведений относится только к случаю, когда "
                "непредоставление клиентом документов или информации установлено."
            )
        if self.withdrawal_losses_not_compensated and not self.withdrawal_without_reasonable_notice:
            raise ValueError(
                "Невозмещение убытков, вызванных расторжением, относится только к случаю, когда "
                "односторонний отказ без предупреждения в разумный срок установлен."
            )
        return self


class ForwardingFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ForwardingEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ForwardingFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ForwardingFactProvenance] = Field(default_factory=list)


class ForwardingConstraintSet(BaseModel):
    id: str
    model_version: str = FORWARDING_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ForwardingEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    forwarding_qualified: bool
    form_or_authority_requirement_breached: bool
    forwarding_services_not_performed: bool
    carrier_linked_liability_applies: bool
    client_information_duty_breached: bool
    forwarder_notice_duty_breached: bool
    personal_performance_duty_breached: bool
    withdrawal_notice_duty_breached: bool
    withdrawal_losses_compensation_due: bool
    statutory_penalty_due: bool
    requires_human_forwarding_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_forwarding_evidence(
    evidence: ReviewedForwardingEvidence,
) -> ForwardingEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Forwarding evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Forwarding evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_FORWARDING_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed forwarding evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_FORWARDING_PREDICATES
    }
    return ForwardingEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=FORWARDING_MAPPING_VERSION,
        facts=ForwardingFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ForwardingFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_FORWARDING_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_forwarding_constraint_set(
    mapping: ForwardingEvidenceMappingResult,
) -> ForwardingConstraintSet:
    return ForwardingConstraintSet(
        id=f"forwarding-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "forwarding_qualified == forwarding_services_for_fee_at_client_expense",
            "form_or_authority_requirement_breached == forwarding_qualified AND written_form_or_power_of_attorney_missing",
            "forwarding_services_not_performed == forwarding_qualified AND forwarder_failed_to_perform_agreed_services",
            "carrier_linked_liability_applies == forwarding_qualified AND carrier_breach_caused_forwarder_liability",
            "client_information_duty_breached == forwarding_qualified AND client_documents_or_information_not_provided",
            "forwarder_notice_duty_breached == forwarding_qualified AND client_documents_or_information_not_provided AND forwarder_did_not_report_incomplete_information",
            "personal_performance_duty_breached == forwarding_qualified AND third_party_engaged_despite_personal_duty",
            "withdrawal_notice_duty_breached == forwarding_qualified AND withdrawal_without_reasonable_notice",
            "withdrawal_losses_compensation_due == forwarding_qualified AND withdrawal_without_reasonable_notice AND withdrawal_losses_not_compensated",
            "statutory_penalty_due == forwarding_qualified AND statutory_penalty_not_paid_on_withdrawal",
            "requires_human_forwarding_assessment == form_or_authority_requirement_breached OR forwarding_services_not_performed OR carrier_linked_liability_applies OR client_information_duty_breached OR personal_performance_duty_breached OR withdrawal_notice_duty_breached OR statutory_penalty_due",
        ],
    )


def evaluate_forwarding_constraints(
    constraint_set: ForwardingConstraintSet,
    facts: ForwardingFactSet,
) -> ForwardingEvaluation:
    variables = {field_name: Bool(field_name) for field_name in ForwardingFactSet.model_fields}
    forwarding_qualified = Bool("forwarding_qualified")
    form_or_authority_requirement_breached = Bool("form_or_authority_requirement_breached")
    forwarding_services_not_performed = Bool("forwarding_services_not_performed")
    carrier_linked_liability_applies = Bool("carrier_linked_liability_applies")
    client_information_duty_breached = Bool("client_information_duty_breached")
    forwarder_notice_duty_breached = Bool("forwarder_notice_duty_breached")
    personal_performance_duty_breached = Bool("personal_performance_duty_breached")
    withdrawal_notice_duty_breached = Bool("withdrawal_notice_duty_breached")
    withdrawal_losses_compensation_due = Bool("withdrawal_losses_compensation_due")
    statutory_penalty_due = Bool("statutory_penalty_due")
    requires_human_forwarding_assessment = Bool("requires_human_forwarding_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(forwarding_qualified == variables["forwarding_services_for_fee_at_client_expense"])
    solver.add(
        form_or_authority_requirement_breached
        == And(forwarding_qualified, variables["written_form_or_power_of_attorney_missing"])
    )
    solver.add(
        forwarding_services_not_performed
        == And(forwarding_qualified, variables["forwarder_failed_to_perform_agreed_services"])
    )
    solver.add(
        carrier_linked_liability_applies
        == And(forwarding_qualified, variables["carrier_breach_caused_forwarder_liability"])
    )
    solver.add(
        client_information_duty_breached
        == And(forwarding_qualified, variables["client_documents_or_information_not_provided"])
    )
    solver.add(
        forwarder_notice_duty_breached
        == And(
            forwarding_qualified,
            variables["client_documents_or_information_not_provided"],
            variables["forwarder_did_not_report_incomplete_information"],
        )
    )
    solver.add(
        personal_performance_duty_breached
        == And(forwarding_qualified, variables["third_party_engaged_despite_personal_duty"])
    )
    solver.add(
        withdrawal_notice_duty_breached
        == And(forwarding_qualified, variables["withdrawal_without_reasonable_notice"])
    )
    solver.add(
        withdrawal_losses_compensation_due
        == And(
            forwarding_qualified,
            variables["withdrawal_without_reasonable_notice"],
            variables["withdrawal_losses_not_compensated"],
        )
    )
    solver.add(
        statutory_penalty_due
        == And(forwarding_qualified, variables["statutory_penalty_not_paid_on_withdrawal"])
    )
    solver.add(
        requires_human_forwarding_assessment
        == Or(
            form_or_authority_requirement_breached,
            forwarding_services_not_performed,
            carrier_linked_liability_applies,
            client_information_duty_breached,
            personal_performance_duty_breached,
            withdrawal_notice_duty_breached,
            statutory_penalty_due,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ForwardingEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            forwarding_qualified=False,
            form_or_authority_requirement_breached=False,
            forwarding_services_not_performed=False,
            carrier_linked_liability_applies=False,
            client_information_duty_breached=False,
            forwarder_notice_duty_breached=False,
            personal_performance_duty_breached=False,
            withdrawal_notice_duty_breached=False,
            withdrawal_losses_compensation_due=False,
            statutory_penalty_due=False,
            requires_human_forwarding_assessment=True,
            reasons_ru=["Набор фактов о транспортной экспедиции противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как транспортная экспедиция: экспедитор обязуется за "
            "вознаграждение и за счёт клиента выполнить или организовать выполнение определённых "
            "договором услуг, связанных с перевозкой груза (статья 801 ГК РФ)."
            if truth(forwarding_qualified)
            else "Отношения не квалифицированы как договор транспортной экспедиции."
        ),
    ]
    if truth(form_or_authority_requirement_breached):
        reasons_ru.append(
            "Договор транспортной экспедиции заключается в письменной форме, а клиент обязан "
            "выдать экспедитору доверенность, если она необходима для выполнения его "
            "обязанностей (статья 802 ГК РФ)."
        )
    if truth(forwarding_services_not_performed):
        reasons_ru.append(
            "Экспедитор не выполнил и не организовал выполнение предусмотренных договором услуг, "
            "связанных с перевозкой груза (статьи 801 и 803 ГК РФ)."
        )
    if truth(carrier_linked_liability_applies):
        reasons_ru.append(
            "Нарушение обязательства вызвано ненадлежащим исполнением договора перевозки: "
            "ответственность экспедитора перед клиентом определяется по тем же правилам, по "
            "которым перед экспедитором отвечает соответствующий перевозчик "
            "(статья 803 ГК РФ)."
        )
    if truth(client_information_duty_breached):
        reasons_ru.append(
            "Клиент обязан предоставить экспедитору документы и другую информацию о свойствах "
            "груза, об условиях его перевозки и иную информацию, необходимую для исполнения "
            "экспедитором его обязанности (статья 804 ГК РФ)."
        )
    if truth(forwarder_notice_duty_breached):
        reasons_ru.append(
            "Экспедитор обязан сообщить клиенту об обнаруженных недостатках полученной "
            "информации, а при её неполноте — запросить у клиента необходимые дополнительные "
            "данные (статья 804 ГК РФ)."
        )
    if truth(personal_performance_duty_breached):
        reasons_ru.append(
            "Экспедитор вправе привлечь к исполнению своих обязанностей других лиц, только если "
            "из договора не следует, что он должен исполнить их лично; возложение исполнения на "
            "третье лицо не освобождает экспедитора от ответственности (статья 805 ГК РФ)."
        )
    if truth(withdrawal_notice_duty_breached):
        reasons_ru.append(
            "Любая сторона вправе отказаться от исполнения договора транспортной экспедиции, "
            "предупредив об этом другую сторону в разумный срок (статья 806 ГК РФ)."
        )
    if truth(withdrawal_losses_compensation_due):
        reasons_ru.append(
            "Сторона, заявившая об отказе от исполнения договора, возмещает другой стороне "
            "убытки, вызванные расторжением договора (статья 806 ГК РФ)."
        )
    if truth(statutory_penalty_due):
        reasons_ru.append(
            "При одностороннем отказе клиента от исполнения договора экспедитору уплачивается "
            "штраф в размере десяти процентов суммы понесённых им затрат, а при отказе "
            "экспедитора — соответствующий штраф клиенту (статья 806 ГК РФ)."
        )
    return ForwardingEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        forwarding_qualified=truth(forwarding_qualified),
        form_or_authority_requirement_breached=truth(form_or_authority_requirement_breached),
        forwarding_services_not_performed=truth(forwarding_services_not_performed),
        carrier_linked_liability_applies=truth(carrier_linked_liability_applies),
        client_information_duty_breached=truth(client_information_duty_breached),
        forwarder_notice_duty_breached=truth(forwarder_notice_duty_breached),
        personal_performance_duty_breached=truth(personal_performance_duty_breached),
        withdrawal_notice_duty_breached=truth(withdrawal_notice_duty_breached),
        withdrawal_losses_compensation_due=truth(withdrawal_losses_compensation_due),
        statutory_penalty_due=truth(statutory_penalty_due),
        requires_human_forwarding_assessment=truth(requires_human_forwarding_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о транспортной экспедиции и не заменяет "
            "судебную оценку.",
            "Разумность срока предупреждения, состав экспедиционных услуг и размер убытков и "
            "затрат оцениваются экспертом и судом (статьи 801, 803 и 806 ГК РФ).",
        ],
    )
