from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


REPRESENTATION_EVIDENCE_SCHEMA_VERSION = "contracts.representation-evidence.v0"
REPRESENTATION_MAPPING_VERSION = "contracts-reviewed-representation-to-facts-v0"
REPRESENTATION_MODEL_VERSION = "contracts-representation-articles-182-189-v0"


class RepresentationEvidencePredicate(str, Enum):
    # Представительство и основания полномочия (статья 182 ГК РФ).
    REPRESENTATION_RELATION_ESTABLISHED = "representation_relation_established"
    AUTHORITY_BASIS_INVALID = "authority_basis_invalid"
    PROHIBITED_SELF_DEALING = "prohibited_self_dealing"
    # Коммерческое представительство (статья 184 ГК РФ).
    COMMERCIAL_REPRESENTATION_RULES_BREACHED = "commercial_representation_rules_breached"
    # Доверенность: форма, удостоверение и срок (статьи 185, 185.1 и 186 ГК РФ).
    POWER_OF_ATTORNEY_FORM_BREACHED = "power_of_attorney_form_breached"
    POWER_OF_ATTORNEY_TERM_BREACHED = "power_of_attorney_term_breached"
    # Передоверие (статья 187 ГК РФ).
    SUBSTITUTION_RULES_BREACHED = "substitution_rules_breached"
    # Прекращение доверенности и его последствия (статьи 188 и 189 ГК РФ).
    TERMINATION_OR_NOTICE_BREACHED = "termination_or_notice_breached"
    # Совершение сделки неуполномоченным лицом (статья 183 ГК РФ).
    UNAUTHORIZED_ACT_WITHOUT_RATIFICATION = "unauthorized_act_without_ratification"
    RATIFICATION_EFFECT_DISREGARDED = "ratification_effect_disregarded"


REQUIRED_REPRESENTATION_PREDICATES = frozenset(RepresentationEvidencePredicate)


class RepresentationEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: RepresentationEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedRepresentationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = REPRESENTATION_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[RepresentationEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedRepresentationEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Representation evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Representation evidence contains duplicate legal source refs.")
        return self


class RepresentationFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    representation_relation_established: bool
    authority_basis_invalid: bool
    prohibited_self_dealing: bool
    commercial_representation_rules_breached: bool
    power_of_attorney_form_breached: bool
    power_of_attorney_term_breached: bool
    substitution_rules_breached: bool
    termination_or_notice_breached: bool
    unauthorized_act_without_ratification: bool
    ratification_effect_disregarded: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "RepresentationFactSet":
        if self.ratification_effect_disregarded and not self.unauthorized_act_without_ratification:
            raise ValueError(
                "Неучёт последующего одобрения сделки представляемым относится только к случаю, "
                "когда совершение сделки неуполномоченным лицом установлено."
            )
        if self.authority_basis_invalid and not self.representation_relation_established:
            raise ValueError(
                "Порок основания полномочия относится только к установленным отношениям "
                "представительства."
            )
        return self


class RepresentationFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class RepresentationEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: RepresentationFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[RepresentationFactProvenance] = Field(default_factory=list)


class RepresentationConstraintSet(BaseModel):
    id: str
    model_version: str = REPRESENTATION_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class RepresentationEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    representation_qualified: bool
    authority_basis_duty_breached: bool
    self_dealing_duty_breached: bool
    commercial_representation_duty_breached: bool
    power_of_attorney_form_duty_breached: bool
    power_of_attorney_term_duty_breached: bool
    substitution_duty_breached: bool
    termination_notice_duty_breached: bool
    # Ключевой вывод для слоя общих положений: сделка совершена без полномочий и
    # не одобрена представляемым, поэтому его не связывает (статья 183 ГК РФ).
    unauthorized_representation_detected: bool
    ratification_effect_breached: bool
    requires_human_representation_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_representation_evidence(
    evidence: ReviewedRepresentationEvidence,
) -> RepresentationEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Representation evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Representation evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_REPRESENTATION_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed representation evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_REPRESENTATION_PREDICATES
    }
    return RepresentationEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=REPRESENTATION_MAPPING_VERSION,
        facts=RepresentationFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            RepresentationFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_REPRESENTATION_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_representation_constraint_set(
    mapping: RepresentationEvidenceMappingResult,
) -> RepresentationConstraintSet:
    return RepresentationConstraintSet(
        id=f"representation-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "representation_qualified == representation_relation_established",
            "authority_basis_duty_breached == representation_qualified AND authority_basis_invalid",
            "self_dealing_duty_breached == representation_qualified AND prohibited_self_dealing",
            "commercial_representation_duty_breached == representation_qualified AND commercial_representation_rules_breached",
            "power_of_attorney_form_duty_breached == representation_qualified AND power_of_attorney_form_breached",
            "power_of_attorney_term_duty_breached == representation_qualified AND power_of_attorney_term_breached",
            "substitution_duty_breached == representation_qualified AND substitution_rules_breached",
            "termination_notice_duty_breached == representation_qualified AND termination_or_notice_breached",
            "unauthorized_representation_detected == representation_qualified AND unauthorized_act_without_ratification",
            "ratification_effect_breached == representation_qualified AND unauthorized_act_without_ratification AND ratification_effect_disregarded",
            "requires_human_representation_assessment == authority_basis_duty_breached OR self_dealing_duty_breached OR commercial_representation_duty_breached OR power_of_attorney_form_duty_breached OR power_of_attorney_term_duty_breached OR substitution_duty_breached OR termination_notice_duty_breached OR unauthorized_representation_detected",
        ],
    )


def evaluate_representation_constraints(
    constraint_set: RepresentationConstraintSet,
    facts: RepresentationFactSet,
) -> RepresentationEvaluation:
    variables = {field_name: Bool(field_name) for field_name in RepresentationFactSet.model_fields}
    representation_qualified = Bool("representation_qualified")
    authority_basis_duty_breached = Bool("authority_basis_duty_breached")
    self_dealing_duty_breached = Bool("self_dealing_duty_breached")
    commercial_representation_duty_breached = Bool("commercial_representation_duty_breached")
    power_of_attorney_form_duty_breached = Bool("power_of_attorney_form_duty_breached")
    power_of_attorney_term_duty_breached = Bool("power_of_attorney_term_duty_breached")
    substitution_duty_breached = Bool("substitution_duty_breached")
    termination_notice_duty_breached = Bool("termination_notice_duty_breached")
    unauthorized_representation_detected = Bool("unauthorized_representation_detected")
    ratification_effect_breached = Bool("ratification_effect_breached")
    requires_human_representation_assessment = Bool("requires_human_representation_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(representation_qualified == variables["representation_relation_established"])
    solver.add(
        authority_basis_duty_breached
        == And(representation_qualified, variables["authority_basis_invalid"])
    )
    solver.add(
        self_dealing_duty_breached
        == And(representation_qualified, variables["prohibited_self_dealing"])
    )
    solver.add(
        commercial_representation_duty_breached
        == And(representation_qualified, variables["commercial_representation_rules_breached"])
    )
    solver.add(
        power_of_attorney_form_duty_breached
        == And(representation_qualified, variables["power_of_attorney_form_breached"])
    )
    solver.add(
        power_of_attorney_term_duty_breached
        == And(representation_qualified, variables["power_of_attorney_term_breached"])
    )
    solver.add(
        substitution_duty_breached
        == And(representation_qualified, variables["substitution_rules_breached"])
    )
    solver.add(
        termination_notice_duty_breached
        == And(representation_qualified, variables["termination_or_notice_breached"])
    )
    solver.add(
        unauthorized_representation_detected
        == And(representation_qualified, variables["unauthorized_act_without_ratification"])
    )
    solver.add(
        ratification_effect_breached
        == And(
            representation_qualified,
            variables["unauthorized_act_without_ratification"],
            variables["ratification_effect_disregarded"],
        )
    )
    solver.add(
        requires_human_representation_assessment
        == Or(
            authority_basis_duty_breached,
            self_dealing_duty_breached,
            commercial_representation_duty_breached,
            power_of_attorney_form_duty_breached,
            power_of_attorney_term_duty_breached,
            substitution_duty_breached,
            termination_notice_duty_breached,
            unauthorized_representation_detected,
        )
    )
    satisfiable = solver.check() == sat
    if not satisfiable:
        return RepresentationEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            representation_qualified=False,
            authority_basis_duty_breached=False,
            self_dealing_duty_breached=False,
            commercial_representation_duty_breached=False,
            power_of_attorney_form_duty_breached=False,
            power_of_attorney_term_duty_breached=False,
            substitution_duty_breached=False,
            termination_notice_duty_breached=False,
            unauthorized_representation_detected=False,
            ratification_effect_breached=False,
            requires_human_representation_assessment=True,
            reasons_ru=["Набор фактов о представительстве и доверенности противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Установлены отношения представительства: сделка, совершённая одним лицом "
            "(представителем) от имени другого лица (представляемого) в силу полномочия, "
            "основанного на доверенности, указании закона либо акте уполномоченного органа, "
            "непосредственно создаёт, изменяет и прекращает гражданские права и обязанности "
            "представляемого (статья 182 ГК РФ)."
            if truth(representation_qualified)
            else "Отношения представительства не установлены."
        ),
    ]
    if truth(authority_basis_duty_breached):
        reasons_ru.append(
            "Полномочие представителя должно основываться на доверенности, указании закона либо "
            "акте уполномоченного государственного органа или органа местного самоуправления "
            "либо явствовать из обстановки, в которой действует представитель "
            "(статья 182 ГК РФ)."
        )
    if truth(self_dealing_duty_breached):
        reasons_ru.append(
            "Представитель не может совершать сделки от имени представляемого в отношении себя "
            "лично, а также в отношении другого лица, представителем которого он одновременно "
            "является, за исключением случаев коммерческого представительства; такая сделка "
            "может быть признана судом недействительной по иску представляемого "
            "(статья 182 ГК РФ)."
        )
    if truth(commercial_representation_duty_breached):
        reasons_ru.append(
            "Коммерческим представителем является лицо, постоянно и самостоятельно "
            "представительствующее от имени предпринимателей при заключении ими договоров; "
            "одновременное представительство разных сторон допускается с их согласия, а "
            "коммерческий представитель обязан исполнять поручения с заботливостью обычного "
            "предпринимателя (статья 184 ГК РФ)."
        )
    if truth(power_of_attorney_form_duty_breached):
        reasons_ru.append(
            "Доверенностью признаётся письменное уполномочие, выдаваемое одним лицом другому "
            "для представительства перед третьими лицами; доверенность на совершение сделок, "
            "требующих нотариальной формы, на подачу заявлений о государственной регистрации "
            "прав и на распоряжение зарегистрированными правами должна быть нотариально "
            "удостоверена, если иное не установлено законом (статьи 185 и 185.1 ГК РФ)."
        )
    if truth(power_of_attorney_term_duty_breached):
        reasons_ru.append(
            "Если в доверенности не указан срок её действия, она сохраняет силу в течение года "
            "со дня её совершения; доверенность, в которой не указана дата её совершения, "
            "ничтожна (статья 186 ГК РФ)."
        )
    if truth(substitution_duty_breached):
        reasons_ru.append(
            "Лицо, которому выдана доверенность, должно лично совершать действия, на которые оно "
            "уполномочено, и может передоверить их совершение другому лицу, если уполномочено на "
            "это доверенностью либо вынуждено силою обстоятельств для охраны интересов "
            "выдавшего доверенность; передавший полномочия обязан известить об этом выдавшего "
            "доверенность (статья 187 ГК РФ)."
        )
    if truth(termination_notice_duty_breached):
        reasons_ru.append(
            "Действие доверенности прекращается по основаниям, установленным законом, в том "
            "числе вследствие её отмены или отказа от неё; лицо, выдавшее доверенность, обязано "
            "известить о её отмене представителя и известных ему третьих лиц, а права и "
            "обязанности, возникшие до того, как представитель узнал или должен был узнать о "
            "прекращении доверенности, сохраняют силу для представляемого "
            "(статьи 188 и 189 ГК РФ)."
        )
    if truth(unauthorized_representation_detected):
        reasons_ru.append(
            "При отсутствии полномочий действовать от имени другого лица или при их превышении "
            "сделка считается заключённой от имени и в интересах совершившего её лица, если "
            "только другое лицо впоследствии не одобрит данную сделку; до одобрения "
            "представляемый такой сделкой не связан (статья 183 ГК РФ)."
        )
    if truth(ratification_effect_breached):
        reasons_ru.append(
            "Последующее одобрение сделки представляемым создаёт, изменяет и прекращает для него "
            "гражданские права и обязанности по данной сделке с момента её совершения "
            "(статья 183 ГК РФ)."
        )
    return RepresentationEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        representation_qualified=truth(representation_qualified),
        authority_basis_duty_breached=truth(authority_basis_duty_breached),
        self_dealing_duty_breached=truth(self_dealing_duty_breached),
        commercial_representation_duty_breached=truth(commercial_representation_duty_breached),
        power_of_attorney_form_duty_breached=truth(power_of_attorney_form_duty_breached),
        power_of_attorney_term_duty_breached=truth(power_of_attorney_term_duty_breached),
        substitution_duty_breached=truth(substitution_duty_breached),
        termination_notice_duty_breached=truth(termination_notice_duty_breached),
        unauthorized_representation_detected=truth(unauthorized_representation_detected),
        ratification_effect_breached=truth(ratification_effect_breached),
        requires_human_representation_assessment=truth(requires_human_representation_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о представительстве и доверенности и не "
            "заменяет судебную оценку.",
            "Объём полномочий представителя, явствование полномочия из обстановки и факт "
            "последующего одобрения сделки оцениваются экспертом и судом "
            "(статьи 182, 183 и 189 ГК РФ).",
        ],
    )
