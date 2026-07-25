from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


THIRD_PARTY_EVIDENCE_SCHEMA_VERSION = "contracts.third-party-evidence.v0"
THIRD_PARTY_MAPPING_VERSION = "contracts-reviewed-third-party-to-facts-v0"
THIRD_PARTY_MODEL_VERSION = "contracts-third-party-article-430-v0"


class ThirdPartyEvidencePredicate(str, Enum):
    # Договор в пользу третьего лица и право требования (пункт 1 статьи 430 ГК РФ).
    THIRD_PARTY_BENEFICIARY_CONTRACT = "third_party_beneficiary_contract"
    THIRD_PARTY_IDENTIFIED_OR_DETERMINABLE = "third_party_identified_or_determinable"
    THIRD_PARTY_GRANTED_RIGHT_TO_DEMAND = "third_party_granted_right_to_demand"
    # Связанность сторон после выражения намерения (пункт 2 статьи 430 ГК РФ).
    THIRD_PARTY_INTENT_EXPRESSED = "third_party_intent_expressed"
    STATUTE_OR_CONTRACT_ALLOWS_CHANGE_WITHOUT_CONSENT = (
        "statute_or_contract_allows_change_without_consent"
    )
    PARTIES_SEEK_MODIFICATION_OR_TERMINATION = "parties_seek_modification_or_termination"
    THIRD_PARTY_CONSENTS_TO_CHANGE = "third_party_consents_to_change"
    # Отказ третьего лица и переход права к кредитору (пункт 4 статьи 430 ГК РФ).
    THIRD_PARTY_WAIVED_RIGHT = "third_party_waived_right"
    CREDITOR_RECLAIMS_RIGHT = "creditor_reclaims_right"


REQUIRED_THIRD_PARTY_PREDICATES = frozenset(ThirdPartyEvidencePredicate)


class ThirdPartyEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ThirdPartyEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedThirdPartyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = THIRD_PARTY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ThirdPartyEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedThirdPartyEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Third-party evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Third-party evidence contains duplicate legal source refs.")
        return self


class ThirdPartyFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    third_party_beneficiary_contract: bool
    third_party_identified_or_determinable: bool
    third_party_granted_right_to_demand: bool
    third_party_intent_expressed: bool
    statute_or_contract_allows_change_without_consent: bool
    parties_seek_modification_or_termination: bool
    third_party_consents_to_change: bool
    third_party_waived_right: bool
    creditor_reclaims_right: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ThirdPartyFactSet":
        if self.third_party_intent_expressed and not self.third_party_beneficiary_contract:
            raise ValueError(
                "Намерение воспользоваться правом невозможно без договора в пользу третьего лица."
            )
        if self.third_party_waived_right and not self.third_party_beneficiary_contract:
            raise ValueError(
                "Отказ третьего лица от права невозможен без договора в пользу третьего лица."
            )
        if self.third_party_intent_expressed and self.third_party_waived_right:
            raise ValueError(
                "Третье лицо не может одновременно выразить намерение воспользоваться "
                "правом и отказаться от него."
            )
        if self.creditor_reclaims_right and not self.third_party_waived_right:
            raise ValueError(
                "Кредитор может воспользоваться правом только после отказа третьего лица."
            )
        return self


class ThirdPartyFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ThirdPartyEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ThirdPartyFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ThirdPartyFactProvenance] = Field(default_factory=list)


class ThirdPartyConstraintSet(BaseModel):
    id: str
    model_version: str = THIRD_PARTY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ThirdPartyEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    beneficiary_contract_valid: bool
    third_party_may_demand_performance: bool
    change_requires_third_party_consent: bool
    change_permitted: bool
    creditor_may_use_right: bool
    requires_human_third_party_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_third_party_evidence(
    evidence: ReviewedThirdPartyEvidence,
) -> ThirdPartyEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Third-party evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Third-party evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_THIRD_PARTY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed third-party evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_THIRD_PARTY_PREDICATES
    }
    return ThirdPartyEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=THIRD_PARTY_MAPPING_VERSION,
        facts=ThirdPartyFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ThirdPartyFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_THIRD_PARTY_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_third_party_constraint_set(
    mapping: ThirdPartyEvidenceMappingResult,
) -> ThirdPartyConstraintSet:
    return ThirdPartyConstraintSet(
        id=f"third-party-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "beneficiary_contract_valid == third_party_beneficiary_contract AND third_party_identified_or_determinable",
            "third_party_may_demand_performance == beneficiary_contract_valid AND third_party_granted_right_to_demand AND NOT third_party_waived_right",
            "change_requires_third_party_consent == beneficiary_contract_valid AND third_party_intent_expressed AND NOT statute_or_contract_allows_change_without_consent",
            "change_permitted == parties_seek_modification_or_termination AND (NOT change_requires_third_party_consent OR third_party_consents_to_change)",
            "creditor_may_use_right == beneficiary_contract_valid AND third_party_waived_right AND creditor_reclaims_right",
            "requires_human_third_party_assessment == (parties_seek_modification_or_termination AND change_requires_third_party_consent AND NOT third_party_consents_to_change) OR creditor_may_use_right",
        ],
    )


def evaluate_third_party_constraints(
    constraint_set: ThirdPartyConstraintSet,
    facts: ThirdPartyFactSet,
) -> ThirdPartyEvaluation:
    variables = {field_name: Bool(field_name) for field_name in ThirdPartyFactSet.model_fields}
    beneficiary_contract_valid = Bool("beneficiary_contract_valid")
    third_party_may_demand_performance = Bool("third_party_may_demand_performance")
    change_requires_third_party_consent = Bool("change_requires_third_party_consent")
    change_permitted = Bool("change_permitted")
    creditor_may_use_right = Bool("creditor_may_use_right")
    requires_human_third_party_assessment = Bool("requires_human_third_party_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        beneficiary_contract_valid
        == And(
            variables["third_party_beneficiary_contract"],
            variables["third_party_identified_or_determinable"],
        )
    )
    solver.add(
        third_party_may_demand_performance
        == And(
            beneficiary_contract_valid,
            variables["third_party_granted_right_to_demand"],
            Not(variables["third_party_waived_right"]),
        )
    )
    solver.add(
        change_requires_third_party_consent
        == And(
            beneficiary_contract_valid,
            variables["third_party_intent_expressed"],
            Not(variables["statute_or_contract_allows_change_without_consent"]),
        )
    )
    solver.add(
        change_permitted
        == And(
            variables["parties_seek_modification_or_termination"],
            Or(
                Not(change_requires_third_party_consent),
                variables["third_party_consents_to_change"],
            ),
        )
    )
    solver.add(
        creditor_may_use_right
        == And(
            beneficiary_contract_valid,
            variables["third_party_waived_right"],
            variables["creditor_reclaims_right"],
        )
    )
    solver.add(
        requires_human_third_party_assessment
        == Or(
            And(
                variables["parties_seek_modification_or_termination"],
                change_requires_third_party_consent,
                Not(variables["third_party_consents_to_change"]),
            ),
            creditor_may_use_right,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ThirdPartyEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            beneficiary_contract_valid=False,
            third_party_may_demand_performance=False,
            change_requires_third_party_consent=False,
            change_permitted=False,
            creditor_may_use_right=False,
            requires_human_third_party_assessment=True,
            reasons_ru=["Набор фактов о договоре в пользу третьего лица противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор в пользу третьего лица действителен (статья 430 ГК РФ)."
            if truth(beneficiary_contract_valid)
            else "Договор в пользу третьего лица не признается действительным."
        ),
    ]
    if truth(third_party_may_demand_performance):
        reasons_ru.append(
            "Третье лицо вправе требовать от должника исполнения обязательства "
            "(пункт 1 статьи 430 ГК РФ)."
        )
    if truth(change_requires_third_party_consent):
        reasons_ru.append(
            "После выражения третьим лицом намерения воспользоваться правом изменение "
            "и расторжение договора без его согласия не допускаются "
            "(пункт 2 статьи 430 ГК РФ)."
        )
    if truth(creditor_may_use_right):
        reasons_ru.append(
            "При отказе третьего лица от права кредитор может воспользоваться им, если "
            "это не противоречит закону, иным правовым актам и договору "
            "(пункт 4 статьи 430 ГК РФ)."
        )
    return ThirdPartyEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        beneficiary_contract_valid=truth(beneficiary_contract_valid),
        third_party_may_demand_performance=truth(third_party_may_demand_performance),
        change_requires_third_party_consent=truth(change_requires_third_party_consent),
        change_permitted=truth(change_permitted),
        creditor_may_use_right=truth(creditor_may_use_right),
        requires_human_third_party_assessment=truth(requires_human_third_party_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о договоре в пользу третьего "
            "лица и не заменяет судебную оценку.",
            "Возражения должника против требования третьего лица и пределы права "
            "оцениваются экспертом и судом.",
        ],
    )
