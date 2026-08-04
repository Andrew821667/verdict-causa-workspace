from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


COMMERCIAL_CREDIT_EVIDENCE_SCHEMA_VERSION = "contracts.commercial-credit-evidence.v0"
COMMERCIAL_CREDIT_MAPPING_VERSION = "contracts-reviewed-commercial-credit-to-facts-v0"
COMMERCIAL_CREDIT_MODEL_VERSION = "contracts-commercial-credit-articles-822-823-v0"


class CommercialCreditEvidencePredicate(str, Enum):
    # Товарный кредит (статья 822 ГК РФ).
    GOODS_CREDIT_OBLIGATION_TO_PROVIDE_FUNGIBLES = "goods_credit_obligation_to_provide_fungibles"
    GOODS_CREDIT_ITEMS_NOT_PROVIDED = "goods_credit_items_not_provided"
    QUANTITY_ASSORTMENT_OR_COMPLETENESS_TERMS_BREACHED = (
        "quantity_assortment_or_completeness_terms_breached"
    )
    QUALITY_PACKAGING_OR_CONTAINER_TERMS_BREACHED = "quality_packaging_or_container_terms_breached"
    LOAN_RULES_APPLICATION_EXCLUDED_WITHOUT_GROUND = (
        "loan_rules_application_excluded_without_ground"
    )
    # Коммерческий кредит (статья 823 ГК РФ).
    COMMERCIAL_CREDIT_GRANTED_IN_MAIN_CONTRACT = "commercial_credit_granted_in_main_contract"
    COMMERCIAL_CREDIT_TERMS_NOT_AGREED_IN_MAIN_CONTRACT = (
        "commercial_credit_terms_not_agreed_in_main_contract"
    )
    COMMERCIAL_CREDIT_INTEREST_TERMS_BREACHED = "commercial_credit_interest_terms_breached"
    CHAPTER_RULES_APPLIED_CONTRARY_TO_MAIN_CONTRACT = (
        "chapter_rules_applied_contrary_to_main_contract"
    )
    STATUTORY_PROHIBITION_ON_COMMERCIAL_CREDIT = "statutory_prohibition_on_commercial_credit"


REQUIRED_COMMERCIAL_CREDIT_PREDICATES = frozenset(CommercialCreditEvidencePredicate)


class CommercialCreditEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: CommercialCreditEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedCommercialCreditEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = COMMERCIAL_CREDIT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[CommercialCreditEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedCommercialCreditEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Commercial-credit evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Commercial-credit evidence contains duplicate legal source refs.")
        return self


class CommercialCreditFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    goods_credit_obligation_to_provide_fungibles: bool
    goods_credit_items_not_provided: bool
    quantity_assortment_or_completeness_terms_breached: bool
    quality_packaging_or_container_terms_breached: bool
    loan_rules_application_excluded_without_ground: bool
    commercial_credit_granted_in_main_contract: bool
    commercial_credit_terms_not_agreed_in_main_contract: bool
    commercial_credit_interest_terms_breached: bool
    chapter_rules_applied_contrary_to_main_contract: bool
    statutory_prohibition_on_commercial_credit: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "CommercialCreditFactSet":
        if self.goods_credit_items_not_provided and not (
            self.goods_credit_obligation_to_provide_fungibles
        ):
            raise ValueError(
                "Непредоставление вещей относится только к договору товарного кредита."
            )
        if self.commercial_credit_terms_not_agreed_in_main_contract and not (
            self.commercial_credit_granted_in_main_contract
        ):
            raise ValueError(
                "Несогласование условий коммерческого кредита относится только к случаю, когда "
                "предоставление коммерческого кредита в основном договоре установлено."
            )
        return self


class CommercialCreditFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class CommercialCreditEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: CommercialCreditFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[CommercialCreditFactProvenance] = Field(default_factory=list)


class CommercialCreditConstraintSet(BaseModel):
    id: str
    model_version: str = COMMERCIAL_CREDIT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class CommercialCreditEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    goods_credit_qualified: bool
    goods_credit_delivery_breached: bool
    quantity_terms_breached: bool
    quality_terms_breached: bool
    loan_rules_exclusion_unjustified: bool
    commercial_credit_qualified: bool
    commercial_credit_terms_missing: bool
    commercial_credit_interest_breached: bool
    chapter_rules_application_conflict: bool
    statutory_prohibition_applies: bool
    requires_human_commercial_credit_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_commercial_credit_evidence(
    evidence: ReviewedCommercialCreditEvidence,
) -> CommercialCreditEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Commercial-credit evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Commercial-credit evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_COMMERCIAL_CREDIT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed commercial-credit evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_COMMERCIAL_CREDIT_PREDICATES
    }
    return CommercialCreditEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=COMMERCIAL_CREDIT_MAPPING_VERSION,
        facts=CommercialCreditFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            CommercialCreditFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_COMMERCIAL_CREDIT_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_commercial_credit_constraint_set(
    mapping: CommercialCreditEvidenceMappingResult,
) -> CommercialCreditConstraintSet:
    return CommercialCreditConstraintSet(
        id=f"commercial-credit-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "goods_credit_qualified == goods_credit_obligation_to_provide_fungibles",
            "goods_credit_delivery_breached == goods_credit_qualified AND goods_credit_items_not_provided",
            "quantity_terms_breached == goods_credit_qualified AND quantity_assortment_or_completeness_terms_breached",
            "quality_terms_breached == goods_credit_qualified AND quality_packaging_or_container_terms_breached",
            "loan_rules_exclusion_unjustified == goods_credit_qualified AND loan_rules_application_excluded_without_ground",
            "commercial_credit_qualified == commercial_credit_granted_in_main_contract",
            "commercial_credit_terms_missing == commercial_credit_qualified AND commercial_credit_terms_not_agreed_in_main_contract",
            "commercial_credit_interest_breached == commercial_credit_qualified AND commercial_credit_interest_terms_breached",
            "chapter_rules_application_conflict == commercial_credit_qualified AND chapter_rules_applied_contrary_to_main_contract",
            "statutory_prohibition_applies == commercial_credit_qualified AND statutory_prohibition_on_commercial_credit",
            "requires_human_commercial_credit_assessment == goods_credit_delivery_breached OR quantity_terms_breached OR quality_terms_breached OR loan_rules_exclusion_unjustified OR commercial_credit_terms_missing OR commercial_credit_interest_breached OR chapter_rules_application_conflict OR statutory_prohibition_applies",
        ],
    )


def evaluate_commercial_credit_constraints(
    constraint_set: CommercialCreditConstraintSet,
    facts: CommercialCreditFactSet,
) -> CommercialCreditEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in CommercialCreditFactSet.model_fields
    }
    goods_credit_qualified = Bool("goods_credit_qualified")
    goods_credit_delivery_breached = Bool("goods_credit_delivery_breached")
    quantity_terms_breached = Bool("quantity_terms_breached")
    quality_terms_breached = Bool("quality_terms_breached")
    loan_rules_exclusion_unjustified = Bool("loan_rules_exclusion_unjustified")
    commercial_credit_qualified = Bool("commercial_credit_qualified")
    commercial_credit_terms_missing = Bool("commercial_credit_terms_missing")
    commercial_credit_interest_breached = Bool("commercial_credit_interest_breached")
    chapter_rules_application_conflict = Bool("chapter_rules_application_conflict")
    statutory_prohibition_applies = Bool("statutory_prohibition_applies")
    requires_human_commercial_credit_assessment = Bool(
        "requires_human_commercial_credit_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(goods_credit_qualified == variables["goods_credit_obligation_to_provide_fungibles"])
    solver.add(
        goods_credit_delivery_breached
        == And(goods_credit_qualified, variables["goods_credit_items_not_provided"])
    )
    solver.add(
        quantity_terms_breached
        == And(
            goods_credit_qualified,
            variables["quantity_assortment_or_completeness_terms_breached"],
        )
    )
    solver.add(
        quality_terms_breached
        == And(goods_credit_qualified, variables["quality_packaging_or_container_terms_breached"])
    )
    solver.add(
        loan_rules_exclusion_unjustified
        == And(
            goods_credit_qualified,
            variables["loan_rules_application_excluded_without_ground"],
        )
    )
    solver.add(
        commercial_credit_qualified == variables["commercial_credit_granted_in_main_contract"]
    )
    solver.add(
        commercial_credit_terms_missing
        == And(
            commercial_credit_qualified,
            variables["commercial_credit_terms_not_agreed_in_main_contract"],
        )
    )
    solver.add(
        commercial_credit_interest_breached
        == And(commercial_credit_qualified, variables["commercial_credit_interest_terms_breached"])
    )
    solver.add(
        chapter_rules_application_conflict
        == And(
            commercial_credit_qualified,
            variables["chapter_rules_applied_contrary_to_main_contract"],
        )
    )
    solver.add(
        statutory_prohibition_applies
        == And(commercial_credit_qualified, variables["statutory_prohibition_on_commercial_credit"])
    )
    solver.add(
        requires_human_commercial_credit_assessment
        == Or(
            goods_credit_delivery_breached,
            quantity_terms_breached,
            quality_terms_breached,
            loan_rules_exclusion_unjustified,
            commercial_credit_terms_missing,
            commercial_credit_interest_breached,
            chapter_rules_application_conflict,
            statutory_prohibition_applies,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return CommercialCreditEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            goods_credit_qualified=False,
            goods_credit_delivery_breached=False,
            quantity_terms_breached=False,
            quality_terms_breached=False,
            loan_rules_exclusion_unjustified=False,
            commercial_credit_qualified=False,
            commercial_credit_terms_missing=False,
            commercial_credit_interest_breached=False,
            chapter_rules_application_conflict=False,
            statutory_prohibition_applies=False,
            requires_human_commercial_credit_assessment=True,
            reasons_ru=["Набор фактов о товарном и коммерческом кредите противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как товарный кредит: сторона обязуется предоставить другой "
            "стороне вещи, определённые родовыми признаками, и к такому договору применяются "
            "правила о займе, если иное не предусмотрено договором и не вытекает из существа "
            "обязательства (статья 822 ГК РФ)."
            if truth(goods_credit_qualified)
            else "Отношения не квалифицированы как договор товарного кредита."
        ),
        (
            "Основным договором предусмотрено предоставление коммерческого кредита в виде аванса, "
            "предварительной оплаты, отсрочки или рассрочки оплаты товаров, работ или услуг "
            "(статья 823 ГК РФ)."
            if truth(commercial_credit_qualified)
            else "Предоставление коммерческого кредита основным договором не установлено."
        ),
    ]
    if truth(goods_credit_delivery_breached):
        reasons_ru.append(
            "Вещи, определённые родовыми признаками, по договору товарного кредита не "
            "предоставлены (статья 822 ГК РФ)."
        )
    if truth(quantity_terms_breached):
        reasons_ru.append(
            "Условия о количестве, ассортименте и комплектности предоставляемых вещей исполняются "
            "по правилам о купле-продаже товаров, если иное не предусмотрено договором "
            "(статья 822 ГК РФ)."
        )
    if truth(quality_terms_breached):
        reasons_ru.append(
            "Условия о качестве, таре и упаковке предоставляемых вещей исполняются по правилам о "
            "купле-продаже товаров, если иное не предусмотрено договором (статья 822 ГК РФ)."
        )
    if truth(loan_rules_exclusion_unjustified):
        reasons_ru.append(
            "Правила о займе применяются к договору товарного кредита, если иное не предусмотрено "
            "договором и не вытекает из существа обязательства (статья 822 ГК РФ)."
        )
    if truth(commercial_credit_terms_missing):
        reasons_ru.append(
            "Условие о предоставлении коммерческого кредита должно быть согласовано в договоре, "
            "исполнение которого связано с передачей денежных сумм или вещей, определяемых "
            "родовыми признаками (статья 823 ГК РФ)."
        )
    if truth(commercial_credit_interest_breached):
        reasons_ru.append(
            "К коммерческому кредиту применяются правила главы о займе и кредите, включая правила "
            "о процентах за пользование, если иное не предусмотрено правилами о договоре, из "
            "которого возникло обязательство (статьи 809 и 823 ГК РФ)."
        )
    if truth(chapter_rules_application_conflict):
        reasons_ru.append(
            "Правила главы о займе и кредите применяются к коммерческому кредиту лишь постольку, "
            "поскольку это не противоречит правилам о договоре, из которого возникло "
            "обязательство, и существу такого обязательства (статья 823 ГК РФ)."
        )
    if truth(statutory_prohibition_applies):
        reasons_ru.append(
            "Предоставление коммерческого кредита допускается, если иное не установлено законом; "
            "установленный законом запрет исключает такое условие (статья 823 ГК РФ)."
        )
    return CommercialCreditEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        goods_credit_qualified=truth(goods_credit_qualified),
        goods_credit_delivery_breached=truth(goods_credit_delivery_breached),
        quantity_terms_breached=truth(quantity_terms_breached),
        quality_terms_breached=truth(quality_terms_breached),
        loan_rules_exclusion_unjustified=truth(loan_rules_exclusion_unjustified),
        commercial_credit_qualified=truth(commercial_credit_qualified),
        commercial_credit_terms_missing=truth(commercial_credit_terms_missing),
        commercial_credit_interest_breached=truth(commercial_credit_interest_breached),
        chapter_rules_application_conflict=truth(chapter_rules_application_conflict),
        statutory_prohibition_applies=truth(statutory_prohibition_applies),
        requires_human_commercial_credit_assessment=truth(
            requires_human_commercial_credit_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о товарном и коммерческом кредите и не "
            "заменяет судебную оценку.",
            "Существо обязательства, применимость правил основного договора и размер процентов за "
            "пользование кредитом оцениваются экспертом и судом (статьи 822 и 823 ГК РФ).",
        ],
    )
