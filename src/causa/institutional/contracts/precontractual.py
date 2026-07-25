from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


PRECONTRACTUAL_EVIDENCE_SCHEMA_VERSION = "contracts.precontractual-evidence.v0"
PRECONTRACTUAL_MAPPING_VERSION = "contracts-reviewed-precontractual-to-facts-v0"
PRECONTRACTUAL_MODEL_VERSION = "contracts-precontractual-article-434-1-v0"


class PrecontractualEvidencePredicate(str, Enum):
    # Переговоры и недобросовестное поведение (пункты 1 и 2 статьи 434.1 ГК РФ).
    NEGOTIATIONS_ENTERED = "negotiations_entered"
    INCOMPLETE_OR_FALSE_INFORMATION_PROVIDED = "incomplete_or_false_information_provided"
    ABRUPT_UNJUSTIFIED_BREAKOFF = "abrupt_unjustified_breakoff"
    COUNTERPARTY_COULD_NOT_REASONABLY_EXPECT_BREAKOFF = (
        "counterparty_could_not_reasonably_expect_breakoff"
    )
    # Конфиденциальность (пункт 4 статьи 434.1 ГК РФ).
    CONFIDENTIAL_INFORMATION_RECEIVED = "confidential_information_received"
    CONFIDENTIAL_INFORMATION_MISUSED = "confidential_information_misused"
    # Убытки и ограничение ответственности (пункты 3 и 5 статьи 434.1 ГК РФ).
    LOSSES_INCURRED = "losses_incurred"
    DAMAGES_CLAIMED = "damages_claimed"
    LIABILITY_LIMITATION_AGREEMENT_PRESENT = "liability_limitation_agreement_present"


REQUIRED_PRECONTRACTUAL_PREDICATES = frozenset(PrecontractualEvidencePredicate)


class PrecontractualEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: PrecontractualEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedPrecontractualEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = PRECONTRACTUAL_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[PrecontractualEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedPrecontractualEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Precontractual evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Precontractual evidence contains duplicate legal source refs.")
        return self


class PrecontractualFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    negotiations_entered: bool
    incomplete_or_false_information_provided: bool
    abrupt_unjustified_breakoff: bool
    counterparty_could_not_reasonably_expect_breakoff: bool
    confidential_information_received: bool
    confidential_information_misused: bool
    losses_incurred: bool
    damages_claimed: bool
    liability_limitation_agreement_present: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "PrecontractualFactSet":
        if self.incomplete_or_false_information_provided and not self.negotiations_entered:
            raise ValueError(
                "Недобросовестное предоставление информации невозможно без переговоров."
            )
        if self.abrupt_unjustified_breakoff and not self.negotiations_entered:
            raise ValueError("Прекращение переговоров невозможно без вступления в переговоры.")
        if (
            self.counterparty_could_not_reasonably_expect_breakoff
            and not self.abrupt_unjustified_breakoff
        ):
            raise ValueError("Оценка ожидаемости прекращения предполагает прекращение переговоров.")
        if self.confidential_information_misused and not self.confidential_information_received:
            raise ValueError(
                "Ненадлежащее использование конфиденциальной информации невозможно без "
                "её получения."
            )
        return self


class PrecontractualFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class PrecontractualEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: PrecontractualFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[PrecontractualFactProvenance] = Field(default_factory=list)


class PrecontractualConstraintSet(BaseModel):
    id: str
    model_version: str = PRECONTRACTUAL_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class PrecontractualEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    bad_faith_negotiation: bool
    confidentiality_breach: bool
    precontractual_liability_present: bool
    damages_available: bool
    liability_limitation_void: bool
    requires_human_precontractual_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_precontractual_evidence(
    evidence: ReviewedPrecontractualEvidence,
) -> PrecontractualEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Precontractual evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Precontractual evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_PRECONTRACTUAL_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed precontractual evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_PRECONTRACTUAL_PREDICATES
    }
    return PrecontractualEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=PRECONTRACTUAL_MAPPING_VERSION,
        facts=PrecontractualFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            PrecontractualFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_PRECONTRACTUAL_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_precontractual_constraint_set(
    mapping: PrecontractualEvidenceMappingResult,
) -> PrecontractualConstraintSet:
    return PrecontractualConstraintSet(
        id=f"precontractual-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "bad_faith_negotiation == negotiations_entered AND (incomplete_or_false_information_provided OR (abrupt_unjustified_breakoff AND counterparty_could_not_reasonably_expect_breakoff))",
            "confidentiality_breach == confidential_information_received AND confidential_information_misused",
            "precontractual_liability_present == bad_faith_negotiation OR confidentiality_breach",
            "damages_available == precontractual_liability_present AND losses_incurred AND damages_claimed",
            "liability_limitation_void == liability_limitation_agreement_present",
            "requires_human_precontractual_assessment == precontractual_liability_present OR liability_limitation_void",
        ],
    )


def evaluate_precontractual_constraints(
    constraint_set: PrecontractualConstraintSet,
    facts: PrecontractualFactSet,
) -> PrecontractualEvaluation:
    variables = {field_name: Bool(field_name) for field_name in PrecontractualFactSet.model_fields}
    bad_faith_negotiation = Bool("bad_faith_negotiation")
    confidentiality_breach = Bool("confidentiality_breach")
    precontractual_liability_present = Bool("precontractual_liability_present")
    damages_available = Bool("damages_available")
    liability_limitation_void = Bool("liability_limitation_void")
    requires_human_precontractual_assessment = Bool("requires_human_precontractual_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        bad_faith_negotiation
        == And(
            variables["negotiations_entered"],
            Or(
                variables["incomplete_or_false_information_provided"],
                And(
                    variables["abrupt_unjustified_breakoff"],
                    variables["counterparty_could_not_reasonably_expect_breakoff"],
                ),
            ),
        )
    )
    solver.add(
        confidentiality_breach
        == And(
            variables["confidential_information_received"],
            variables["confidential_information_misused"],
        )
    )
    solver.add(
        precontractual_liability_present == Or(bad_faith_negotiation, confidentiality_breach)
    )
    solver.add(
        damages_available
        == And(
            precontractual_liability_present,
            variables["losses_incurred"],
            variables["damages_claimed"],
        )
    )
    solver.add(liability_limitation_void == variables["liability_limitation_agreement_present"])
    solver.add(
        requires_human_precontractual_assessment
        == Or(precontractual_liability_present, liability_limitation_void)
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return PrecontractualEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            bad_faith_negotiation=False,
            confidentiality_breach=False,
            precontractual_liability_present=False,
            damages_available=False,
            liability_limitation_void=False,
            requires_human_precontractual_assessment=True,
            reasons_ru=["Набор фактов о преддоговорной ответственности противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Установлена недобросовестность при ведении переговоров или нарушение "
            "конфиденциальности (статья 434.1 ГК РФ)."
            if truth(precontractual_liability_present)
            else "Недобросовестность при ведении переговоров не установлена."
        ),
    ]
    if truth(bad_faith_negotiation):
        reasons_ru.append(
            "Недобросовестное ведение или прекращение переговоров нарушает обязанность "
            "действовать добросовестно (пункт 2 статьи 434.1 ГК РФ)."
        )
    if truth(confidentiality_breach):
        reasons_ru.append(
            "Ненадлежащее раскрытие или использование конфиденциальной информации, "
            "полученной в ходе переговоров, влечёт ответственность "
            "(пункт 4 статьи 434.1 ГК РФ)."
        )
    if truth(damages_available):
        reasons_ru.append(
            "Причинённые недобросовестным поведением убытки подлежат возмещению "
            "независимо от того, был ли заключён договор (пункты 3 и 7 статьи 434.1 ГК РФ)."
        )
    if truth(liability_limitation_void):
        reasons_ru.append(
            "Соглашение об ограничении ответственности за недобросовестные действия "
            "при переговорах ничтожно (пункт 5 статьи 434.1 ГК РФ)."
        )
    return PrecontractualEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        bad_faith_negotiation=truth(bad_faith_negotiation),
        confidentiality_breach=truth(confidentiality_breach),
        precontractual_liability_present=truth(precontractual_liability_present),
        damages_available=truth(damages_available),
        liability_limitation_void=truth(liability_limitation_void),
        requires_human_precontractual_assessment=truth(requires_human_precontractual_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о преддоговорной ответственности "
            "и не заменяет судебную оценку.",
            "Добросовестность сторон и оправданность прекращения переговоров оцениваются "
            "экспертом и судом.",
        ],
    )
