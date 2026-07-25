from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


OPTION_EVIDENCE_SCHEMA_VERSION = "contracts.option-evidence.v0"
OPTION_MAPPING_VERSION = "contracts-reviewed-option-to-facts-v0"
OPTION_MODEL_VERSION = "contracts-option-articles-429-2-429-3-v0"


class OptionEvidencePredicate(str, Enum):
    # Опцион на заключение договора (статья 429.2 ГК РФ).
    OPTION_TO_CONCLUDE_GRANTED = "option_to_conclude_granted"
    OPTION_ESSENTIAL_TERMS_DEFINED = "option_essential_terms_defined"
    OPTION_CONSIDERATION_VALID = "option_consideration_valid"
    OPTION_ACCEPTANCE_WITHIN_TERM = "option_acceptance_within_term"
    OPTION_RIGHT_ASSIGNED = "option_right_assigned"
    ASSIGNMENT_PROHIBITED = "assignment_prohibited"
    # Опционный договор (статья 429.3 ГК РФ).
    OPTION_CONTRACT_CONCLUDED = "option_contract_concluded"
    OPTION_CONTRACT_DEMAND_WITHIN_TERM = "option_contract_demand_within_term"
    OPTION_CONTRACT_PAYMENT_MADE = "option_contract_payment_made"


REQUIRED_OPTION_PREDICATES = frozenset(OptionEvidencePredicate)


class OptionEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: OptionEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedOptionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = OPTION_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[OptionEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedOptionEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Option evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Option evidence contains duplicate legal source refs.")
        return self


class OptionFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    option_to_conclude_granted: bool
    option_essential_terms_defined: bool
    option_consideration_valid: bool
    option_acceptance_within_term: bool
    option_right_assigned: bool
    assignment_prohibited: bool
    option_contract_concluded: bool
    option_contract_demand_within_term: bool
    option_contract_payment_made: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "OptionFactSet":
        if self.option_essential_terms_defined and not self.option_to_conclude_granted:
            raise ValueError(
                "Существенные условия опциона невозможны без предоставленного опциона."
            )
        if self.option_acceptance_within_term and not self.option_to_conclude_granted:
            raise ValueError("Акцепт опциона невозможен без предоставленного опциона.")
        if self.option_contract_demand_within_term and not self.option_contract_concluded:
            raise ValueError(
                "Требование по опционному договору невозможно без заключённого опционного договора."
            )
        if self.option_contract_payment_made and not self.option_contract_concluded:
            raise ValueError(
                "Платёж по опционному договору невозможен без заключённого опционного договора."
            )
        return self


class OptionFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class OptionEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: OptionFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[OptionFactProvenance] = Field(default_factory=list)


class OptionConstraintSet(BaseModel):
    id: str
    model_version: str = OPTION_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class OptionEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    option_offer_valid: bool
    main_contract_formed_by_option: bool
    option_lapsed_unexercised: bool
    option_contract_demand_enforceable: bool
    option_contract_terminated_by_expiry: bool
    option_payment_non_refundable: bool
    option_right_transferable: bool
    requires_human_option_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_option_evidence(
    evidence: ReviewedOptionEvidence,
) -> OptionEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Option evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Option evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_OPTION_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed option evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_OPTION_PREDICATES
    }
    return OptionEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=OPTION_MAPPING_VERSION,
        facts=OptionFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            OptionFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_OPTION_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_option_constraint_set(
    mapping: OptionEvidenceMappingResult,
) -> OptionConstraintSet:
    return OptionConstraintSet(
        id=f"option-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "option_offer_valid == option_to_conclude_granted AND option_essential_terms_defined AND option_consideration_valid",
            "main_contract_formed_by_option == option_offer_valid AND option_acceptance_within_term",
            "option_lapsed_unexercised == option_offer_valid AND NOT option_acceptance_within_term",
            "option_contract_demand_enforceable == option_contract_concluded AND option_contract_demand_within_term",
            "option_contract_terminated_by_expiry == option_contract_concluded AND NOT option_contract_demand_within_term",
            "option_payment_non_refundable == option_contract_terminated_by_expiry AND option_contract_payment_made",
            "option_right_transferable == option_right_assigned AND NOT assignment_prohibited",
            "requires_human_option_assessment == option_lapsed_unexercised OR option_contract_terminated_by_expiry OR (option_right_assigned AND assignment_prohibited)",
        ],
    )


def evaluate_option_constraints(
    constraint_set: OptionConstraintSet,
    facts: OptionFactSet,
) -> OptionEvaluation:
    variables = {field_name: Bool(field_name) for field_name in OptionFactSet.model_fields}
    option_offer_valid = Bool("option_offer_valid")
    main_contract_formed_by_option = Bool("main_contract_formed_by_option")
    option_lapsed_unexercised = Bool("option_lapsed_unexercised")
    option_contract_demand_enforceable = Bool("option_contract_demand_enforceable")
    option_contract_terminated_by_expiry = Bool("option_contract_terminated_by_expiry")
    option_payment_non_refundable = Bool("option_payment_non_refundable")
    option_right_transferable = Bool("option_right_transferable")
    requires_human_option_assessment = Bool("requires_human_option_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        option_offer_valid
        == And(
            variables["option_to_conclude_granted"],
            variables["option_essential_terms_defined"],
            variables["option_consideration_valid"],
        )
    )
    solver.add(
        main_contract_formed_by_option
        == And(option_offer_valid, variables["option_acceptance_within_term"])
    )
    solver.add(
        option_lapsed_unexercised
        == And(option_offer_valid, Not(variables["option_acceptance_within_term"]))
    )
    solver.add(
        option_contract_demand_enforceable
        == And(
            variables["option_contract_concluded"],
            variables["option_contract_demand_within_term"],
        )
    )
    solver.add(
        option_contract_terminated_by_expiry
        == And(
            variables["option_contract_concluded"],
            Not(variables["option_contract_demand_within_term"]),
        )
    )
    solver.add(
        option_payment_non_refundable
        == And(option_contract_terminated_by_expiry, variables["option_contract_payment_made"])
    )
    solver.add(
        option_right_transferable
        == And(variables["option_right_assigned"], Not(variables["assignment_prohibited"]))
    )
    solver.add(
        requires_human_option_assessment
        == Or(
            option_lapsed_unexercised,
            option_contract_terminated_by_expiry,
            And(variables["option_right_assigned"], variables["assignment_prohibited"]),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return OptionEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            option_offer_valid=False,
            main_contract_formed_by_option=False,
            option_lapsed_unexercised=False,
            option_contract_demand_enforceable=False,
            option_contract_terminated_by_expiry=False,
            option_payment_non_refundable=False,
            option_right_transferable=False,
            requires_human_option_assessment=True,
            reasons_ru=["Набор фактов об опционных конструкциях противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Опцион на заключение договора действителен (статья 429.2 ГК РФ)."
            if truth(option_offer_valid)
            else "Опцион на заключение договора не признаётся действительным."
        ),
    ]
    if truth(main_contract_formed_by_option):
        reasons_ru.append(
            "Акцепт безотзывной оферты в установленный срок влечёт заключение основного "
            "договора (пункты 1 и 2 статьи 429.2 ГК РФ)."
        )
    if truth(option_lapsed_unexercised):
        reasons_ru.append(
            "Право на заключение договора по опциону прекращается, если акцепт не "
            "совершён в установленный срок (пункт 2 статьи 429.2 ГК РФ)."
        )
    if truth(option_contract_demand_enforceable):
        reasons_ru.append(
            "По опционному договору сторона вправе требовать совершения предусмотренных "
            "действий в установленный срок (статья 429.3 ГК РФ)."
        )
    if truth(option_contract_terminated_by_expiry):
        reasons_ru.append(
            "Опционный договор прекращается, если управомоченная сторона не заявит "
            "требование в установленный срок (пункт 2 статьи 429.3 ГК РФ)."
        )
    if truth(option_payment_non_refundable):
        reasons_ru.append(
            "Платёж по опционному договору по общему правилу не возвращается при "
            "прекращении договора (пункт 3 статьи 429.3 ГК РФ)."
        )
    return OptionEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        option_offer_valid=truth(option_offer_valid),
        main_contract_formed_by_option=truth(main_contract_formed_by_option),
        option_lapsed_unexercised=truth(option_lapsed_unexercised),
        option_contract_demand_enforceable=truth(option_contract_demand_enforceable),
        option_contract_terminated_by_expiry=truth(option_contract_terminated_by_expiry),
        option_payment_non_refundable=truth(option_payment_non_refundable),
        option_right_transferable=truth(option_right_transferable),
        requires_human_option_assessment=truth(requires_human_option_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила об опционе на заключение "
            "договора и опционном договоре и не заменяет судебную оценку.",
            "Определённость условий, возмездность и соблюдение сроков оцениваются "
            "экспертом и судом.",
        ],
    )
