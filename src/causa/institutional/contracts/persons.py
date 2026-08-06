"""Формальная модель правоспособности и дееспособности по статьям 17–53 ГК РФ.

Модель разделяет правоспособность гражданина и её содержание, объём
дееспособности по возрасту, признание гражданина недееспособным, ограничение
дееспособности и согласие попечителя, ничтожность сделок, направленных на
ограничение правоспособности или дееспособности, правоспособность юридического
лица и лицензируемые виды деятельности, государственную регистрацию
юридического лица и действия его органов.

Ключевой вывод для слоя общих положений — `party_lacks_capacity`: сторона
признана судом недееспособной. По статье 171 ГК РФ сделка, совершённая таким
гражданином, **ничтожна**, поэтому слой снимает действие договора, а не помечает
сделку оспоримой: в отличие от отсутствия согласия по статье 173.1, здесь
недействительность наступает независимо от признания её судом (пункт 1
статьи 166 ГК РФ).
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


PERSONS_EVIDENCE_SCHEMA_VERSION = "contracts.persons-evidence.v0"
PERSONS_MAPPING_VERSION = "contracts-reviewed-persons-to-facts-v0"
PERSONS_MODEL_VERSION = "contracts-persons-articles-17-53-v0"


class PersonsEvidencePredicate(str, Enum):
    # Правоспособность и дееспособность гражданина (статьи 17–21, 26, 28).
    PARTY_CAPACITY_ASSERTED = "party_capacity_asserted"
    LEGAL_CAPACITY_RULES_BREACHED = "legal_capacity_rules_breached"
    ACTIVE_CAPACITY_AGE_RULES_BREACHED = "active_capacity_age_rules_breached"
    # Признание недееспособным и ограничение дееспособности (статьи 29–30).
    INCAPACITY_DECLARED_BY_COURT = "incapacity_declared_by_court"
    LIMITED_CAPACITY_RULES_BREACHED = "limited_capacity_rules_breached"
    GUARDIANSHIP_CONSENT_MISSING = "guardianship_consent_missing"
    # Недопустимость ограничения правоспособности и дееспособности (статья 22).
    CAPACITY_RESTRICTION_BY_AGREEMENT = "capacity_restriction_by_agreement"
    # Юридические лица: правоспособность, регистрация и органы (статьи 49–53).
    ENTITY_CAPACITY_SCOPE_BREACHED = "entity_capacity_scope_breached"
    ENTITY_REGISTRATION_OR_STATUS_BREACHED = "entity_registration_or_status_breached"
    ENTITY_BODY_AUTHORITY_BREACHED = "entity_body_authority_breached"


REQUIRED_PERSONS_PREDICATES = frozenset(PersonsEvidencePredicate)


class PersonsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: PersonsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedPersonsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = PERSONS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[PersonsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedPersonsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Persons evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Persons evidence contains duplicate legal source refs.")
        return self


class PersonsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    party_capacity_asserted: bool
    legal_capacity_rules_breached: bool
    active_capacity_age_rules_breached: bool
    incapacity_declared_by_court: bool
    limited_capacity_rules_breached: bool
    guardianship_consent_missing: bool
    capacity_restriction_by_agreement: bool
    entity_capacity_scope_breached: bool
    entity_registration_or_status_breached: bool
    entity_body_authority_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "PersonsFactSet":
        if self.guardianship_consent_missing and not self.limited_capacity_rules_breached:
            raise ValueError(
                "Отсутствие согласия попечителя относится только к случаю, когда применяются "
                "правила об ограничении дееспособности."
            )
        if self.incapacity_declared_by_court and not self.party_capacity_asserted:
            raise ValueError(
                "Признание гражданина недееспособным относится только к заявленному вопросу о "
                "правоспособности или дееспособности стороны."
            )
        return self


class PersonsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class PersonsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: PersonsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[PersonsFactProvenance] = Field(default_factory=list)


class PersonsConstraintSet(BaseModel):
    id: str
    model_version: str = PERSONS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class PersonsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    persons_qualified: bool
    legal_capacity_duty_breached: bool
    active_capacity_age_duty_breached: bool
    # Ключевой вывод для слоя общих положений: сторона признана судом
    # недееспособной, поэтому совершённая ею сделка ничтожна (статья 171 ГК РФ).
    party_lacks_capacity: bool
    limited_capacity_duty_breached: bool
    guardianship_consent_duty_breached: bool
    capacity_restriction_duty_breached: bool
    entity_capacity_scope_duty_breached: bool
    entity_registration_duty_breached: bool
    entity_body_authority_duty_breached: bool
    requires_human_persons_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_persons_evidence(
    evidence: ReviewedPersonsEvidence,
) -> PersonsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Persons evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Persons evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_PERSONS_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed persons evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_PERSONS_PREDICATES
    }
    return PersonsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=PERSONS_MAPPING_VERSION,
        facts=PersonsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            PersonsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_PERSONS_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_persons_constraint_set(mapping: PersonsEvidenceMappingResult) -> PersonsConstraintSet:
    return PersonsConstraintSet(
        id=f"persons-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "persons_qualified == party_capacity_asserted",
            "legal_capacity_duty_breached == persons_qualified AND legal_capacity_rules_breached",
            "active_capacity_age_duty_breached == persons_qualified AND active_capacity_age_rules_breached",
            "party_lacks_capacity == persons_qualified AND incapacity_declared_by_court",
            "limited_capacity_duty_breached == persons_qualified AND limited_capacity_rules_breached",
            "guardianship_consent_duty_breached == persons_qualified AND limited_capacity_rules_breached AND guardianship_consent_missing",
            "capacity_restriction_duty_breached == persons_qualified AND capacity_restriction_by_agreement",
            "entity_capacity_scope_duty_breached == persons_qualified AND entity_capacity_scope_breached",
            "entity_registration_duty_breached == persons_qualified AND entity_registration_or_status_breached",
            "entity_body_authority_duty_breached == persons_qualified AND entity_body_authority_breached",
            "requires_human_persons_assessment == legal_capacity_duty_breached OR active_capacity_age_duty_breached OR party_lacks_capacity OR limited_capacity_duty_breached OR capacity_restriction_duty_breached OR entity_capacity_scope_duty_breached OR entity_registration_duty_breached OR entity_body_authority_duty_breached",
        ],
    )


def evaluate_persons_constraints(
    constraint_set: PersonsConstraintSet,
    facts: PersonsFactSet,
) -> PersonsEvaluation:
    variables = {field_name: Bool(field_name) for field_name in PersonsFactSet.model_fields}
    persons_qualified = Bool("persons_qualified")
    legal_capacity_duty_breached = Bool("legal_capacity_duty_breached")
    active_capacity_age_duty_breached = Bool("active_capacity_age_duty_breached")
    party_lacks_capacity = Bool("party_lacks_capacity")
    limited_capacity_duty_breached = Bool("limited_capacity_duty_breached")
    guardianship_consent_duty_breached = Bool("guardianship_consent_duty_breached")
    capacity_restriction_duty_breached = Bool("capacity_restriction_duty_breached")
    entity_capacity_scope_duty_breached = Bool("entity_capacity_scope_duty_breached")
    entity_registration_duty_breached = Bool("entity_registration_duty_breached")
    entity_body_authority_duty_breached = Bool("entity_body_authority_duty_breached")
    requires_human_persons_assessment = Bool("requires_human_persons_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(persons_qualified == variables["party_capacity_asserted"])
    solver.add(
        legal_capacity_duty_breached
        == And(persons_qualified, variables["legal_capacity_rules_breached"])
    )
    solver.add(
        active_capacity_age_duty_breached
        == And(persons_qualified, variables["active_capacity_age_rules_breached"])
    )
    solver.add(
        party_lacks_capacity == And(persons_qualified, variables["incapacity_declared_by_court"])
    )
    solver.add(
        limited_capacity_duty_breached
        == And(persons_qualified, variables["limited_capacity_rules_breached"])
    )
    solver.add(
        guardianship_consent_duty_breached
        == And(
            persons_qualified,
            variables["limited_capacity_rules_breached"],
            variables["guardianship_consent_missing"],
        )
    )
    solver.add(
        capacity_restriction_duty_breached
        == And(persons_qualified, variables["capacity_restriction_by_agreement"])
    )
    solver.add(
        entity_capacity_scope_duty_breached
        == And(persons_qualified, variables["entity_capacity_scope_breached"])
    )
    solver.add(
        entity_registration_duty_breached
        == And(persons_qualified, variables["entity_registration_or_status_breached"])
    )
    solver.add(
        entity_body_authority_duty_breached
        == And(persons_qualified, variables["entity_body_authority_breached"])
    )
    solver.add(
        requires_human_persons_assessment
        == Or(
            legal_capacity_duty_breached,
            active_capacity_age_duty_breached,
            party_lacks_capacity,
            limited_capacity_duty_breached,
            capacity_restriction_duty_breached,
            entity_capacity_scope_duty_breached,
            entity_registration_duty_breached,
            entity_body_authority_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return PersonsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            persons_qualified=False,
            legal_capacity_duty_breached=False,
            active_capacity_age_duty_breached=False,
            party_lacks_capacity=False,
            limited_capacity_duty_breached=False,
            guardianship_consent_duty_breached=False,
            capacity_restriction_duty_breached=False,
            entity_capacity_scope_duty_breached=False,
            entity_registration_duty_breached=False,
            entity_body_authority_duty_breached=False,
            requires_human_persons_assessment=True,
            reasons_ru=["Набор фактов о правоспособности и дееспособности противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Заявлен вопрос о правоспособности или дееспособности стороны: способность иметь "
            "гражданские права и нести обязанности признаётся в равной мере за всеми "
            "гражданами (статья 17 ГК РФ)."
            if truth(persons_qualified)
            else "Вопрос о правоспособности или дееспособности стороны не заявлен."
        ),
    ]
    if truth(legal_capacity_duty_breached):
        reasons_ru.append(
            "Нарушены правила о правоспособности гражданина: она возникает в момент рождения и "
            "прекращается смертью, а её содержание включает возможность иметь имущество, "
            "совершать сделки и иметь иные имущественные и личные неимущественные права "
            "(статьи 17 и 18 ГК РФ)."
        )
    if truth(active_capacity_age_duty_breached):
        reasons_ru.append(
            "Нарушены правила об объёме дееспособности по возрасту: способность своими "
            "действиями приобретать и осуществлять гражданские права возникает в полном "
            "объёме с наступлением совершеннолетия, а сделки несовершеннолетних совершаются "
            "по особым правилам (статьи 21, 26 и 28 ГК РФ)."
        )
    if truth(party_lacks_capacity):
        reasons_ru.append(
            "Сторона признана судом недееспособной вследствие психического расстройства, при "
            "котором она не может понимать значения своих действий или руководить ими; от её "
            "имени сделки совершает опекун (статья 29 ГК РФ), а сделка, совершённая ею самой, "
            "ничтожна (статья 171 ГК РФ)."
        )
    if truth(limited_capacity_duty_breached):
        reasons_ru.append(
            "Нарушены правила об ограничении дееспособности: гражданин, ограниченный судом в "
            "дееспособности, самостоятельно совершает лишь мелкие бытовые сделки "
            "(статья 30 ГК РФ)."
        )
    if truth(guardianship_consent_duty_breached):
        reasons_ru.append(
            "Сделка совершена ограниченно дееспособным гражданином без согласия попечителя, "
            "тогда как иные сделки он вправе совершать только с такого согласия "
            "(статья 30 ГК РФ)."
        )
    if truth(capacity_restriction_duty_breached):
        reasons_ru.append(
            "Совершена сделка, направленная на ограничение правоспособности или "
            "дееспособности: такие сделки ничтожны, за исключением случаев, когда они "
            "допускаются законом (статья 22 ГК РФ)."
        )
    if truth(entity_capacity_scope_duty_breached):
        reasons_ru.append(
            "Нарушены правила о правоспособности юридического лица: оно может иметь "
            "гражданские права, соответствующие целям деятельности, а отдельными видами "
            "деятельности вправе заниматься только на основании лицензии или членства в "
            "саморегулируемой организации (статья 49 ГК РФ)."
        )
    if truth(entity_registration_duty_breached):
        reasons_ru.append(
            "Нарушены правила о государственной регистрации и статусе юридического лица: оно "
            "подлежит государственной регистрации и считается созданным со дня внесения "
            "соответствующей записи в единый государственный реестр (статья 51 ГК РФ)."
        )
    if truth(entity_body_authority_duty_breached):
        reasons_ru.append(
            "Нарушены правила об органах юридического лица: оно приобретает гражданские права "
            "и принимает на себя гражданские обязанности через свои органы, действующие от "
            "его имени и обязанные действовать добросовестно и разумно (статья 53 ГК РФ)."
        )
    return PersonsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        persons_qualified=truth(persons_qualified),
        legal_capacity_duty_breached=truth(legal_capacity_duty_breached),
        active_capacity_age_duty_breached=truth(active_capacity_age_duty_breached),
        party_lacks_capacity=truth(party_lacks_capacity),
        limited_capacity_duty_breached=truth(limited_capacity_duty_breached),
        guardianship_consent_duty_breached=truth(guardianship_consent_duty_breached),
        capacity_restriction_duty_breached=truth(capacity_restriction_duty_breached),
        entity_capacity_scope_duty_breached=truth(entity_capacity_scope_duty_breached),
        entity_registration_duty_breached=truth(entity_registration_duty_breached),
        entity_body_authority_duty_breached=truth(entity_body_authority_duty_breached),
        requires_human_persons_assessment=truth(requires_human_persons_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о правоспособности и дееспособности и "
            "не заменяет судебную оценку.",
            "Признание гражданина недееспособным или ограниченно дееспособным, наличие "
            "лицензии и добросовестность действий органов юридического лица оцениваются "
            "экспертом и судом (статьи 29, 30, 49 и 53 ГК РФ).",
        ],
    )
