from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


PUBLIC_CONTRACT_EVIDENCE_SCHEMA_VERSION = "contracts.public-contract-evidence.v0"
PUBLIC_CONTRACT_MAPPING_VERSION = "contracts-reviewed-public-contract-to-facts-v0"
PUBLIC_CONTRACT_MODEL_VERSION = "contracts-public-contract-article-426-v0"


class PublicContractEvidencePredicate(str, Enum):
    # Публичный характер и обязанность заключить договор (пункты 1 и 3 статьи 426 ГК РФ).
    PUBLIC_CONTRACT_REGIME = "public_contract_regime"
    COUNTERPARTY_REQUESTED_CONTRACT = "counterparty_requested_contract"
    PERFORMANCE_POSSIBLE = "performance_possible"
    REFUSAL_WITHOUT_LAWFUL_GROUND = "refusal_without_lawful_ground"
    # Недопустимость предпочтения и различия условий (пункты 1 и 2 статьи 426 ГК РФ).
    PREFERENCE_GIVEN_WITHOUT_LEGAL_BASIS = "preference_given_without_legal_basis"
    LAWFUL_DIFFERENTIATION = "lawful_differentiation"
    TERMS_UNIFORM_FOR_CATEGORY = "terms_uniform_for_category"
    # Понуждение к заключению и ничтожность условий (пункты 3 и 5 статьи 426 ГК РФ).
    COMPULSION_DEMANDED = "compulsion_demanded"
    TERMS_CONFLICT_WITH_PUBLIC_RULES = "terms_conflict_with_public_rules"


REQUIRED_PUBLIC_CONTRACT_PREDICATES = frozenset(PublicContractEvidencePredicate)


class PublicContractEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: PublicContractEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedPublicContractEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = PUBLIC_CONTRACT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[PublicContractEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedPublicContractEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Public-contract evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Public-contract evidence contains duplicate legal source refs.")
        return self


class PublicContractFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    public_contract_regime: bool
    counterparty_requested_contract: bool
    performance_possible: bool
    refusal_without_lawful_ground: bool
    preference_given_without_legal_basis: bool
    lawful_differentiation: bool
    terms_uniform_for_category: bool
    compulsion_demanded: bool
    terms_conflict_with_public_rules: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "PublicContractFactSet":
        if self.refusal_without_lawful_ground and not self.counterparty_requested_contract:
            raise ValueError("Отказ в заключении договора невозможен без обращения контрагента.")
        if self.compulsion_demanded and not self.counterparty_requested_contract:
            raise ValueError(
                "Требование о понуждении к заключению предполагает обращение контрагента."
            )
        if self.preference_given_without_legal_basis and not self.public_contract_regime:
            raise ValueError(
                "Недопустимое предпочтение возможно только в режиме публичного договора."
            )
        return self


class PublicContractFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class PublicContractEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: PublicContractFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[PublicContractFactProvenance] = Field(default_factory=list)


class PublicContractConstraintSet(BaseModel):
    id: str
    model_version: str = PUBLIC_CONTRACT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class PublicContractEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    duty_to_contract_applies: bool
    unlawful_refusal: bool
    unlawful_preference: bool
    uniform_terms_satisfied: bool
    compulsion_available: bool
    discriminatory_terms_void: bool
    requires_human_public_contract_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_public_contract_evidence(
    evidence: ReviewedPublicContractEvidence,
) -> PublicContractEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Public-contract evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Public-contract evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_PUBLIC_CONTRACT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed public-contract evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_PUBLIC_CONTRACT_PREDICATES
    }
    return PublicContractEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=PUBLIC_CONTRACT_MAPPING_VERSION,
        facts=PublicContractFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            PublicContractFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_PUBLIC_CONTRACT_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_public_contract_constraint_set(
    mapping: PublicContractEvidenceMappingResult,
) -> PublicContractConstraintSet:
    return PublicContractConstraintSet(
        id=f"public-contract-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "duty_to_contract_applies == public_contract_regime AND counterparty_requested_contract",
            "unlawful_refusal == duty_to_contract_applies AND performance_possible AND refusal_without_lawful_ground",
            "unlawful_preference == public_contract_regime AND preference_given_without_legal_basis",
            "uniform_terms_satisfied == lawful_differentiation OR NOT public_contract_regime OR terms_uniform_for_category",
            "compulsion_available == unlawful_refusal AND compulsion_demanded",
            "discriminatory_terms_void == public_contract_regime AND terms_conflict_with_public_rules",
            "requires_human_public_contract_assessment == unlawful_refusal OR unlawful_preference OR NOT uniform_terms_satisfied OR discriminatory_terms_void",
        ],
    )


def evaluate_public_contract_constraints(
    constraint_set: PublicContractConstraintSet,
    facts: PublicContractFactSet,
) -> PublicContractEvaluation:
    variables = {field_name: Bool(field_name) for field_name in PublicContractFactSet.model_fields}
    duty_to_contract_applies = Bool("duty_to_contract_applies")
    unlawful_refusal = Bool("unlawful_refusal")
    unlawful_preference = Bool("unlawful_preference")
    uniform_terms_satisfied = Bool("uniform_terms_satisfied")
    compulsion_available = Bool("compulsion_available")
    discriminatory_terms_void = Bool("discriminatory_terms_void")
    requires_human_public_contract_assessment = Bool("requires_human_public_contract_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        duty_to_contract_applies
        == And(
            variables["public_contract_regime"],
            variables["counterparty_requested_contract"],
        )
    )
    solver.add(
        unlawful_refusal
        == And(
            duty_to_contract_applies,
            variables["performance_possible"],
            variables["refusal_without_lawful_ground"],
        )
    )
    solver.add(
        unlawful_preference
        == And(
            variables["public_contract_regime"],
            variables["preference_given_without_legal_basis"],
        )
    )
    solver.add(
        uniform_terms_satisfied
        == Or(
            variables["lawful_differentiation"],
            Not(variables["public_contract_regime"]),
            variables["terms_uniform_for_category"],
        )
    )
    solver.add(compulsion_available == And(unlawful_refusal, variables["compulsion_demanded"]))
    solver.add(
        discriminatory_terms_void
        == And(
            variables["public_contract_regime"],
            variables["terms_conflict_with_public_rules"],
        )
    )
    solver.add(
        requires_human_public_contract_assessment
        == Or(
            unlawful_refusal,
            unlawful_preference,
            Not(uniform_terms_satisfied),
            discriminatory_terms_void,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return PublicContractEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            duty_to_contract_applies=False,
            unlawful_refusal=False,
            unlawful_preference=False,
            uniform_terms_satisfied=False,
            compulsion_available=False,
            discriminatory_terms_void=False,
            requires_human_public_contract_assessment=True,
            reasons_ru=["Набор фактов о публичном договоре противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Обязанность заключить публичный договор с обратившимся лицом действует "
            "(пункты 1 и 3 статьи 426 ГК РФ)."
            if truth(duty_to_contract_applies)
            else "Обязанность заключить публичный договор в данной ситуации не установлена."
        ),
    ]
    if truth(unlawful_refusal):
        reasons_ru.append(
            "Отказ от заключения договора при наличии возможности предоставить "
            "исполнение не допускается (пункт 3 статьи 426 ГК РФ)."
        )
    if truth(compulsion_available):
        reasons_ru.append(
            "При необоснованном уклонении доступно понуждение к заключению договора "
            "и возмещение убытков (пункт 3 статьи 426, пункт 4 статьи 445 ГК РФ)."
        )
    if truth(unlawful_preference):
        reasons_ru.append(
            "Оказание предпочтения одному лицу перед другим не допускается, кроме "
            "случаев, предусмотренных законом (пункт 1 статьи 426 ГК РФ)."
        )
    if truth(discriminatory_terms_void):
        reasons_ru.append(
            "Условия договора, не соответствующие требованиям публичного договора, "
            "ничтожны (пункт 5 статьи 426 ГК РФ)."
        )
    return PublicContractEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        duty_to_contract_applies=truth(duty_to_contract_applies),
        unlawful_refusal=truth(unlawful_refusal),
        unlawful_preference=truth(unlawful_preference),
        uniform_terms_satisfied=truth(uniform_terms_satisfied),
        compulsion_available=truth(compulsion_available),
        discriminatory_terms_void=truth(discriminatory_terms_void),
        requires_human_public_contract_assessment=truth(requires_human_public_contract_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о публичном договоре и не "
            "заменяет судебную оценку.",
            "Наличие законных оснований для отказа и различия условий оценивается "
            "экспертом и судом.",
        ],
    )
