from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


INTERPRETATION_EVIDENCE_SCHEMA_VERSION = "contracts.interpretation-evidence.v0"
INTERPRETATION_MAPPING_VERSION = "contracts-reviewed-interpretation-to-facts-v0"
INTERPRETATION_MODEL_VERSION = "contracts-interpretation-article-431-v0"


class InterpretationEvidencePredicate(str, Enum):
    # Буквальное толкование условия договора (абзац 1 статьи 431 ГК РФ).
    DISPUTED_TERM_PRESENT = "disputed_term_present"
    LITERAL_MEANING_CLEAR = "literal_meaning_clear"
    CONSISTENT_WITH_OTHER_TERMS = "consistent_with_other_terms"
    CONSISTENT_WITH_WHOLE_CONTRACT = "consistent_with_whole_contract"
    # Действительная общая воля сторон (абзац 2 статьи 431 ГК РФ).
    COMMON_INTENT_ESTABLISHED = "common_intent_established"
    PURPOSE_CONSIDERED = "purpose_considered"
    PRELIMINARY_NEGOTIATIONS_CONSIDERED = "preliminary_negotiations_considered"
    ESTABLISHED_PRACTICE_CONSIDERED = "established_practice_considered"
    USAGES_CONSIDERED = "usages_considered"
    SUBSEQUENT_CONDUCT_CONSIDERED = "subsequent_conduct_considered"
    # Толкование против стороны, подготовившей условие (contra proferentem).
    TERM_DRAFTED_BY_ONE_PARTY = "term_drafted_by_one_party"


REQUIRED_INTERPRETATION_PREDICATES = frozenset(InterpretationEvidencePredicate)


class InterpretationEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: InterpretationEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedInterpretationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = INTERPRETATION_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[InterpretationEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedInterpretationEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Interpretation evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Interpretation evidence contains duplicate legal source refs.")
        return self


class InterpretationFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    disputed_term_present: bool
    literal_meaning_clear: bool
    consistent_with_other_terms: bool
    consistent_with_whole_contract: bool
    common_intent_established: bool
    purpose_considered: bool
    preliminary_negotiations_considered: bool
    established_practice_considered: bool
    usages_considered: bool
    subsequent_conduct_considered: bool
    term_drafted_by_one_party: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "InterpretationFactSet":
        if self.common_intent_established and not self.disputed_term_present:
            raise ValueError("Common intent cannot be established without a disputed term.")
        return self


class InterpretationFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class InterpretationEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: InterpretationFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[InterpretationFactProvenance] = Field(default_factory=list)


class InterpretationConstraintSet(BaseModel):
    id: str
    model_version: str = INTERPRETATION_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class InterpretationEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    literal_interpretation_controls: bool
    systematic_reading_required: bool
    circumstances_considered: bool
    common_intent_interpretation_controls: bool
    interpretation_resolved: bool
    contra_proferentem_available: bool
    requires_human_interpretation_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_interpretation_evidence(
    evidence: ReviewedInterpretationEvidence,
) -> InterpretationEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Interpretation evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Interpretation evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_INTERPRETATION_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed interpretation evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_INTERPRETATION_PREDICATES
    }
    return InterpretationEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=INTERPRETATION_MAPPING_VERSION,
        facts=InterpretationFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            InterpretationFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_INTERPRETATION_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_interpretation_constraint_set(
    mapping: InterpretationEvidenceMappingResult,
) -> InterpretationConstraintSet:
    return InterpretationConstraintSet(
        id=f"interpretation-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "literal_interpretation_controls == disputed_term_present AND literal_meaning_clear AND consistent_with_other_terms AND consistent_with_whole_contract",
            "systematic_reading_required == disputed_term_present AND literal_meaning_clear AND NOT (consistent_with_other_terms AND consistent_with_whole_contract)",
            "circumstances_considered == purpose_considered OR preliminary_negotiations_considered OR established_practice_considered OR usages_considered OR subsequent_conduct_considered",
            "common_intent_interpretation_controls == disputed_term_present AND NOT literal_interpretation_controls AND common_intent_established AND circumstances_considered",
            "interpretation_resolved == literal_interpretation_controls OR common_intent_interpretation_controls",
            "contra_proferentem_available == disputed_term_present AND NOT interpretation_resolved AND term_drafted_by_one_party",
            "requires_human_interpretation_assessment == disputed_term_present AND NOT interpretation_resolved",
        ],
    )


def evaluate_interpretation_constraints(
    constraint_set: InterpretationConstraintSet,
    facts: InterpretationFactSet,
) -> InterpretationEvaluation:
    variables = {field_name: Bool(field_name) for field_name in InterpretationFactSet.model_fields}
    literal_interpretation_controls = Bool("literal_interpretation_controls")
    systematic_reading_required = Bool("systematic_reading_required")
    circumstances_considered = Bool("circumstances_considered")
    common_intent_interpretation_controls = Bool("common_intent_interpretation_controls")
    interpretation_resolved = Bool("interpretation_resolved")
    contra_proferentem_available = Bool("contra_proferentem_available")
    requires_human_interpretation_assessment = Bool("requires_human_interpretation_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        literal_interpretation_controls
        == And(
            variables["disputed_term_present"],
            variables["literal_meaning_clear"],
            variables["consistent_with_other_terms"],
            variables["consistent_with_whole_contract"],
        )
    )
    solver.add(
        systematic_reading_required
        == And(
            variables["disputed_term_present"],
            variables["literal_meaning_clear"],
            Not(
                And(
                    variables["consistent_with_other_terms"],
                    variables["consistent_with_whole_contract"],
                )
            ),
        )
    )
    solver.add(
        circumstances_considered
        == Or(
            variables["purpose_considered"],
            variables["preliminary_negotiations_considered"],
            variables["established_practice_considered"],
            variables["usages_considered"],
            variables["subsequent_conduct_considered"],
        )
    )
    solver.add(
        common_intent_interpretation_controls
        == And(
            variables["disputed_term_present"],
            Not(literal_interpretation_controls),
            variables["common_intent_established"],
            circumstances_considered,
        )
    )
    solver.add(
        interpretation_resolved
        == Or(literal_interpretation_controls, common_intent_interpretation_controls)
    )
    solver.add(
        contra_proferentem_available
        == And(
            variables["disputed_term_present"],
            Not(interpretation_resolved),
            variables["term_drafted_by_one_party"],
        )
    )
    solver.add(
        requires_human_interpretation_assessment
        == And(variables["disputed_term_present"], Not(interpretation_resolved))
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return InterpretationEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            literal_interpretation_controls=False,
            systematic_reading_required=False,
            circumstances_considered=False,
            common_intent_interpretation_controls=False,
            interpretation_resolved=False,
            contra_proferentem_available=False,
            requires_human_interpretation_assessment=True,
            reasons_ru=["Набор фактов о толковании договора противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = []
    if truth(literal_interpretation_controls):
        reasons_ru.append(
            "Содержание условия определяется буквальным значением слов и выражений "
            "(абзац 1 статьи 431 ГК РФ)."
        )
    elif truth(systematic_reading_required):
        reasons_ru.append(
            "Буквальное значение неясно; условие сопоставляется с другими условиями "
            "и смыслом договора в целом."
        )
    if truth(common_intent_interpretation_controls):
        reasons_ru.append(
            "Содержание условия определяется действительной общей волей сторон с учетом "
            "цели договора и иных обстоятельств (абзац 2 статьи 431 ГК РФ)."
        )
    if truth(contra_proferentem_available):
        reasons_ru.append(
            "Неустраненная неясность толкуется против стороны, подготовившей условие."
        )
    if truth(requires_human_interpretation_assessment):
        reasons_ru.append("Содержание спорного условия не установлено формально и требует юриста.")
    if not facts.disputed_term_present:
        reasons_ru.append("Спор о толковании условия договора не заявлен.")
    return InterpretationEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        literal_interpretation_controls=truth(literal_interpretation_controls),
        systematic_reading_required=truth(systematic_reading_required),
        circumstances_considered=truth(circumstances_considered),
        common_intent_interpretation_controls=truth(common_intent_interpretation_controls),
        interpretation_resolved=truth(interpretation_resolved),
        contra_proferentem_available=truth(contra_proferentem_available),
        requires_human_interpretation_assessment=truth(requires_human_interpretation_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальную последовательность толкования и не заменяет судебную оценку.",
            "Действительный смысл условия, воля сторон и оценка доказательств устанавливаются экспертом и судом.",
        ],
    )
