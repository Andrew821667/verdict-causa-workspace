from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


GENERAL_OBLIGATIONS_EVIDENCE_SCHEMA_VERSION = "contracts.general-obligations-evidence.v0"
GENERAL_OBLIGATIONS_MAPPING_VERSION = "contracts-reviewed-general-obligations-to-facts-v0"
GENERAL_OBLIGATIONS_MODEL_VERSION = "contracts-general-obligations-articles-307-3083-v0"


class GeneralObligationsEvidencePredicate(str, Enum):
    # Понятие обязательства и его стороны (статьи 307 и 308 ГК РФ).
    OBLIGATION_ESTABLISHED = "obligation_established"
    GOOD_FAITH_OBSERVED = "good_faith_observed"
    OBLIGATION_BINDS_THIRD_PARTY_CLAIMED = "obligation_binds_third_party_claimed"
    # Альтернативное и факультативное обязательство (статьи 308.1 и 308.2 ГК РФ).
    ALTERNATIVE_OBLIGATION = "alternative_obligation"
    CHOICE_MADE_IN_ALTERNATIVE = "choice_made_in_alternative"
    FACULTATIVE_OBLIGATION = "facultative_obligation"
    FACULTATIVE_SUBSTITUTION_PROVIDED = "facultative_substitution_provided"
    # Защита прав кредитора (статья 308.3 ГК РФ).
    SPECIFIC_PERFORMANCE_DEMANDED = "specific_performance_demanded"
    PERFORMANCE_UNIQUELY_PERSONAL = "performance_uniquely_personal"
    JUDICIAL_ACT_NON_COMPLIANCE = "judicial_act_non_compliance"


REQUIRED_GENERAL_OBLIGATIONS_PREDICATES = frozenset(GeneralObligationsEvidencePredicate)


class GeneralObligationsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: GeneralObligationsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedGeneralObligationsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = GENERAL_OBLIGATIONS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[GeneralObligationsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedGeneralObligationsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("General obligations evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("General obligations evidence contains duplicate legal source refs.")
        return self


class GeneralObligationsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    obligation_established: bool
    good_faith_observed: bool
    obligation_binds_third_party_claimed: bool
    alternative_obligation: bool
    choice_made_in_alternative: bool
    facultative_obligation: bool
    facultative_substitution_provided: bool
    specific_performance_demanded: bool
    performance_uniquely_personal: bool
    judicial_act_non_compliance: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "GeneralObligationsFactSet":
        if self.choice_made_in_alternative and not self.alternative_obligation:
            raise ValueError(
                "Выбор предмета исполнения невозможен без альтернативного обязательства."
            )
        if self.facultative_substitution_provided and not self.facultative_obligation:
            raise ValueError(
                "Факультативное исполнение невозможно без факультативного обязательства."
            )
        return self


class GeneralObligationsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class GeneralObligationsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: GeneralObligationsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[GeneralObligationsFactProvenance] = Field(default_factory=list)


class GeneralObligationsConstraintSet(BaseModel):
    id: str
    model_version: str = GENERAL_OBLIGATIONS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class GeneralObligationsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    creditor_may_demand_performance: bool
    third_party_binding_rejected: bool
    alternative_obligation_fixed: bool
    creditor_limited_to_principal: bool
    specific_performance_available: bool
    astreinte_available: bool
    good_faith_breach_flagged: bool
    requires_human_general_obligations_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_general_obligations_evidence(
    evidence: ReviewedGeneralObligationsEvidence,
) -> GeneralObligationsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("General obligations evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("General obligations evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_GENERAL_OBLIGATIONS_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed general obligations evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_GENERAL_OBLIGATIONS_PREDICATES
    }
    return GeneralObligationsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=GENERAL_OBLIGATIONS_MAPPING_VERSION,
        facts=GeneralObligationsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            GeneralObligationsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_GENERAL_OBLIGATIONS_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_general_obligations_constraint_set(
    mapping: GeneralObligationsEvidenceMappingResult,
) -> GeneralObligationsConstraintSet:
    return GeneralObligationsConstraintSet(
        id=f"general-obligations-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "creditor_may_demand_performance == obligation_established",
            "third_party_binding_rejected == obligation_binds_third_party_claimed",
            "alternative_obligation_fixed == alternative_obligation AND choice_made_in_alternative",
            "creditor_limited_to_principal == facultative_obligation AND NOT facultative_substitution_provided",
            "specific_performance_available == specific_performance_demanded AND obligation_established AND NOT performance_uniquely_personal",
            "astreinte_available == judicial_act_non_compliance",
            "good_faith_breach_flagged == obligation_established AND NOT good_faith_observed",
            "requires_human_general_obligations_assessment == obligation_binds_third_party_claimed OR (obligation_established AND NOT good_faith_observed) OR (facultative_obligation AND NOT facultative_substitution_provided) OR judicial_act_non_compliance OR (alternative_obligation AND NOT choice_made_in_alternative) OR (specific_performance_demanded AND performance_uniquely_personal)",
        ],
    )


def evaluate_general_obligations_constraints(
    constraint_set: GeneralObligationsConstraintSet,
    facts: GeneralObligationsFactSet,
) -> GeneralObligationsEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in GeneralObligationsFactSet.model_fields
    }
    creditor_may_demand_performance = Bool("creditor_may_demand_performance")
    third_party_binding_rejected = Bool("third_party_binding_rejected")
    alternative_obligation_fixed = Bool("alternative_obligation_fixed")
    creditor_limited_to_principal = Bool("creditor_limited_to_principal")
    specific_performance_available = Bool("specific_performance_available")
    astreinte_available = Bool("astreinte_available")
    good_faith_breach_flagged = Bool("good_faith_breach_flagged")
    requires_human_general_obligations_assessment = Bool(
        "requires_human_general_obligations_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(creditor_may_demand_performance == variables["obligation_established"])
    solver.add(third_party_binding_rejected == variables["obligation_binds_third_party_claimed"])
    solver.add(
        alternative_obligation_fixed
        == And(variables["alternative_obligation"], variables["choice_made_in_alternative"])
    )
    solver.add(
        creditor_limited_to_principal
        == And(
            variables["facultative_obligation"],
            Not(variables["facultative_substitution_provided"]),
        )
    )
    solver.add(
        specific_performance_available
        == And(
            variables["specific_performance_demanded"],
            variables["obligation_established"],
            Not(variables["performance_uniquely_personal"]),
        )
    )
    solver.add(astreinte_available == variables["judicial_act_non_compliance"])
    solver.add(
        good_faith_breach_flagged
        == And(variables["obligation_established"], Not(variables["good_faith_observed"]))
    )
    solver.add(
        requires_human_general_obligations_assessment
        == Or(
            variables["obligation_binds_third_party_claimed"],
            And(variables["obligation_established"], Not(variables["good_faith_observed"])),
            And(
                variables["facultative_obligation"],
                Not(variables["facultative_substitution_provided"]),
            ),
            variables["judicial_act_non_compliance"],
            And(
                variables["alternative_obligation"],
                Not(variables["choice_made_in_alternative"]),
            ),
            And(
                variables["specific_performance_demanded"],
                variables["performance_uniquely_personal"],
            ),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return GeneralObligationsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            creditor_may_demand_performance=False,
            third_party_binding_rejected=False,
            alternative_obligation_fixed=False,
            creditor_limited_to_principal=False,
            specific_performance_available=False,
            astreinte_available=False,
            good_faith_breach_flagged=False,
            requires_human_general_obligations_assessment=True,
            reasons_ru=["Набор фактов об общих положениях об обязательствах противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Обязательство установлено; кредитор вправе требовать от должника исполнения "
            "обязанности (статья 307 ГК РФ)."
            if truth(creditor_may_demand_performance)
            else "Обязательство не признаётся установленным."
        ),
    ]
    if truth(third_party_binding_rejected):
        reasons_ru.append(
            "Обязательство не создаёт обязанностей для лиц, не участвующих в нём в "
            "качестве сторон (пункт 3 статьи 308 ГК РФ)."
        )
    if truth(alternative_obligation_fixed):
        reasons_ru.append(
            "После выбора предмета исполнения альтернативное обязательство перестаёт быть "
            "альтернативным (статья 308.1 ГК РФ)."
        )
    if truth(creditor_limited_to_principal):
        reasons_ru.append(
            "При непредоставлении факультативного исполнения кредитор вправе требовать "
            "только основное исполнение (статья 308.2 ГК РФ)."
        )
    if truth(specific_performance_available):
        reasons_ru.append(
            "Кредитор вправе требовать исполнения обязательства в натуре, если иное не "
            "предусмотрено и исполнение объективно возможно (статья 308.3 ГК РФ)."
        )
    if truth(astreinte_available):
        reasons_ru.append(
            "На случай неисполнения судебного акта суд может присудить денежную сумму в "
            "пользу кредитора (пункт 1 статьи 308.3 ГК РФ)."
        )
    if truth(good_faith_breach_flagged):
        reasons_ru.append(
            "Установление, исполнение и прекращение обязательства должны отвечать "
            "требованию добросовестности (пункт 3 статьи 307 ГК РФ)."
        )
    return GeneralObligationsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        creditor_may_demand_performance=truth(creditor_may_demand_performance),
        third_party_binding_rejected=truth(third_party_binding_rejected),
        alternative_obligation_fixed=truth(alternative_obligation_fixed),
        creditor_limited_to_principal=truth(creditor_limited_to_principal),
        specific_performance_available=truth(specific_performance_available),
        astreinte_available=truth(astreinte_available),
        good_faith_breach_flagged=truth(good_faith_breach_flagged),
        requires_human_general_obligations_assessment=truth(
            requires_human_general_obligations_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные общие положения об обязательствах и не "
            "заменяет судебную оценку.",
            "Добросовестность сторон, возможность исполнения в натуре и размер судебной "
            "неустойки оцениваются экспертом и судом.",
        ],
    )
