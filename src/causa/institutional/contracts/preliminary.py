from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


PRELIMINARY_EVIDENCE_SCHEMA_VERSION = "contracts.preliminary-evidence.v0"
PRELIMINARY_MAPPING_VERSION = "contracts-reviewed-preliminary-to-facts-v0"
PRELIMINARY_MODEL_VERSION = "contracts-preliminary-article-429-v0"


class PreliminaryEvidencePredicate(str, Enum):
    # Заключение и действительность предварительного договора (пункты 1–3 статьи 429 ГК РФ).
    PRELIMINARY_CONTRACT_CONCLUDED = "preliminary_contract_concluded"
    FORM_REQUIREMENT_OBSERVED = "form_requirement_observed"
    MAIN_CONTRACT_SUBJECT_DEFINED = "main_contract_subject_defined"
    DISPUTED_TERMS_AGREED = "disputed_terms_agreed"
    # Срок заключения основного договора (пункты 4 и 6 статьи 429 ГК РФ).
    WITHIN_CONCLUSION_TERM = "within_conclusion_term"
    MAIN_CONTRACT_CONCLUDED_OR_PROPOSAL_MADE = "main_contract_concluded_or_proposal_made"
    # Уклонение и понуждение к заключению основного договора (пункт 5 статьи 429, статья 445 ГК РФ).
    PARTY_EVADES_CONCLUSION = "party_evades_conclusion"
    DEMAND_TO_CONCLUDE_MADE = "demand_to_conclude_made"
    DEMAND_WITHIN_SIX_MONTHS = "demand_within_six_months"


REQUIRED_PRELIMINARY_PREDICATES = frozenset(PreliminaryEvidencePredicate)


class PreliminaryEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: PreliminaryEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedPreliminaryEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = PRELIMINARY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[PreliminaryEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedPreliminaryEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Preliminary evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Preliminary evidence contains duplicate legal source refs.")
        return self


class PreliminaryFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    preliminary_contract_concluded: bool
    form_requirement_observed: bool
    main_contract_subject_defined: bool
    disputed_terms_agreed: bool
    within_conclusion_term: bool
    main_contract_concluded_or_proposal_made: bool
    party_evades_conclusion: bool
    demand_to_conclude_made: bool
    demand_within_six_months: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "PreliminaryFactSet":
        if self.party_evades_conclusion and not self.preliminary_contract_concluded:
            raise ValueError(
                "Уклонение от заключения основного договора невозможно без "
                "заключенного предварительного договора."
            )
        if self.demand_to_conclude_made and not self.party_evades_conclusion:
            raise ValueError(
                "Требование о понуждении к заключению заявляется только при "
                "уклонении стороны от заключения основного договора."
            )
        if self.demand_within_six_months and not self.demand_to_conclude_made:
            raise ValueError(
                "Соблюдение шестимесячного срока предполагает заявленное "
                "требование о понуждении к заключению."
            )
        return self


class PreliminaryFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class PreliminaryEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: PreliminaryFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[PreliminaryFactProvenance] = Field(default_factory=list)


class PreliminaryConstraintSet(BaseModel):
    id: str
    model_version: str = PRELIMINARY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class PreliminaryEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    preliminary_contract_valid: bool
    preliminary_form_void: bool
    conclusion_obligation_active: bool
    compulsion_to_conclude_available: bool
    damages_for_evasion_available: bool
    preliminary_obligations_terminated: bool
    requires_human_preliminary_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_preliminary_evidence(
    evidence: ReviewedPreliminaryEvidence,
) -> PreliminaryEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Preliminary evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Preliminary evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_PRELIMINARY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed preliminary evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_PRELIMINARY_PREDICATES
    }
    return PreliminaryEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=PRELIMINARY_MAPPING_VERSION,
        facts=PreliminaryFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            PreliminaryFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_PRELIMINARY_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_preliminary_constraint_set(
    mapping: PreliminaryEvidenceMappingResult,
) -> PreliminaryConstraintSet:
    return PreliminaryConstraintSet(
        id=f"preliminary-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "preliminary_contract_valid == preliminary_contract_concluded AND form_requirement_observed AND main_contract_subject_defined AND disputed_terms_agreed",
            "preliminary_form_void == preliminary_contract_concluded AND NOT form_requirement_observed",
            "conclusion_obligation_active == preliminary_contract_valid AND within_conclusion_term AND NOT main_contract_concluded_or_proposal_made",
            "compulsion_to_conclude_available == preliminary_contract_valid AND party_evades_conclusion AND demand_to_conclude_made AND demand_within_six_months",
            "damages_for_evasion_available == preliminary_contract_valid AND party_evades_conclusion AND demand_to_conclude_made AND demand_within_six_months",
            "preliminary_obligations_terminated == preliminary_contract_valid AND NOT within_conclusion_term AND NOT main_contract_concluded_or_proposal_made",
            "requires_human_preliminary_assessment == preliminary_form_void OR (party_evades_conclusion AND NOT compulsion_to_conclude_available)",
        ],
    )


def evaluate_preliminary_constraints(
    constraint_set: PreliminaryConstraintSet,
    facts: PreliminaryFactSet,
) -> PreliminaryEvaluation:
    variables = {field_name: Bool(field_name) for field_name in PreliminaryFactSet.model_fields}
    preliminary_contract_valid = Bool("preliminary_contract_valid")
    preliminary_form_void = Bool("preliminary_form_void")
    conclusion_obligation_active = Bool("conclusion_obligation_active")
    compulsion_to_conclude_available = Bool("compulsion_to_conclude_available")
    damages_for_evasion_available = Bool("damages_for_evasion_available")
    preliminary_obligations_terminated = Bool("preliminary_obligations_terminated")
    requires_human_preliminary_assessment = Bool("requires_human_preliminary_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        preliminary_contract_valid
        == And(
            variables["preliminary_contract_concluded"],
            variables["form_requirement_observed"],
            variables["main_contract_subject_defined"],
            variables["disputed_terms_agreed"],
        )
    )
    solver.add(
        preliminary_form_void
        == And(
            variables["preliminary_contract_concluded"],
            Not(variables["form_requirement_observed"]),
        )
    )
    solver.add(
        conclusion_obligation_active
        == And(
            preliminary_contract_valid,
            variables["within_conclusion_term"],
            Not(variables["main_contract_concluded_or_proposal_made"]),
        )
    )
    solver.add(
        compulsion_to_conclude_available
        == And(
            preliminary_contract_valid,
            variables["party_evades_conclusion"],
            variables["demand_to_conclude_made"],
            variables["demand_within_six_months"],
        )
    )
    solver.add(
        damages_for_evasion_available
        == And(
            preliminary_contract_valid,
            variables["party_evades_conclusion"],
            variables["demand_to_conclude_made"],
            variables["demand_within_six_months"],
        )
    )
    solver.add(
        preliminary_obligations_terminated
        == And(
            preliminary_contract_valid,
            Not(variables["within_conclusion_term"]),
            Not(variables["main_contract_concluded_or_proposal_made"]),
        )
    )
    solver.add(
        requires_human_preliminary_assessment
        == Or(
            preliminary_form_void,
            And(
                variables["party_evades_conclusion"],
                Not(compulsion_to_conclude_available),
            ),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return PreliminaryEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            preliminary_contract_valid=False,
            preliminary_form_void=False,
            conclusion_obligation_active=False,
            compulsion_to_conclude_available=False,
            damages_for_evasion_available=False,
            preliminary_obligations_terminated=False,
            requires_human_preliminary_assessment=True,
            reasons_ru=["Набор фактов о предварительном договоре противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Предварительный договор действителен (статья 429 ГК РФ)."
            if truth(preliminary_contract_valid)
            else "Предварительный договор не признается действительным."
        ),
    ]
    if truth(preliminary_form_void):
        reasons_ru.append(
            "Несоблюдение формы предварительного договора влечет его ничтожность "
            "(пункт 2 статьи 429 ГК РФ)."
        )
    if truth(conclusion_obligation_active):
        reasons_ru.append(
            "Обязанность заключить основной договор в согласованный срок сохраняется "
            "(пункты 4 и 5 статьи 429 ГК РФ)."
        )
    if truth(compulsion_to_conclude_available):
        reasons_ru.append(
            "При уклонении стороны доступно понуждение к заключению основного договора "
            "и возмещение убытков (пункт 5 статьи 429, пункт 4 статьи 445 ГК РФ)."
        )
    if truth(preliminary_obligations_terminated):
        reasons_ru.append(
            "Обязательства из предварительного договора прекращены по истечении срока "
            "без заключения основного договора и предложения его заключить "
            "(пункт 6 статьи 429 ГК РФ)."
        )
    return PreliminaryEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        preliminary_contract_valid=truth(preliminary_contract_valid),
        preliminary_form_void=truth(preliminary_form_void),
        conclusion_obligation_active=truth(conclusion_obligation_active),
        compulsion_to_conclude_available=truth(compulsion_to_conclude_available),
        damages_for_evasion_available=truth(damages_for_evasion_available),
        preliminary_obligations_terminated=truth(preliminary_obligations_terminated),
        requires_human_preliminary_assessment=truth(requires_human_preliminary_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о предварительном договоре "
            "и не заменяет судебную оценку.",
            "Определенность предмета основного договора и добросовестность сторон "
            "оцениваются экспертом и судом.",
        ],
    )
