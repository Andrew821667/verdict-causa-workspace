from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


REAL_ESTATE_SALE_EVIDENCE_SCHEMA_VERSION = "contracts.real-estate-sale-evidence.v0"
REAL_ESTATE_SALE_MAPPING_VERSION = "contracts-reviewed-real-estate-sale-to-facts-v0"
REAL_ESTATE_SALE_MODEL_VERSION = "contracts-real-estate-sale-articles-549-558-v0"


class RealEstateSaleEvidencePredicate(str, Enum):
    # Понятие и форма договора продажи недвижимости (статьи 549 и 550 ГК РФ).
    REAL_ESTATE_TRANSFER_CONTRACT = "real_estate_transfer_contract"
    WRITTEN_SINGLE_DOCUMENT_SIGNED = "written_single_document_signed"
    # Определённость предмета и цена (статьи 554 и 555 ГК РФ).
    PROPERTY_DEFINITIVELY_IDENTIFIED = "property_definitively_identified"
    PRICE_AGREED_IN_CONTRACT = "price_agreed_in_contract"
    # Государственная регистрация перехода права (статья 551 ГК РФ).
    OWNERSHIP_TRANSFER_REGISTERED = "ownership_transfer_registered"
    # Передача недвижимости (статья 556 ГК РФ).
    PROPERTY_HANDED_OVER_BY_DEED = "property_handed_over_by_deed"
    PARTY_EVADED_TRANSFER_DEED = "party_evaded_transfer_deed"
    # Качество недвижимости (статья 557 ГК РФ).
    PROPERTY_QUALITY_DEFECTIVE = "property_quality_defective"
    # Особенности продажи жилых помещений (статья 558 ГК РФ).
    RESIDENTIAL_PREMISES = "residential_premises"
    OCCUPANT_RIGHTS_LIST_INCLUDED = "occupant_rights_list_included"


REQUIRED_REAL_ESTATE_SALE_PREDICATES = frozenset(RealEstateSaleEvidencePredicate)


class RealEstateSaleEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: RealEstateSaleEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedRealEstateSaleEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = REAL_ESTATE_SALE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[RealEstateSaleEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedRealEstateSaleEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Real estate sale evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Real estate sale evidence contains duplicate legal source refs.")
        return self


class RealEstateSaleFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    real_estate_transfer_contract: bool
    written_single_document_signed: bool
    property_definitively_identified: bool
    price_agreed_in_contract: bool
    ownership_transfer_registered: bool
    property_handed_over_by_deed: bool
    party_evaded_transfer_deed: bool
    property_quality_defective: bool
    residential_premises: bool
    occupant_rights_list_included: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "RealEstateSaleFactSet":
        if self.occupant_rights_list_included and not self.residential_premises:
            raise ValueError(
                "Перечень лиц, сохраняющих право пользования, указывается только при продаже "
                "жилого помещения."
            )
        if self.party_evaded_transfer_deed and self.property_handed_over_by_deed:
            raise ValueError(
                "Передача недвижимости по акту и уклонение от подписания акта несовместимы."
            )
        return self


class RealEstateSaleFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class RealEstateSaleEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: RealEstateSaleFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[RealEstateSaleFactProvenance] = Field(default_factory=list)


class RealEstateSaleConstraintSet(BaseModel):
    id: str
    model_version: str = REAL_ESTATE_SALE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class RealEstateSaleEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    real_estate_sale_qualified: bool
    written_form_satisfied: bool
    contract_concluded: bool
    ownership_transfer_effective: bool
    transfer_obligation_met: bool
    transfer_evasion_is_refusal: bool
    buyer_quality_remedies_available: bool
    requires_human_real_estate_sale_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_real_estate_sale_evidence(
    evidence: ReviewedRealEstateSaleEvidence,
) -> RealEstateSaleEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Real estate sale evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Real estate sale evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_REAL_ESTATE_SALE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed real estate sale evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_REAL_ESTATE_SALE_PREDICATES
    }
    return RealEstateSaleEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=REAL_ESTATE_SALE_MAPPING_VERSION,
        facts=RealEstateSaleFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            RealEstateSaleFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_REAL_ESTATE_SALE_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_real_estate_sale_constraint_set(
    mapping: RealEstateSaleEvidenceMappingResult,
) -> RealEstateSaleConstraintSet:
    return RealEstateSaleConstraintSet(
        id=f"real-estate-sale-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "real_estate_sale_qualified == real_estate_transfer_contract",
            "written_form_satisfied == real_estate_transfer_contract AND written_single_document_signed",
            "contract_concluded == real_estate_sale_qualified AND property_definitively_identified AND price_agreed_in_contract AND (NOT residential_premises OR occupant_rights_list_included)",
            "ownership_transfer_effective == real_estate_sale_qualified AND ownership_transfer_registered",
            "transfer_obligation_met == real_estate_sale_qualified AND property_handed_over_by_deed",
            "transfer_evasion_is_refusal == party_evaded_transfer_deed",
            "buyer_quality_remedies_available == real_estate_sale_qualified AND property_quality_defective",
            "requires_human_real_estate_sale_assessment == (real_estate_sale_qualified AND property_quality_defective) OR party_evaded_transfer_deed",
        ],
    )


def evaluate_real_estate_sale_constraints(
    constraint_set: RealEstateSaleConstraintSet,
    facts: RealEstateSaleFactSet,
) -> RealEstateSaleEvaluation:
    variables = {field_name: Bool(field_name) for field_name in RealEstateSaleFactSet.model_fields}
    real_estate_sale_qualified = Bool("real_estate_sale_qualified")
    written_form_satisfied = Bool("written_form_satisfied")
    contract_concluded = Bool("contract_concluded")
    ownership_transfer_effective = Bool("ownership_transfer_effective")
    transfer_obligation_met = Bool("transfer_obligation_met")
    transfer_evasion_is_refusal = Bool("transfer_evasion_is_refusal")
    buyer_quality_remedies_available = Bool("buyer_quality_remedies_available")
    requires_human_real_estate_sale_assessment = Bool("requires_human_real_estate_sale_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(real_estate_sale_qualified == variables["real_estate_transfer_contract"])
    solver.add(
        written_form_satisfied
        == And(
            variables["real_estate_transfer_contract"],
            variables["written_single_document_signed"],
        )
    )
    solver.add(
        contract_concluded
        == And(
            real_estate_sale_qualified,
            variables["property_definitively_identified"],
            variables["price_agreed_in_contract"],
            Or(
                Not(variables["residential_premises"]),
                variables["occupant_rights_list_included"],
            ),
        )
    )
    solver.add(
        ownership_transfer_effective
        == And(real_estate_sale_qualified, variables["ownership_transfer_registered"])
    )
    solver.add(
        transfer_obligation_met
        == And(real_estate_sale_qualified, variables["property_handed_over_by_deed"])
    )
    solver.add(transfer_evasion_is_refusal == variables["party_evaded_transfer_deed"])
    solver.add(
        buyer_quality_remedies_available
        == And(real_estate_sale_qualified, variables["property_quality_defective"])
    )
    solver.add(
        requires_human_real_estate_sale_assessment
        == Or(
            And(real_estate_sale_qualified, variables["property_quality_defective"]),
            variables["party_evaded_transfer_deed"],
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return RealEstateSaleEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            real_estate_sale_qualified=False,
            written_form_satisfied=False,
            contract_concluded=False,
            ownership_transfer_effective=False,
            transfer_obligation_met=False,
            transfer_evasion_is_refusal=False,
            buyer_quality_remedies_available=False,
            requires_human_real_estate_sale_assessment=True,
            reasons_ru=["Набор фактов о продаже недвижимости противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как продажа недвижимости: продавец обязуется передать в "
            "собственность покупателя недвижимое имущество (статья 549 ГК РФ)."
            if truth(real_estate_sale_qualified)
            else "Отношения не квалифицированы как договор продажи недвижимости."
        ),
    ]
    if truth(written_form_satisfied):
        reasons_ru.append(
            "Договор заключён в письменной форме путём составления одного документа, "
            "подписанного сторонами (статья 550 ГК РФ)."
        )
    if truth(contract_concluded):
        reasons_ru.append(
            "Договор считается заключённым: предмет определён, цена согласована и для жилого "
            "помещения указан перечень лиц, сохраняющих право пользования "
            "(статьи 554, 555 и 558 ГК РФ)."
        )
    if truth(ownership_transfer_effective):
        reasons_ru.append(
            "Переход права собственности на недвижимость к покупателю зарегистрирован "
            "(статья 551 ГК РФ)."
        )
    if truth(transfer_obligation_met):
        reasons_ru.append(
            "Недвижимость передана по передаточному акту или иному документу о передаче "
            "(статья 556 ГК РФ)."
        )
    if truth(transfer_evasion_is_refusal):
        reasons_ru.append(
            "Уклонение стороны от подписания передаточного акта считается отказом от "
            "исполнения обязанности по передаче или принятию недвижимости (статья 556 ГК РФ)."
        )
    if truth(buyer_quality_remedies_available):
        reasons_ru.append(
            "При передаче недвижимости ненадлежащего качества покупатель вправе воспользоваться "
            "последствиями статьи 475 ГК РФ, кроме требования о замене (статья 557 ГК РФ)."
        )
    return RealEstateSaleEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        real_estate_sale_qualified=truth(real_estate_sale_qualified),
        written_form_satisfied=truth(written_form_satisfied),
        contract_concluded=truth(contract_concluded),
        ownership_transfer_effective=truth(ownership_transfer_effective),
        transfer_obligation_met=truth(transfer_obligation_met),
        transfer_evasion_is_refusal=truth(transfer_evasion_is_refusal),
        buyer_quality_remedies_available=truth(buyer_quality_remedies_available),
        requires_human_real_estate_sale_assessment=truth(
            requires_human_real_estate_sale_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о продаже недвижимости и не заменяет "
            "судебную оценку.",
            "Определённость предмета, размер убытков и государственная регистрация оцениваются "
            "экспертом и регистрирующим органом.",
        ],
    )
