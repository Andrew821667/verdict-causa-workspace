from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


MORAL_HARM_EVIDENCE_SCHEMA_VERSION = "contracts.moral-harm-evidence.v0"
MORAL_HARM_MAPPING_VERSION = "contracts-reviewed-moral-harm-to-facts-v0"
MORAL_HARM_MODEL_VERSION = "contracts-moral-harm-articles-1099-1101-v0"


class MoralHarmEvidencePredicate(str, Enum):
    # Общие положения о компенсации морального вреда (статья 1099 ГК РФ).
    MORAL_HARM_CLAIM_ESTABLISHED = "moral_harm_claim_established"
    NON_MATERIAL_BENEFITS_SCOPE_BREACHED = "non_material_benefits_scope_breached"
    PROPERTY_RIGHTS_COMPENSATION_LIMITS_BREACHED = "property_rights_compensation_limits_breached"
    INDEPENDENT_FROM_PROPERTY_DAMAGE_BREACHED = "independent_from_property_damage_breached"
    # Основания компенсации независимо от вины причинителя (статья 1100 ГК РФ).
    NO_FAULT_GROUNDS_DISREGARDED = "no_fault_grounds_disregarded"
    HIGH_RISK_SOURCE_GROUND_BREACHED = "high_risk_source_ground_breached"
    UNLAWFUL_PROSECUTION_GROUND_BREACHED = "unlawful_prosecution_ground_breached"
    DEFAMATION_GROUND_BREACHED = "defamation_ground_breached"
    # Способ и размер компенсации морального вреда (статья 1101 ГК РФ).
    COMPENSATION_FORM_OR_AMOUNT_BREACHED = "compensation_form_or_amount_breached"
    VICTIM_INDIVIDUAL_FEATURES_DISREGARDED = "victim_individual_features_disregarded"


REQUIRED_MORAL_HARM_PREDICATES = frozenset(MoralHarmEvidencePredicate)


class MoralHarmEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: MoralHarmEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedMoralHarmEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = MORAL_HARM_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[MoralHarmEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedMoralHarmEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Moral-harm evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Moral-harm evidence contains duplicate legal source refs.")
        return self


class MoralHarmFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    moral_harm_claim_established: bool
    non_material_benefits_scope_breached: bool
    property_rights_compensation_limits_breached: bool
    independent_from_property_damage_breached: bool
    no_fault_grounds_disregarded: bool
    high_risk_source_ground_breached: bool
    unlawful_prosecution_ground_breached: bool
    defamation_ground_breached: bool
    compensation_form_or_amount_breached: bool
    victim_individual_features_disregarded: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "MoralHarmFactSet":
        if (
            self.victim_individual_features_disregarded
            and not self.compensation_form_or_amount_breached
        ):
            raise ValueError(
                "Неучёт индивидуальных особенностей потерпевшего относится только к случаю, "
                "когда нарушение способа или размера компенсации морального вреда установлено."
            )
        if self.non_material_benefits_scope_breached and not self.moral_harm_claim_established:
            raise ValueError(
                "Нарушение оснований компенсации при посягательстве на нематериальные блага "
                "относится только к случаю, когда причинение морального вреда установлено."
            )
        return self


class MoralHarmFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class MoralHarmEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: MoralHarmFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[MoralHarmFactProvenance] = Field(default_factory=list)


class MoralHarmConstraintSet(BaseModel):
    id: str
    model_version: str = MORAL_HARM_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class MoralHarmEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    moral_harm_qualified: bool
    non_material_benefits_duty_breached: bool
    property_rights_limits_duty_breached: bool
    independence_duty_breached: bool
    no_fault_grounds_duty_breached: bool
    high_risk_source_ground_duty_breached: bool
    unlawful_prosecution_ground_duty_breached: bool
    defamation_ground_duty_breached: bool
    compensation_form_duty_breached: bool
    victim_features_breached: bool
    requires_human_moral_harm_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_moral_harm_evidence(
    evidence: ReviewedMoralHarmEvidence,
) -> MoralHarmEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Moral-harm evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Moral-harm evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_MORAL_HARM_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed moral-harm evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_MORAL_HARM_PREDICATES
    }
    return MoralHarmEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=MORAL_HARM_MAPPING_VERSION,
        facts=MoralHarmFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            MoralHarmFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_MORAL_HARM_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_moral_harm_constraint_set(
    mapping: MoralHarmEvidenceMappingResult,
) -> MoralHarmConstraintSet:
    return MoralHarmConstraintSet(
        id=f"moral-harm-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "moral_harm_qualified == moral_harm_claim_established",
            "non_material_benefits_duty_breached == moral_harm_qualified AND non_material_benefits_scope_breached",
            "property_rights_limits_duty_breached == moral_harm_qualified AND property_rights_compensation_limits_breached",
            "independence_duty_breached == moral_harm_qualified AND independent_from_property_damage_breached",
            "no_fault_grounds_duty_breached == moral_harm_qualified AND no_fault_grounds_disregarded",
            "high_risk_source_ground_duty_breached == moral_harm_qualified AND high_risk_source_ground_breached",
            "unlawful_prosecution_ground_duty_breached == moral_harm_qualified AND unlawful_prosecution_ground_breached",
            "defamation_ground_duty_breached == moral_harm_qualified AND defamation_ground_breached",
            "compensation_form_duty_breached == moral_harm_qualified AND compensation_form_or_amount_breached",
            "victim_features_breached == moral_harm_qualified AND compensation_form_or_amount_breached AND victim_individual_features_disregarded",
            "requires_human_moral_harm_assessment == non_material_benefits_duty_breached OR property_rights_limits_duty_breached OR independence_duty_breached OR no_fault_grounds_duty_breached OR high_risk_source_ground_duty_breached OR unlawful_prosecution_ground_duty_breached OR defamation_ground_duty_breached OR compensation_form_duty_breached",
        ],
    )


def evaluate_moral_harm_constraints(
    constraint_set: MoralHarmConstraintSet,
    facts: MoralHarmFactSet,
) -> MoralHarmEvaluation:
    variables = {field_name: Bool(field_name) for field_name in MoralHarmFactSet.model_fields}
    moral_harm_qualified = Bool("moral_harm_qualified")
    non_material_benefits_duty_breached = Bool("non_material_benefits_duty_breached")
    property_rights_limits_duty_breached = Bool("property_rights_limits_duty_breached")
    independence_duty_breached = Bool("independence_duty_breached")
    no_fault_grounds_duty_breached = Bool("no_fault_grounds_duty_breached")
    high_risk_source_ground_duty_breached = Bool("high_risk_source_ground_duty_breached")
    unlawful_prosecution_ground_duty_breached = Bool("unlawful_prosecution_ground_duty_breached")
    defamation_ground_duty_breached = Bool("defamation_ground_duty_breached")
    compensation_form_duty_breached = Bool("compensation_form_duty_breached")
    victim_features_breached = Bool("victim_features_breached")
    requires_human_moral_harm_assessment = Bool("requires_human_moral_harm_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(moral_harm_qualified == variables["moral_harm_claim_established"])
    solver.add(
        non_material_benefits_duty_breached
        == And(moral_harm_qualified, variables["non_material_benefits_scope_breached"])
    )
    solver.add(
        property_rights_limits_duty_breached
        == And(moral_harm_qualified, variables["property_rights_compensation_limits_breached"])
    )
    solver.add(
        independence_duty_breached
        == And(moral_harm_qualified, variables["independent_from_property_damage_breached"])
    )
    solver.add(
        no_fault_grounds_duty_breached
        == And(moral_harm_qualified, variables["no_fault_grounds_disregarded"])
    )
    solver.add(
        high_risk_source_ground_duty_breached
        == And(moral_harm_qualified, variables["high_risk_source_ground_breached"])
    )
    solver.add(
        unlawful_prosecution_ground_duty_breached
        == And(moral_harm_qualified, variables["unlawful_prosecution_ground_breached"])
    )
    solver.add(
        defamation_ground_duty_breached
        == And(moral_harm_qualified, variables["defamation_ground_breached"])
    )
    solver.add(
        compensation_form_duty_breached
        == And(moral_harm_qualified, variables["compensation_form_or_amount_breached"])
    )
    solver.add(
        victim_features_breached
        == And(
            moral_harm_qualified,
            variables["compensation_form_or_amount_breached"],
            variables["victim_individual_features_disregarded"],
        )
    )
    solver.add(
        requires_human_moral_harm_assessment
        == Or(
            non_material_benefits_duty_breached,
            property_rights_limits_duty_breached,
            independence_duty_breached,
            no_fault_grounds_duty_breached,
            high_risk_source_ground_duty_breached,
            unlawful_prosecution_ground_duty_breached,
            defamation_ground_duty_breached,
            compensation_form_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return MoralHarmEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            moral_harm_qualified=False,
            non_material_benefits_duty_breached=False,
            property_rights_limits_duty_breached=False,
            independence_duty_breached=False,
            no_fault_grounds_duty_breached=False,
            high_risk_source_ground_duty_breached=False,
            unlawful_prosecution_ground_duty_breached=False,
            defamation_ground_duty_breached=False,
            compensation_form_duty_breached=False,
            victim_features_breached=False,
            requires_human_moral_harm_assessment=True,
            reasons_ru=["Набор фактов о компенсации морального вреда противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Установлено причинение морального вреда: основания и размер компенсации "
            "гражданину морального вреда определяются правилами главы 59 и статьи 151 ГК РФ "
            "(статья 1099 ГК РФ)."
            if truth(moral_harm_qualified)
            else "Причинение морального вреда не установлено."
        ),
    ]
    if truth(non_material_benefits_duty_breached):
        reasons_ru.append(
            "Основания и размер компенсации гражданину морального вреда, причинённого "
            "действиями, нарушающими его личные неимущественные права либо посягающими на "
            "принадлежащие ему другие нематериальные блага, определяются правилами главы 59 и "
            "статьи 151 ГК РФ (статья 1099 ГК РФ)."
        )
    if truth(property_rights_limits_duty_breached):
        reasons_ru.append(
            "Моральный вред, причинённый действиями, нарушающими имущественные права "
            "гражданина, подлежит компенсации в случаях, предусмотренных законом "
            "(статья 1099 ГК РФ)."
        )
    if truth(independence_duty_breached):
        reasons_ru.append(
            "Компенсация морального вреда осуществляется независимо от подлежащего возмещению "
            "имущественного вреда (статья 1099 ГК РФ)."
        )
    if truth(no_fault_grounds_duty_breached):
        reasons_ru.append(
            "Компенсация морального вреда осуществляется независимо от вины причинителя в "
            "случаях, предусмотренных законом, перечень которых установлен статьёй 1100 ГК РФ "
            "(статья 1100 ГК РФ)."
        )
    if truth(high_risk_source_ground_duty_breached):
        reasons_ru.append(
            "Моральный вред компенсируется независимо от вины причинителя, когда вред причинён "
            "жизни или здоровью гражданина источником повышенной опасности "
            "(статья 1100 ГК РФ)."
        )
    if truth(unlawful_prosecution_ground_duty_breached):
        reasons_ru.append(
            "Моральный вред компенсируется независимо от вины причинителя, когда вред причинён "
            "гражданину в результате его незаконного осуждения, незаконного привлечения к "
            "уголовной ответственности, незаконного применения в качестве меры пресечения "
            "заключения под стражу или подписки о невыезде, а также незаконного наложения "
            "административного наказания (статья 1100 ГК РФ)."
        )
    if truth(defamation_ground_duty_breached):
        reasons_ru.append(
            "Моральный вред компенсируется независимо от вины причинителя, когда вред причинён "
            "распространением сведений, порочащих честь, достоинство и деловую репутацию "
            "(статья 1100 ГК РФ)."
        )
    if truth(compensation_form_duty_breached):
        reasons_ru.append(
            "Компенсация морального вреда осуществляется в денежной форме, а её размер "
            "определяется судом в зависимости от характера причинённых потерпевшему физических "
            "и нравственных страданий, степени вины причинителя в случаях, когда вина является "
            "основанием возмещения, и с учётом требований разумности и справедливости "
            "(статья 1101 ГК РФ)."
        )
    if truth(victim_features_breached):
        reasons_ru.append(
            "При определении размера компенсации характер физических и нравственных страданий "
            "оценивается судом с учётом фактических обстоятельств причинения морального вреда и "
            "индивидуальных особенностей потерпевшего (статья 1101 ГК РФ)."
        )
    return MoralHarmEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        moral_harm_qualified=truth(moral_harm_qualified),
        non_material_benefits_duty_breached=truth(non_material_benefits_duty_breached),
        property_rights_limits_duty_breached=truth(property_rights_limits_duty_breached),
        independence_duty_breached=truth(independence_duty_breached),
        no_fault_grounds_duty_breached=truth(no_fault_grounds_duty_breached),
        high_risk_source_ground_duty_breached=truth(high_risk_source_ground_duty_breached),
        unlawful_prosecution_ground_duty_breached=truth(unlawful_prosecution_ground_duty_breached),
        defamation_ground_duty_breached=truth(defamation_ground_duty_breached),
        compensation_form_duty_breached=truth(compensation_form_duty_breached),
        victim_features_breached=truth(victim_features_breached),
        requires_human_moral_harm_assessment=truth(requires_human_moral_harm_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о компенсации морального вреда и не "
            "заменяет судебную оценку.",
            "Характер и степень физических и нравственных страданий, индивидуальные "
            "особенности потерпевшего и требования разумности и справедливости оцениваются "
            "экспертом и судом (статьи 1099 и 1101 ГК РФ).",
        ],
    )
