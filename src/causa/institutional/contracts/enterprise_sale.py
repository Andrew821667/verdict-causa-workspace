from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


ENTERPRISE_SALE_EVIDENCE_SCHEMA_VERSION = "contracts.enterprise-sale-evidence.v0"
ENTERPRISE_SALE_MAPPING_VERSION = "contracts-reviewed-enterprise-sale-to-facts-v0"
ENTERPRISE_SALE_MODEL_VERSION = "contracts-enterprise-sale-articles-559-566-v0"


class EnterpriseSaleEvidencePredicate(str, Enum):
    # Понятие, форма и регистрация договора (статьи 559 и 560 ГК РФ).
    ENTERPRISE_AS_GOING_CONCERN_CONTRACT = "enterprise_as_going_concern_contract"
    WRITTEN_SINGLE_DOCUMENT_WITH_ANNEXES = "written_single_document_with_annexes"
    SALE_CONTRACT_REGISTERED = "sale_contract_registered"
    # Удостоверение состава предприятия (статья 561 ГК РФ).
    COMPOSITION_DOCUMENTS_PREPARED = "composition_documents_prepared"
    # Права кредиторов при продаже предприятия (статья 562 ГК РФ).
    CREDITORS_NOTIFIED_IN_WRITING = "creditors_notified_in_writing"
    DEBT_TRANSFERRED_WITHOUT_CREDITOR_CONSENT = "debt_transferred_without_creditor_consent"
    # Передача предприятия и переход права (статьи 563 и 564 ГК РФ).
    ENTERPRISE_TRANSFERRED_BY_DEED = "enterprise_transferred_by_deed"
    OWNERSHIP_TRANSFER_REGISTERED = "ownership_transfer_registered"
    # Недостатки состава и публичные интересы (статьи 565 и 566 ГК РФ).
    UNDISCLOSED_DEBTS_IN_COMPOSITION = "undisclosed_debts_in_composition"
    RESCISSION_HARMS_CREDITORS_OR_PUBLIC = "rescission_harms_creditors_or_public"


REQUIRED_ENTERPRISE_SALE_PREDICATES = frozenset(EnterpriseSaleEvidencePredicate)


class EnterpriseSaleEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: EnterpriseSaleEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedEnterpriseSaleEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = ENTERPRISE_SALE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[EnterpriseSaleEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedEnterpriseSaleEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Enterprise sale evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Enterprise sale evidence contains duplicate legal source refs.")
        return self


class EnterpriseSaleFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    enterprise_as_going_concern_contract: bool
    written_single_document_with_annexes: bool
    sale_contract_registered: bool
    composition_documents_prepared: bool
    creditors_notified_in_writing: bool
    debt_transferred_without_creditor_consent: bool
    enterprise_transferred_by_deed: bool
    ownership_transfer_registered: bool
    undisclosed_debts_in_composition: bool
    rescission_harms_creditors_or_public: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "EnterpriseSaleFactSet":
        if self.sale_contract_registered and not self.written_single_document_with_annexes:
            raise ValueError(
                "Государственная регистрация договора продажи предприятия невозможна без "
                "письменной формы с обязательными приложениями."
            )
        return self


class EnterpriseSaleFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class EnterpriseSaleEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: EnterpriseSaleFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[EnterpriseSaleFactProvenance] = Field(default_factory=list)


class EnterpriseSaleConstraintSet(BaseModel):
    id: str
    model_version: str = ENTERPRISE_SALE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class EnterpriseSaleEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    enterprise_sale_qualified: bool
    written_form_satisfied: bool
    sale_contract_concluded: bool
    composition_duly_certified: bool
    creditor_protection_met: bool
    joint_liability_for_unconsented_debt: bool
    enterprise_transfer_effective: bool
    ownership_transfer_effective: bool
    price_reduction_available: bool
    rescission_restricted_by_public_interest: bool
    requires_human_enterprise_sale_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_enterprise_sale_evidence(
    evidence: ReviewedEnterpriseSaleEvidence,
) -> EnterpriseSaleEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Enterprise sale evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Enterprise sale evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_ENTERPRISE_SALE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed enterprise sale evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_ENTERPRISE_SALE_PREDICATES
    }
    return EnterpriseSaleEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=ENTERPRISE_SALE_MAPPING_VERSION,
        facts=EnterpriseSaleFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            EnterpriseSaleFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_ENTERPRISE_SALE_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_enterprise_sale_constraint_set(
    mapping: EnterpriseSaleEvidenceMappingResult,
) -> EnterpriseSaleConstraintSet:
    return EnterpriseSaleConstraintSet(
        id=f"enterprise-sale-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "enterprise_sale_qualified == enterprise_as_going_concern_contract",
            "written_form_satisfied == enterprise_as_going_concern_contract AND written_single_document_with_annexes",
            "sale_contract_concluded == written_form_satisfied AND sale_contract_registered",
            "composition_duly_certified == enterprise_sale_qualified AND composition_documents_prepared",
            "creditor_protection_met == enterprise_sale_qualified AND creditors_notified_in_writing AND NOT debt_transferred_without_creditor_consent",
            "joint_liability_for_unconsented_debt == enterprise_sale_qualified AND debt_transferred_without_creditor_consent",
            "enterprise_transfer_effective == enterprise_sale_qualified AND enterprise_transferred_by_deed",
            "ownership_transfer_effective == enterprise_sale_qualified AND ownership_transfer_registered",
            "price_reduction_available == enterprise_sale_qualified AND undisclosed_debts_in_composition",
            "rescission_restricted_by_public_interest == rescission_harms_creditors_or_public",
            "requires_human_enterprise_sale_assessment == (enterprise_sale_qualified AND debt_transferred_without_creditor_consent) OR (enterprise_sale_qualified AND undisclosed_debts_in_composition) OR rescission_harms_creditors_or_public",
        ],
    )


def evaluate_enterprise_sale_constraints(
    constraint_set: EnterpriseSaleConstraintSet,
    facts: EnterpriseSaleFactSet,
) -> EnterpriseSaleEvaluation:
    variables = {field_name: Bool(field_name) for field_name in EnterpriseSaleFactSet.model_fields}
    enterprise_sale_qualified = Bool("enterprise_sale_qualified")
    written_form_satisfied = Bool("written_form_satisfied")
    sale_contract_concluded = Bool("sale_contract_concluded")
    composition_duly_certified = Bool("composition_duly_certified")
    creditor_protection_met = Bool("creditor_protection_met")
    joint_liability_for_unconsented_debt = Bool("joint_liability_for_unconsented_debt")
    enterprise_transfer_effective = Bool("enterprise_transfer_effective")
    ownership_transfer_effective = Bool("ownership_transfer_effective")
    price_reduction_available = Bool("price_reduction_available")
    rescission_restricted_by_public_interest = Bool("rescission_restricted_by_public_interest")
    requires_human_enterprise_sale_assessment = Bool("requires_human_enterprise_sale_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(enterprise_sale_qualified == variables["enterprise_as_going_concern_contract"])
    solver.add(
        written_form_satisfied
        == And(
            variables["enterprise_as_going_concern_contract"],
            variables["written_single_document_with_annexes"],
        )
    )
    solver.add(
        sale_contract_concluded
        == And(written_form_satisfied, variables["sale_contract_registered"])
    )
    solver.add(
        composition_duly_certified
        == And(enterprise_sale_qualified, variables["composition_documents_prepared"])
    )
    solver.add(
        creditor_protection_met
        == And(
            enterprise_sale_qualified,
            variables["creditors_notified_in_writing"],
            Not(variables["debt_transferred_without_creditor_consent"]),
        )
    )
    solver.add(
        joint_liability_for_unconsented_debt
        == And(
            enterprise_sale_qualified,
            variables["debt_transferred_without_creditor_consent"],
        )
    )
    solver.add(
        enterprise_transfer_effective
        == And(enterprise_sale_qualified, variables["enterprise_transferred_by_deed"])
    )
    solver.add(
        ownership_transfer_effective
        == And(enterprise_sale_qualified, variables["ownership_transfer_registered"])
    )
    solver.add(
        price_reduction_available
        == And(enterprise_sale_qualified, variables["undisclosed_debts_in_composition"])
    )
    solver.add(
        rescission_restricted_by_public_interest
        == variables["rescission_harms_creditors_or_public"]
    )
    solver.add(
        requires_human_enterprise_sale_assessment
        == Or(
            And(
                enterprise_sale_qualified,
                variables["debt_transferred_without_creditor_consent"],
            ),
            And(enterprise_sale_qualified, variables["undisclosed_debts_in_composition"]),
            variables["rescission_harms_creditors_or_public"],
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return EnterpriseSaleEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            enterprise_sale_qualified=False,
            written_form_satisfied=False,
            sale_contract_concluded=False,
            composition_duly_certified=False,
            creditor_protection_met=False,
            joint_liability_for_unconsented_debt=False,
            enterprise_transfer_effective=False,
            ownership_transfer_effective=False,
            price_reduction_available=False,
            rescission_restricted_by_public_interest=False,
            requires_human_enterprise_sale_assessment=True,
            reasons_ru=["Набор фактов о продаже предприятия противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как продажа предприятия: продавец обязуется передать в "
            "собственность покупателя предприятие в целом как имущественный комплекс "
            "(статья 559 ГК РФ)."
            if truth(enterprise_sale_qualified)
            else "Отношения не квалифицированы как договор продажи предприятия."
        ),
    ]
    if truth(written_form_satisfied):
        reasons_ru.append(
            "Договор заключён в письменной форме одним документом с обязательными "
            "приложениями (статья 560 ГК РФ)."
        )
    if truth(sale_contract_concluded):
        reasons_ru.append(
            "Договор продажи предприятия прошёл государственную регистрацию и считается "
            "заключённым (статья 560 ГК РФ)."
        )
    if truth(composition_duly_certified):
        reasons_ru.append(
            "Состав предприятия удостоверён актом инвентаризации, балансом, заключением "
            "аудитора и перечнем долгов (статья 561 ГК РФ)."
        )
    if truth(creditor_protection_met):
        reasons_ru.append(
            "Кредиторы по включённым обязательствам письменно уведомлены о продаже, "
            "перевод долга без согласия кредитора отсутствует (статья 562 ГК РФ)."
        )
    if truth(joint_liability_for_unconsented_debt):
        reasons_ru.append(
            "По долгам, переведённым без согласия кредитора, продавец и покупатель отвечают "
            "солидарно (статья 562 ГК РФ)."
        )
    if truth(enterprise_transfer_effective):
        reasons_ru.append(
            "Предприятие передано по передаточному акту, подписанному обеими сторонами "
            "(статья 563 ГК РФ)."
        )
    if truth(ownership_transfer_effective):
        reasons_ru.append(
            "Переход права собственности на предприятие к покупателю зарегистрирован "
            "(статья 564 ГК РФ)."
        )
    if truth(price_reduction_available):
        reasons_ru.append(
            "При выявлении в составе переданного предприятия долгов, не указанных в договоре "
            "или передаточном акте, покупатель вправе требовать уменьшения цены "
            "(статья 565 ГК РФ)."
        )
    if truth(rescission_restricted_by_public_interest):
        reasons_ru.append(
            "Применение последствий недействительности или изменения и расторжения "
            "ограничено, если существенно нарушает права кредиторов и других лиц либо "
            "противоречит публичным интересам (статья 566 ГК РФ)."
        )
    return EnterpriseSaleEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        enterprise_sale_qualified=truth(enterprise_sale_qualified),
        written_form_satisfied=truth(written_form_satisfied),
        sale_contract_concluded=truth(sale_contract_concluded),
        composition_duly_certified=truth(composition_duly_certified),
        creditor_protection_met=truth(creditor_protection_met),
        joint_liability_for_unconsented_debt=truth(joint_liability_for_unconsented_debt),
        enterprise_transfer_effective=truth(enterprise_transfer_effective),
        ownership_transfer_effective=truth(ownership_transfer_effective),
        price_reduction_available=truth(price_reduction_available),
        rescission_restricted_by_public_interest=truth(rescission_restricted_by_public_interest),
        requires_human_enterprise_sale_assessment=truth(requires_human_enterprise_sale_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о продаже предприятия и не заменяет "
            "судебную оценку.",
            "Состав предприятия, размер долгов и убытков и государственная регистрация "
            "оцениваются экспертом, аудитором и регистрирующим органом.",
        ],
    )
