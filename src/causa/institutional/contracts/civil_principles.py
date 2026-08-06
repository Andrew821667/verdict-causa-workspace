from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


CIVIL_PRINCIPLES_EVIDENCE_SCHEMA_VERSION = "contracts.civil-principles-evidence.v0"
CIVIL_PRINCIPLES_MAPPING_VERSION = "contracts-reviewed-civil-principles-to-facts-v0"
CIVIL_PRINCIPLES_MODEL_VERSION = "contracts-civil-principles-articles-1-16-1-v0"


class CivilPrinciplesEvidencePredicate(str, Enum):
    # Основные начала гражданского законодательства (статья 1 ГК РФ).
    CIVIL_RIGHTS_EXERCISE_ASSERTED = "civil_rights_exercise_asserted"
    GOOD_FAITH_PRINCIPLE_BREACHED = "good_faith_principle_breached"
    EQUALITY_OR_FREEDOM_PRINCIPLE_BREACHED = "equality_or_freedom_principle_breached"
    # Основания возникновения гражданских прав и обязанностей (статья 8 ГК РФ).
    RIGHTS_ARISING_GROUNDS_BREACHED = "rights_arising_grounds_breached"
    # Пределы осуществления гражданских прав (статья 10 ГК РФ).
    ABUSE_OF_RIGHT_ESTABLISHED = "abuse_of_right_established"
    PROTECTION_REFUSAL_NOT_APPLIED = "protection_refusal_not_applied"
    # Способы защиты гражданских прав и самозащита (статьи 12 и 14 ГК РФ).
    PROTECTION_METHODS_BREACHED = "protection_methods_breached"
    SELF_HELP_LIMITS_BREACHED = "self_help_limits_breached"
    # Возмещение убытков (статья 15 ГК РФ).
    DAMAGES_COMPENSATION_RULES_BREACHED = "damages_compensation_rules_breached"
    # Ответственность публично-правовых образований (статьи 16 и 16.1 ГК РФ).
    PUBLIC_AUTHORITY_LIABILITY_BREACHED = "public_authority_liability_breached"


REQUIRED_CIVIL_PRINCIPLES_PREDICATES = frozenset(CivilPrinciplesEvidencePredicate)


class CivilPrinciplesEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: CivilPrinciplesEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedCivilPrinciplesEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CIVIL_PRINCIPLES_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[CivilPrinciplesEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedCivilPrinciplesEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Civil-principles evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Civil-principles evidence contains duplicate legal source refs.")
        return self


class CivilPrinciplesFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    civil_rights_exercise_asserted: bool
    good_faith_principle_breached: bool
    equality_or_freedom_principle_breached: bool
    rights_arising_grounds_breached: bool
    abuse_of_right_established: bool
    protection_refusal_not_applied: bool
    protection_methods_breached: bool
    self_help_limits_breached: bool
    damages_compensation_rules_breached: bool
    public_authority_liability_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "CivilPrinciplesFactSet":
        if self.protection_refusal_not_applied and not self.abuse_of_right_established:
            raise ValueError(
                "Неприменение отказа в защите права относится только к случаю, когда "
                "злоупотребление правом установлено."
            )
        if self.good_faith_principle_breached and not self.civil_rights_exercise_asserted:
            raise ValueError(
                "Нарушение принципа добросовестности относится только к заявленному "
                "осуществлению или защите гражданского права."
            )
        return self


class CivilPrinciplesFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class CivilPrinciplesEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: CivilPrinciplesFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[CivilPrinciplesFactProvenance] = Field(default_factory=list)


class CivilPrinciplesConstraintSet(BaseModel):
    id: str
    model_version: str = CIVIL_PRINCIPLES_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class CivilPrinciplesEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    civil_principles_qualified: bool
    good_faith_duty_breached: bool
    equality_and_freedom_duty_breached: bool
    rights_arising_duty_breached: bool
    # Ключевой вывод для слоя общих положений: установлено злоупотребление правом,
    # что влечёт отказ в защите права (статья 10 ГК РФ).
    abuse_of_right_detected: bool
    protection_refusal_breached: bool
    protection_methods_duty_breached: bool
    self_help_duty_breached: bool
    damages_compensation_duty_breached: bool
    public_authority_liability_duty_breached: bool
    requires_human_civil_principles_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_civil_principles_evidence(
    evidence: ReviewedCivilPrinciplesEvidence,
) -> CivilPrinciplesEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Civil-principles evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Civil-principles evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_CIVIL_PRINCIPLES_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed civil-principles evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_CIVIL_PRINCIPLES_PREDICATES
    }
    return CivilPrinciplesEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CIVIL_PRINCIPLES_MAPPING_VERSION,
        facts=CivilPrinciplesFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            CivilPrinciplesFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_CIVIL_PRINCIPLES_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_civil_principles_constraint_set(
    mapping: CivilPrinciplesEvidenceMappingResult,
) -> CivilPrinciplesConstraintSet:
    return CivilPrinciplesConstraintSet(
        id=f"civil-principles-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "civil_principles_qualified == civil_rights_exercise_asserted",
            "good_faith_duty_breached == civil_principles_qualified AND good_faith_principle_breached",
            "equality_and_freedom_duty_breached == civil_principles_qualified AND equality_or_freedom_principle_breached",
            "rights_arising_duty_breached == civil_principles_qualified AND rights_arising_grounds_breached",
            "abuse_of_right_detected == civil_principles_qualified AND abuse_of_right_established",
            "protection_refusal_breached == civil_principles_qualified AND abuse_of_right_established AND protection_refusal_not_applied",
            "protection_methods_duty_breached == civil_principles_qualified AND protection_methods_breached",
            "self_help_duty_breached == civil_principles_qualified AND self_help_limits_breached",
            "damages_compensation_duty_breached == civil_principles_qualified AND damages_compensation_rules_breached",
            "public_authority_liability_duty_breached == civil_principles_qualified AND public_authority_liability_breached",
            "requires_human_civil_principles_assessment == good_faith_duty_breached OR equality_and_freedom_duty_breached OR rights_arising_duty_breached OR abuse_of_right_detected OR protection_methods_duty_breached OR self_help_duty_breached OR damages_compensation_duty_breached OR public_authority_liability_duty_breached",
        ],
    )


def evaluate_civil_principles_constraints(
    constraint_set: CivilPrinciplesConstraintSet,
    facts: CivilPrinciplesFactSet,
) -> CivilPrinciplesEvaluation:
    variables = {field_name: Bool(field_name) for field_name in CivilPrinciplesFactSet.model_fields}
    civil_principles_qualified = Bool("civil_principles_qualified")
    good_faith_duty_breached = Bool("good_faith_duty_breached")
    equality_and_freedom_duty_breached = Bool("equality_and_freedom_duty_breached")
    rights_arising_duty_breached = Bool("rights_arising_duty_breached")
    abuse_of_right_detected = Bool("abuse_of_right_detected")
    protection_refusal_breached = Bool("protection_refusal_breached")
    protection_methods_duty_breached = Bool("protection_methods_duty_breached")
    self_help_duty_breached = Bool("self_help_duty_breached")
    damages_compensation_duty_breached = Bool("damages_compensation_duty_breached")
    public_authority_liability_duty_breached = Bool("public_authority_liability_duty_breached")
    requires_human_civil_principles_assessment = Bool("requires_human_civil_principles_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(civil_principles_qualified == variables["civil_rights_exercise_asserted"])
    solver.add(
        good_faith_duty_breached
        == And(civil_principles_qualified, variables["good_faith_principle_breached"])
    )
    solver.add(
        equality_and_freedom_duty_breached
        == And(civil_principles_qualified, variables["equality_or_freedom_principle_breached"])
    )
    solver.add(
        rights_arising_duty_breached
        == And(civil_principles_qualified, variables["rights_arising_grounds_breached"])
    )
    solver.add(
        abuse_of_right_detected
        == And(civil_principles_qualified, variables["abuse_of_right_established"])
    )
    solver.add(
        protection_refusal_breached
        == And(
            civil_principles_qualified,
            variables["abuse_of_right_established"],
            variables["protection_refusal_not_applied"],
        )
    )
    solver.add(
        protection_methods_duty_breached
        == And(civil_principles_qualified, variables["protection_methods_breached"])
    )
    solver.add(
        self_help_duty_breached
        == And(civil_principles_qualified, variables["self_help_limits_breached"])
    )
    solver.add(
        damages_compensation_duty_breached
        == And(civil_principles_qualified, variables["damages_compensation_rules_breached"])
    )
    solver.add(
        public_authority_liability_duty_breached
        == And(civil_principles_qualified, variables["public_authority_liability_breached"])
    )
    solver.add(
        requires_human_civil_principles_assessment
        == Or(
            good_faith_duty_breached,
            equality_and_freedom_duty_breached,
            rights_arising_duty_breached,
            abuse_of_right_detected,
            protection_methods_duty_breached,
            self_help_duty_breached,
            damages_compensation_duty_breached,
            public_authority_liability_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return CivilPrinciplesEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            civil_principles_qualified=False,
            good_faith_duty_breached=False,
            equality_and_freedom_duty_breached=False,
            rights_arising_duty_breached=False,
            abuse_of_right_detected=False,
            protection_refusal_breached=False,
            protection_methods_duty_breached=False,
            self_help_duty_breached=False,
            damages_compensation_duty_breached=False,
            public_authority_liability_duty_breached=False,
            requires_human_civil_principles_assessment=True,
            reasons_ru=["Набор фактов об основных началах гражданского права противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Заявлено осуществление или защита гражданского права: гражданское "
            "законодательство основывается на признании равенства участников регулируемых им "
            "отношений, неприкосновенности собственности, свободы договора и недопустимости "
            "произвольного вмешательства кого-либо в частные дела (статья 1 ГК РФ)."
            if truth(civil_principles_qualified)
            else "Осуществление или защита гражданского права не заявлены."
        ),
    ]
    if truth(good_faith_duty_breached):
        reasons_ru.append(
            "При установлении, осуществлении и защите гражданских прав и при исполнении "
            "гражданских обязанностей участники гражданских правоотношений должны действовать "
            "добросовестно; никто не вправе извлекать преимущество из своего незаконного или "
            "недобросовестного поведения (статья 1 ГК РФ)."
        )
    if truth(equality_and_freedom_duty_breached):
        reasons_ru.append(
            "Граждане и юридические лица приобретают и осуществляют свои гражданские права "
            "своей волей и в своём интересе и свободны в установлении своих прав и обязанностей "
            "на основе договора; гражданские права могут быть ограничены только на основании "
            "федерального закона и только в той мере, в какой это необходимо для целей, "
            "названных в законе (статья 1 ГК РФ)."
        )
    if truth(rights_arising_duty_breached):
        reasons_ru.append(
            "Гражданские права и обязанности возникают из оснований, предусмотренных законом и "
            "иными правовыми актами, а также из действий граждан и юридических лиц, которые "
            "хотя и не предусмотрены законом, но в силу общих начал и смысла гражданского "
            "законодательства порождают гражданские права и обязанности (статья 8 ГК РФ)."
        )
    if truth(abuse_of_right_detected):
        reasons_ru.append(
            "Не допускаются осуществление гражданских прав исключительно с намерением причинить "
            "вред другому лицу, действия в обход закона с противоправной целью, а также иное "
            "заведомо недобросовестное осуществление гражданских прав (злоупотребление правом) "
            "(статья 10 ГК РФ)."
        )
    if truth(protection_refusal_breached):
        reasons_ru.append(
            "В случае несоблюдения требований о пределах осуществления гражданских прав суд с "
            "учётом характера и последствий допущенного злоупотребления отказывает лицу в "
            "защите принадлежащего ему права полностью или частично, а также применяет иные "
            "меры, предусмотренные законом (статья 10 ГК РФ)."
        )
    if truth(protection_methods_duty_breached):
        reasons_ru.append(
            "Защита гражданских прав осуществляется способами, предусмотренными законом, в том "
            "числе путём признания права, восстановления положения, существовавшего до "
            "нарушения, присуждения к исполнению обязанности в натуре, возмещения убытков и "
            "иными способами, предусмотренными законом (статья 12 ГК РФ)."
        )
    if truth(self_help_duty_breached):
        reasons_ru.append(
            "Допускается самозащита гражданских прав; способы самозащиты должны быть соразмерны "
            "нарушению и не выходить за пределы действий, необходимых для его пресечения "
            "(статья 14 ГК РФ)."
        )
    if truth(damages_compensation_duty_breached):
        reasons_ru.append(
            "Лицо, право которого нарушено, может требовать полного возмещения причинённых ему "
            "убытков, включая реальный ущерб и упущенную выгоду, если законом или договором не "
            "предусмотрено возмещение убытков в меньшем размере (статья 15 ГК РФ)."
        )
    if truth(public_authority_liability_duty_breached):
        reasons_ru.append(
            "Убытки, причинённые гражданину или юридическому лицу в результате незаконных "
            "действий или бездействия государственных органов, органов местного самоуправления "
            "или их должностных лиц, подлежат возмещению соответствующим публично-правовым "
            "образованием; ущерб, причинённый правомерными действиями таких органов, "
            "компенсируется в случаях, предусмотренных законом (статьи 16 и 16.1 ГК РФ)."
        )
    return CivilPrinciplesEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        civil_principles_qualified=truth(civil_principles_qualified),
        good_faith_duty_breached=truth(good_faith_duty_breached),
        equality_and_freedom_duty_breached=truth(equality_and_freedom_duty_breached),
        rights_arising_duty_breached=truth(rights_arising_duty_breached),
        abuse_of_right_detected=truth(abuse_of_right_detected),
        protection_refusal_breached=truth(protection_refusal_breached),
        protection_methods_duty_breached=truth(protection_methods_duty_breached),
        self_help_duty_breached=truth(self_help_duty_breached),
        damages_compensation_duty_breached=truth(damages_compensation_duty_breached),
        public_authority_liability_duty_breached=truth(public_authority_liability_duty_breached),
        requires_human_civil_principles_assessment=truth(
            requires_human_civil_principles_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные основные начала гражданского законодательства и "
            "правила об осуществлении и защите гражданских прав и не заменяет судебную оценку.",
            "Недобросовестность поведения, характер и последствия злоупотребления правом и "
            "размер убытков оцениваются экспертом и судом (статьи 1, 10 и 15 ГК РФ).",
        ],
    )
