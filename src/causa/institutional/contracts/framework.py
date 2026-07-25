from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


FRAMEWORK_EVIDENCE_SCHEMA_VERSION = "contracts.framework-evidence.v0"
FRAMEWORK_MAPPING_VERSION = "contracts-reviewed-framework-to-facts-v0"
FRAMEWORK_MODEL_VERSION = "contracts-framework-subscription-articles-429-1-429-4-v0"


class FrameworkEvidencePredicate(str, Enum):
    # Рамочный договор (статья 429.1 ГК РФ).
    FRAMEWORK_AGREEMENT_CONCLUDED = "framework_agreement_concluded"
    FRAMEWORK_GENERAL_CONDITIONS_DEFINED = "framework_general_conditions_defined"
    SPECIFYING_AGREEMENT_CONCLUDED = "specifying_agreement_concluded"
    SPECIFYING_AGREEMENT_OVERRIDES = "specifying_agreement_overrides"
    # Абонентский договор (статья 429.4 ГК РФ).
    SUBSCRIPTION_AGREEMENT_CONCLUDED = "subscription_agreement_concluded"
    SUBSCRIPTION_PAYMENT_AGREED = "subscription_payment_agreed"
    SUBSCRIBER_DEMANDED_PERFORMANCE = "subscriber_demanded_performance"
    SUBSCRIPTION_PAYMENT_EXCUSED_BY_CONTRACT = "subscription_payment_excused_by_contract"


REQUIRED_FRAMEWORK_PREDICATES = frozenset(FrameworkEvidencePredicate)


class FrameworkEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: FrameworkEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedFrameworkEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = FRAMEWORK_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[FrameworkEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedFrameworkEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Framework evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Framework evidence contains duplicate legal source refs.")
        return self


class FrameworkFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    framework_agreement_concluded: bool
    framework_general_conditions_defined: bool
    specifying_agreement_concluded: bool
    specifying_agreement_overrides: bool
    subscription_agreement_concluded: bool
    subscription_payment_agreed: bool
    subscriber_demanded_performance: bool
    subscription_payment_excused_by_contract: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "FrameworkFactSet":
        if self.framework_general_conditions_defined and not self.framework_agreement_concluded:
            raise ValueError("Общие условия невозможны без заключённого рамочного договора.")
        if self.specifying_agreement_concluded and not self.framework_agreement_concluded:
            raise ValueError("Конкретизирующее соглашение невозможно без рамочного договора.")
        if self.specifying_agreement_overrides and not self.specifying_agreement_concluded:
            raise ValueError("Иное регулирование невозможно без конкретизирующего соглашения.")
        if self.subscription_payment_agreed and not self.subscription_agreement_concluded:
            raise ValueError(
                "Платежи по абоненту невозможны без заключённого абонентского договора."
            )
        if self.subscriber_demanded_performance and not self.subscription_agreement_concluded:
            raise ValueError(
                "Требование абонента невозможно без заключённого абонентского договора."
            )
        return self


class FrameworkFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class FrameworkEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: FrameworkFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[FrameworkFactProvenance] = Field(default_factory=list)


class FrameworkConstraintSet(BaseModel):
    id: str
    model_version: str = FRAMEWORK_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class FrameworkEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    framework_agreement_valid: bool
    framework_terms_apply_to_relations: bool
    specifying_agreement_on_framework: bool
    subscription_agreement_valid: bool
    subscription_payment_due_without_demand: bool
    subscriber_entitled_to_demand: bool
    requires_human_framework_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_framework_evidence(
    evidence: ReviewedFrameworkEvidence,
) -> FrameworkEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Framework evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Framework evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_FRAMEWORK_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed framework evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_FRAMEWORK_PREDICATES
    }
    return FrameworkEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=FRAMEWORK_MAPPING_VERSION,
        facts=FrameworkFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            FrameworkFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_FRAMEWORK_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_framework_constraint_set(
    mapping: FrameworkEvidenceMappingResult,
) -> FrameworkConstraintSet:
    return FrameworkConstraintSet(
        id=f"framework-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "framework_agreement_valid == framework_agreement_concluded AND framework_general_conditions_defined",
            "framework_terms_apply_to_relations == framework_agreement_valid AND NOT specifying_agreement_overrides",
            "specifying_agreement_on_framework == framework_agreement_valid AND specifying_agreement_concluded",
            "subscription_agreement_valid == subscription_agreement_concluded AND subscription_payment_agreed",
            "subscription_payment_due_without_demand == subscription_agreement_valid AND NOT subscriber_demanded_performance AND NOT subscription_payment_excused_by_contract",
            "subscriber_entitled_to_demand == subscription_agreement_valid",
            "requires_human_framework_assessment == subscription_payment_due_without_demand OR (framework_terms_apply_to_relations AND NOT specifying_agreement_concluded)",
        ],
    )


def evaluate_framework_constraints(
    constraint_set: FrameworkConstraintSet,
    facts: FrameworkFactSet,
) -> FrameworkEvaluation:
    variables = {field_name: Bool(field_name) for field_name in FrameworkFactSet.model_fields}
    framework_agreement_valid = Bool("framework_agreement_valid")
    framework_terms_apply_to_relations = Bool("framework_terms_apply_to_relations")
    specifying_agreement_on_framework = Bool("specifying_agreement_on_framework")
    subscription_agreement_valid = Bool("subscription_agreement_valid")
    subscription_payment_due_without_demand = Bool("subscription_payment_due_without_demand")
    subscriber_entitled_to_demand = Bool("subscriber_entitled_to_demand")
    requires_human_framework_assessment = Bool("requires_human_framework_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        framework_agreement_valid
        == And(
            variables["framework_agreement_concluded"],
            variables["framework_general_conditions_defined"],
        )
    )
    solver.add(
        framework_terms_apply_to_relations
        == And(framework_agreement_valid, Not(variables["specifying_agreement_overrides"]))
    )
    solver.add(
        specifying_agreement_on_framework
        == And(framework_agreement_valid, variables["specifying_agreement_concluded"])
    )
    solver.add(
        subscription_agreement_valid
        == And(
            variables["subscription_agreement_concluded"],
            variables["subscription_payment_agreed"],
        )
    )
    solver.add(
        subscription_payment_due_without_demand
        == And(
            subscription_agreement_valid,
            Not(variables["subscriber_demanded_performance"]),
            Not(variables["subscription_payment_excused_by_contract"]),
        )
    )
    solver.add(subscriber_entitled_to_demand == subscription_agreement_valid)
    solver.add(
        requires_human_framework_assessment
        == Or(
            subscription_payment_due_without_demand,
            And(
                framework_terms_apply_to_relations,
                Not(variables["specifying_agreement_concluded"]),
            ),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return FrameworkEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            framework_agreement_valid=False,
            framework_terms_apply_to_relations=False,
            specifying_agreement_on_framework=False,
            subscription_agreement_valid=False,
            subscription_payment_due_without_demand=False,
            subscriber_entitled_to_demand=False,
            requires_human_framework_assessment=True,
            reasons_ru=["Набор фактов о рамочном и абонентском договоре противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Рамочный договор определяет общие условия обязательственных "
            "взаимоотношений сторон (пункт 1 статьи 429.1 ГК РФ)."
            if truth(framework_agreement_valid)
            else "Рамочный договор не признаётся заключённым с определёнными общими условиями."
        ),
    ]
    if truth(specifying_agreement_on_framework):
        reasons_ru.append(
            "Общие условия рамочного договора конкретизированы отдельным договором, "
            "заявкой или иным образом (пункт 1 статьи 429.1 ГК РФ)."
        )
    if truth(framework_terms_apply_to_relations):
        reasons_ru.append(
            "К отношениям сторон, не урегулированным отдельными договорами, применяются "
            "общие условия рамочного договора (пункт 2 статьи 429.1 ГК РФ)."
        )
    if truth(subscription_agreement_valid):
        reasons_ru.append(
            "Абонентский договор предусматривает платежи за право требовать исполнение "
            "по требованию абонента (пункт 1 статьи 429.4 ГК РФ)."
        )
    if truth(subscription_payment_due_without_demand):
        reasons_ru.append(
            "Абонент обязан вносить платежи независимо от того, было ли затребовано "
            "исполнение, если иное не предусмотрено законом или договором "
            "(пункт 2 статьи 429.4 ГК РФ)."
        )
    return FrameworkEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        framework_agreement_valid=truth(framework_agreement_valid),
        framework_terms_apply_to_relations=truth(framework_terms_apply_to_relations),
        specifying_agreement_on_framework=truth(specifying_agreement_on_framework),
        subscription_agreement_valid=truth(subscription_agreement_valid),
        subscription_payment_due_without_demand=truth(subscription_payment_due_without_demand),
        subscriber_entitled_to_demand=truth(subscriber_entitled_to_demand),
        requires_human_framework_assessment=truth(requires_human_framework_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о рамочном и абонентском "
            "договоре и не заменяет судебную оценку.",
            "Существо обязательства, содержание общих условий и условия о плате "
            "оцениваются экспертом и судом.",
        ],
    )
