from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


INVALIDITY_EVIDENCE_SCHEMA_VERSION = "contracts.invalidity-evidence.v0"
INVALIDITY_MAPPING_VERSION = "contracts-reviewed-invalidity-to-facts-v0"
INVALIDITY_MODEL_VERSION = "contracts-transaction-invalidity-articles-166-181-v0"


class InvalidityEvidencePredicate(str, Enum):
    TRANSACTION_CONCLUDED = "transaction_concluded"
    INVALIDITY_CLAIM_MADE = "invalidity_claim_made"
    CLAIMANT_IS_TRANSACTION_PARTY = "claimant_is_transaction_party"
    CLAIMANT_LEGALLY_AUTHORIZED = "claimant_legally_authorized"
    CLAIMANT_RIGHTS_OR_INTERESTS_AFFECTED = "claimant_rights_or_interests_affected"
    COURT_DECISION_ENTERED_INTO_FORCE = "court_decision_entered_into_force"
    NULLITY_CONSEQUENCES_REQUESTED = "nullity_consequences_requested"
    NULLITY_LEGAL_INTEREST_PROVEN = "nullity_legal_interest_proven"
    GOOD_FAITH_RELIANCE_CREATED = "good_faith_reliance_created"
    PARTY_CONFIRMED_VOIDABLE_TRANSACTION = "party_confirmed_voidable_transaction"
    GROUND_KNOWN_AT_CONFIRMATION = "ground_known_at_confirmation"
    VIOLATES_LAW = "violates_law"
    PUBLIC_INTERESTS_OR_THIRD_RIGHTS_AFFECTED = "public_interests_or_third_rights_affected"
    LAW_EXPRESSLY_MAKES_VOID = "law_expressly_makes_void"
    IMMORAL_PURPOSE_PROVEN = "immoral_purpose_proven"
    BOTH_PARTIES_INTENTIONAL_IMMORAL_PURPOSE = "both_parties_intentional_immoral_purpose"
    SHAM_INTENT_PROVEN = "sham_intent_proven"
    FEIGNED_INTENT_PROVEN = "feigned_intent_proven"
    DISGUISED_TRANSACTION_IDENTIFIED = "disguised_transaction_identified"
    INCAPACITATED_PERSON_TRANSACTION = "incapacitated_person_transaction"
    MINOR_UNDER_14_TRANSACTION = "minor_under_14_transaction"
    BENEFIT_TO_INCAPACITATED_OR_MINOR_PROVEN = "benefit_to_incapacitated_or_minor_proven"
    REQUIRED_CONSENT_ABSENT = "required_consent_absent"
    COUNTERPARTY_KNEW_CONSENT_ABSENT = "counterparty_knew_consent_absent"
    AUTHORITY_RESTRICTION_VIOLATED = "authority_restriction_violated"
    COUNTERPARTY_KNEW_AUTHORITY_RESTRICTION = "counterparty_knew_authority_restriction"
    ENTITY_BEYOND_STATUTORY_PURPOSE = "entity_beyond_statutory_purpose"
    COUNTERPARTY_KNEW_BEYOND_PURPOSE = "counterparty_knew_beyond_purpose"
    OBVIOUS_ENTITY_DAMAGE_PROVEN = "obvious_entity_damage_proven"
    COUNTERPARTY_KNEW_OBVIOUS_DAMAGE = "counterparty_knew_obvious_damage"
    MATERIAL_MISTAKE_PROVEN = "material_mistake_proven"
    MISTAKE_RISK_ASSUMED = "mistake_risk_assumed"
    DECEPTION_PROVEN = "deception_proven"
    VIOLENCE_OR_THREAT_PROVEN = "violence_or_threat_proven"
    ADVERSE_CIRCUMSTANCES_PROVEN = "adverse_circumstances_proven"
    EXTREMELY_UNFAVORABLE_TERMS_PROVEN = "extremely_unfavorable_terms_proven"
    COUNTERPARTY_EXPLOITED_CIRCUMSTANCES = "counterparty_exploited_circumstances"
    UNABLE_TO_UNDERSTAND_ACTIONS_PROVEN = "unable_to_understand_actions_proven"
    LIMITED_CAPACITY_WITHOUT_CONSENT = "limited_capacity_without_consent"
    MINOR_14_18_WITHOUT_CONSENT = "minor_14_18_without_consent"
    EXECUTION_STARTED = "execution_started"
    VOID_LIMITATION_PERIOD_EXPIRED = "void_limitation_period_expired"
    VOIDABLE_LIMITATION_PERIOD_EXPIRED = "voidable_limitation_period_expired"
    INVALID_PART_SEPARABLE = "invalid_part_separable"
    REMAINDER_PRESERVES_TRANSACTION_PURPOSE = "remainder_preserves_transaction_purpose"
    PARTY_A_PERFORMED = "party_a_performed"
    PARTY_B_PERFORMED = "party_b_performed"
    RETURN_IN_KIND_POSSIBLE = "return_in_kind_possible"
    VALUE_OF_PERFORMANCE_PROVEN = "value_of_performance_proven"
    ADDITIONAL_DAMAGES_CLAIMED = "additional_damages_claimed"
    ADDITIONAL_DAMAGES_CAUSALLY_LINKED = "additional_damages_causally_linked"


REQUIRED_INVALIDITY_PREDICATES = frozenset(InvalidityEvidencePredicate)


class InvalidityEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: InvalidityEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedInvalidityEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = INVALIDITY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[InvalidityEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedInvalidityEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Invalidity evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Invalidity evidence contains duplicate legal source refs.")
        return self


class InvalidityFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transaction_concluded: bool
    invalidity_claim_made: bool
    claimant_is_transaction_party: bool
    claimant_legally_authorized: bool
    claimant_rights_or_interests_affected: bool
    court_decision_entered_into_force: bool
    nullity_consequences_requested: bool
    nullity_legal_interest_proven: bool
    good_faith_reliance_created: bool
    party_confirmed_voidable_transaction: bool
    ground_known_at_confirmation: bool
    violates_law: bool
    public_interests_or_third_rights_affected: bool
    law_expressly_makes_void: bool
    immoral_purpose_proven: bool
    both_parties_intentional_immoral_purpose: bool
    sham_intent_proven: bool
    feigned_intent_proven: bool
    disguised_transaction_identified: bool
    incapacitated_person_transaction: bool
    minor_under_14_transaction: bool
    benefit_to_incapacitated_or_minor_proven: bool
    required_consent_absent: bool
    counterparty_knew_consent_absent: bool
    authority_restriction_violated: bool
    counterparty_knew_authority_restriction: bool
    entity_beyond_statutory_purpose: bool
    counterparty_knew_beyond_purpose: bool
    obvious_entity_damage_proven: bool
    counterparty_knew_obvious_damage: bool
    material_mistake_proven: bool
    mistake_risk_assumed: bool
    deception_proven: bool
    violence_or_threat_proven: bool
    adverse_circumstances_proven: bool
    extremely_unfavorable_terms_proven: bool
    counterparty_exploited_circumstances: bool
    unable_to_understand_actions_proven: bool
    limited_capacity_without_consent: bool
    minor_14_18_without_consent: bool
    execution_started: bool
    void_limitation_period_expired: bool
    voidable_limitation_period_expired: bool
    invalid_part_separable: bool
    remainder_preserves_transaction_purpose: bool
    party_a_performed: bool
    party_b_performed: bool
    return_in_kind_possible: bool
    value_of_performance_proven: bool
    additional_damages_claimed: bool
    additional_damages_causally_linked: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "InvalidityFactSet":
        if self.court_decision_entered_into_force and not self.invalidity_claim_made:
            raise ValueError("An effective invalidity judgment requires a claim.")
        if self.ground_known_at_confirmation and not self.party_confirmed_voidable_transaction:
            raise ValueError("Known ground requires confirmation of the voidable transaction.")
        if self.counterparty_knew_consent_absent and not self.required_consent_absent:
            raise ValueError("Knowledge of missing consent requires absent consent.")
        if self.counterparty_knew_authority_restriction and not self.authority_restriction_violated:
            raise ValueError("Knowledge of authority restriction requires its violation.")
        if self.counterparty_knew_beyond_purpose and not self.entity_beyond_statutory_purpose:
            raise ValueError("Knowledge beyond purpose requires a purpose violation.")
        if self.counterparty_knew_obvious_damage and not self.obvious_entity_damage_proven:
            raise ValueError("Knowledge of obvious damage requires proven damage.")
        if self.disguised_transaction_identified and not self.feigned_intent_proven:
            raise ValueError("A disguised transaction requires feigned intent.")
        if self.both_parties_intentional_immoral_purpose and not self.immoral_purpose_proven:
            raise ValueError("Intentional immoral purpose requires the purpose to be proven.")
        if self.mistake_risk_assumed and not self.material_mistake_proven:
            raise ValueError("Assumed mistake risk requires a proven material mistake.")
        if self.extremely_unfavorable_terms_proven and not self.adverse_circumstances_proven:
            raise ValueError("Extremely unfavorable terms require adverse circumstances.")
        if self.counterparty_exploited_circumstances and not self.adverse_circumstances_proven:
            raise ValueError("Exploitation requires adverse circumstances.")
        if self.void_limitation_period_expired and not self.execution_started:
            raise ValueError("Void limitation period requires execution to have started.")
        if self.remainder_preserves_transaction_purpose and not self.invalid_part_separable:
            raise ValueError("Preserved remainder requires a separable invalid part.")
        if self.value_of_performance_proven and self.return_in_kind_possible:
            raise ValueError("Monetary valuation is not required when return in kind is possible.")
        if self.additional_damages_causally_linked and not self.additional_damages_claimed:
            raise ValueError("Causally linked damages require a damages claim.")
        return self


class InvalidityFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class InvalidityEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: InvalidityFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[InvalidityFactProvenance] = Field(default_factory=list)


class InvalidityConstraintSet(BaseModel):
    id: str
    model_version: str = INVALIDITY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class InvalidityEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    estoppel_bar: bool
    unlawful_void_ground: bool
    unlawful_voidable_ground: bool
    immoral_void_ground: bool
    sham_void_ground: bool
    feigned_void_ground: bool
    capacity_void_ground: bool
    consent_voidable_ground: bool
    authority_voidable_ground: bool
    entity_purpose_voidable_ground: bool
    mistake_voidable_ground: bool
    coercion_voidable_ground: bool
    capacity_voidable_ground: bool
    void_ground_detected: bool
    voidable_ground_detected: bool
    voidable_claimant_has_standing: bool
    nullity_consequence_claimant_has_standing: bool
    voidable_invalidity_prerequisites: bool
    voidable_invalidity_effective: bool
    nullity_consequences_prerequisites: bool
    contractual_effect_displaced: bool
    transaction_presumed_effective: bool
    disguised_transaction_rules_required: bool
    partial_invalidity_only: bool
    entire_transaction_affected: bool
    restitution_required: bool
    restitution_in_kind: bool
    monetary_restitution_issue: bool
    public_recovery_issue: bool
    additional_damages_issue: bool
    requires_human_invalidity_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_invalidity_evidence(
    evidence: ReviewedInvalidityEvidence,
) -> InvalidityEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Invalidity evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Invalidity evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_INVALIDITY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed invalidity evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_INVALIDITY_PREDICATES
    }
    return InvalidityEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=INVALIDITY_MAPPING_VERSION,
        facts=InvalidityFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            InvalidityFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_INVALIDITY_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_invalidity_constraint_set(
    mapping: InvalidityEvidenceMappingResult,
) -> InvalidityConstraintSet:
    return InvalidityConstraintSet(
        id=f"invalidity-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "estoppel_bar == good_faith_reliance_created OR (party_confirmed_voidable_transaction AND ground_known_at_confirmation)",
            "unlawful_void_ground == violates_law AND (public_interests_or_third_rights_affected OR law_expressly_makes_void)",
            "unlawful_voidable_ground == violates_law AND NOT unlawful_void_ground",
            "void_ground_detected == unlawful_void_ground OR immoral_void_ground OR sham_void_ground OR feigned_void_ground OR capacity_void_ground",
            "voidable_ground_detected == unlawful_voidable_ground OR consent_voidable_ground OR authority_voidable_ground OR entity_purpose_voidable_ground OR mistake_voidable_ground OR coercion_voidable_ground OR capacity_voidable_ground",
            "voidable_invalidity_prerequisites == transaction_concluded AND voidable_ground_detected AND voidable_claimant_has_standing AND NOT estoppel_bar AND NOT voidable_limitation_period_expired",
            "voidable_invalidity_effective == voidable_invalidity_prerequisites AND court_decision_entered_into_force",
            "nullity_consequences_prerequisites == transaction_concluded AND void_ground_detected AND nullity_consequence_claimant_has_standing AND NOT void_limitation_period_expired",
            "contractual_effect_displaced == transaction_concluded AND (void_ground_detected OR voidable_invalidity_effective)",
            "partial_invalidity_only == contractual_effect_displaced AND invalid_part_separable AND remainder_preserves_transaction_purpose",
            "restitution_required == contractual_effect_displaced AND (party_a_performed OR party_b_performed)",
            "additional_damages_issue == contractual_effect_displaced AND additional_damages_claimed AND additional_damages_causally_linked",
        ],
    )


def evaluate_invalidity_constraints(
    constraint_set: InvalidityConstraintSet,
    facts: InvalidityFactSet,
) -> InvalidityEvaluation:
    variables = {field_name: Bool(field_name) for field_name in InvalidityFactSet.model_fields}
    outputs = {
        field_name: Bool(field_name)
        for field_name in InvalidityEvaluation.model_fields
        if field_name not in {"constraint_set_id", "satisfiable", "reasons_ru", "warnings_ru"}
    }
    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    solver.add(
        outputs["estoppel_bar"]
        == Or(
            variables["good_faith_reliance_created"],
            And(
                variables["party_confirmed_voidable_transaction"],
                variables["ground_known_at_confirmation"],
            ),
        )
    )
    solver.add(
        outputs["unlawful_void_ground"]
        == And(
            variables["violates_law"],
            Or(
                variables["public_interests_or_third_rights_affected"],
                variables["law_expressly_makes_void"],
            ),
        )
    )
    solver.add(
        outputs["unlawful_voidable_ground"]
        == And(variables["violates_law"], Not(outputs["unlawful_void_ground"]))
    )
    solver.add(outputs["immoral_void_ground"] == variables["immoral_purpose_proven"])
    solver.add(outputs["sham_void_ground"] == variables["sham_intent_proven"])
    solver.add(outputs["feigned_void_ground"] == variables["feigned_intent_proven"])
    solver.add(
        outputs["capacity_void_ground"]
        == Or(
            variables["incapacitated_person_transaction"],
            variables["minor_under_14_transaction"],
        )
    )
    solver.add(
        outputs["consent_voidable_ground"]
        == And(
            variables["required_consent_absent"],
            variables["counterparty_knew_consent_absent"],
        )
    )
    solver.add(
        outputs["authority_voidable_ground"]
        == Or(
            And(
                variables["authority_restriction_violated"],
                variables["counterparty_knew_authority_restriction"],
            ),
            And(
                variables["obvious_entity_damage_proven"],
                variables["counterparty_knew_obvious_damage"],
            ),
        )
    )
    solver.add(
        outputs["entity_purpose_voidable_ground"]
        == And(
            variables["entity_beyond_statutory_purpose"],
            variables["counterparty_knew_beyond_purpose"],
        )
    )
    solver.add(
        outputs["mistake_voidable_ground"]
        == And(variables["material_mistake_proven"], Not(variables["mistake_risk_assumed"]))
    )
    solver.add(
        outputs["coercion_voidable_ground"]
        == Or(
            variables["deception_proven"],
            variables["violence_or_threat_proven"],
            And(
                variables["adverse_circumstances_proven"],
                variables["extremely_unfavorable_terms_proven"],
                variables["counterparty_exploited_circumstances"],
            ),
        )
    )
    solver.add(
        outputs["capacity_voidable_ground"]
        == Or(
            variables["unable_to_understand_actions_proven"],
            variables["limited_capacity_without_consent"],
            variables["minor_14_18_without_consent"],
        )
    )
    solver.add(
        outputs["void_ground_detected"]
        == Or(
            outputs["unlawful_void_ground"],
            outputs["immoral_void_ground"],
            outputs["sham_void_ground"],
            outputs["feigned_void_ground"],
            outputs["capacity_void_ground"],
        )
    )
    solver.add(
        outputs["voidable_ground_detected"]
        == Or(
            outputs["unlawful_voidable_ground"],
            outputs["consent_voidable_ground"],
            outputs["authority_voidable_ground"],
            outputs["entity_purpose_voidable_ground"],
            outputs["mistake_voidable_ground"],
            outputs["coercion_voidable_ground"],
            outputs["capacity_voidable_ground"],
        )
    )
    solver.add(
        outputs["voidable_claimant_has_standing"]
        == And(
            variables["invalidity_claim_made"],
            Or(
                variables["claimant_is_transaction_party"],
                variables["claimant_legally_authorized"],
            ),
            variables["claimant_rights_or_interests_affected"],
        )
    )
    solver.add(
        outputs["nullity_consequence_claimant_has_standing"]
        == And(
            variables["nullity_consequences_requested"],
            Or(
                variables["claimant_is_transaction_party"],
                variables["claimant_legally_authorized"],
                variables["nullity_legal_interest_proven"],
            ),
        )
    )
    solver.add(
        outputs["voidable_invalidity_prerequisites"]
        == And(
            variables["transaction_concluded"],
            outputs["voidable_ground_detected"],
            outputs["voidable_claimant_has_standing"],
            Not(outputs["estoppel_bar"]),
            Not(variables["voidable_limitation_period_expired"]),
        )
    )
    solver.add(
        outputs["voidable_invalidity_effective"]
        == And(
            outputs["voidable_invalidity_prerequisites"],
            variables["court_decision_entered_into_force"],
        )
    )
    solver.add(
        outputs["nullity_consequences_prerequisites"]
        == And(
            variables["transaction_concluded"],
            outputs["void_ground_detected"],
            outputs["nullity_consequence_claimant_has_standing"],
            Not(variables["void_limitation_period_expired"]),
        )
    )
    solver.add(
        outputs["contractual_effect_displaced"]
        == And(
            variables["transaction_concluded"],
            Or(outputs["void_ground_detected"], outputs["voidable_invalidity_effective"]),
        )
    )
    solver.add(
        outputs["transaction_presumed_effective"]
        == And(
            variables["transaction_concluded"],
            Not(outputs["contractual_effect_displaced"]),
        )
    )
    solver.add(
        outputs["disguised_transaction_rules_required"]
        == And(variables["feigned_intent_proven"], variables["disguised_transaction_identified"])
    )
    solver.add(
        outputs["partial_invalidity_only"]
        == And(
            outputs["contractual_effect_displaced"],
            variables["invalid_part_separable"],
            variables["remainder_preserves_transaction_purpose"],
        )
    )
    solver.add(
        outputs["entire_transaction_affected"]
        == And(outputs["contractual_effect_displaced"], Not(outputs["partial_invalidity_only"]))
    )
    solver.add(
        outputs["restitution_required"]
        == And(
            outputs["contractual_effect_displaced"],
            Or(variables["party_a_performed"], variables["party_b_performed"]),
        )
    )
    solver.add(
        outputs["restitution_in_kind"]
        == And(outputs["restitution_required"], variables["return_in_kind_possible"])
    )
    solver.add(
        outputs["monetary_restitution_issue"]
        == And(
            outputs["restitution_required"],
            Not(variables["return_in_kind_possible"]),
            variables["value_of_performance_proven"],
        )
    )
    solver.add(
        outputs["public_recovery_issue"]
        == And(
            outputs["immoral_void_ground"],
            variables["both_parties_intentional_immoral_purpose"],
        )
    )
    solver.add(
        outputs["additional_damages_issue"]
        == And(
            outputs["contractual_effect_displaced"],
            variables["additional_damages_claimed"],
            variables["additional_damages_causally_linked"],
        )
    )
    solver.add(
        outputs["requires_human_invalidity_assessment"]
        == Or(
            outputs["void_ground_detected"],
            outputs["voidable_ground_detected"],
            variables["invalidity_claim_made"],
            variables["nullity_consequences_requested"],
            outputs["estoppel_bar"],
            outputs["contractual_effect_displaced"],
            outputs["restitution_required"],
            variables["benefit_to_incapacitated_or_minor_proven"],
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return InvalidityEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            **{
                field_name: False
                for field_name in outputs
                if field_name != "requires_human_invalidity_assessment"
            },
            requires_human_invalidity_assessment=True,
            reasons_ru=["Набор фактов о действительности сделки противоречив."],
            warnings_ru=["Требуется повторная проверка исходных данных юристом."],
        )
    model = solver.model()
    values = {
        field_name: bool(model.eval(variable, model_completion=True))
        for field_name, variable in outputs.items()
    }
    reasons_ru = [
        (
            "Формальная модель выявила основание ничтожности сделки."
            if values["void_ground_detected"]
            else "Основание ничтожности сделки не выявлено."
        ),
        (
            "Формальная модель выявила основание оспоримости сделки."
            if values["voidable_ground_detected"]
            else "Основание оспоримости сделки не выявлено."
        ),
    ]
    if values["estoppel_bar"]:
        reasons_ru.append(
            "Выявлен запрет противоречивой или недобросовестной ссылки на недействительность."
        )
    if values["transaction_presumed_effective"]:
        reasons_ru.append("Договорные последствия сделки текущей моделью не устранены.")
    if values["contractual_effect_displaced"]:
        reasons_ru.append("Обычные договорные последствия сделки формально устранены.")
    return InvalidityEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        **values,
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Квалификация основания ничтожности или оспоримости требует правовой оценки.",
            "Модель не признает сделку недействительной и не определяет размер реституции автоматически.",
            "Специальные основания и последствия отдельных сделок проверяются отдельно.",
        ],
    )
