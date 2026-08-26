from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


PROPERTY_RIGHTS_EVIDENCE_SCHEMA_VERSION = "contracts.property-rights-evidence.v0"
PROPERTY_RIGHTS_MAPPING_VERSION = "contracts-reviewed-property-rights-to-facts-v0"
PROPERTY_RIGHTS_MODEL_VERSION = "contracts-property-rights-articles-209-306-v0"


class PropertyRightsEvidencePredicate(str, Enum):
    # Содержание права собственности и распоряжение (статья 209 ГК РФ).
    PROPERTY_RIGHT_ASSERTED = "property_right_asserted"
    OWNERSHIP_POWERS_BREACHED = "ownership_powers_breached"
    DISPOSAL_BY_NON_OWNER_DETECTED = "disposal_by_non_owner_detected"
    # Бремя содержания и риск случайной гибели (статьи 210 и 211 ГК РФ).
    RISK_AND_BURDEN_RULES_BREACHED = "risk_and_burden_rules_breached"
    # Основания приобретения и момент возникновения права (статьи 218 и 223 ГК РФ).
    ACQUISITION_MOMENT_RULES_BREACHED = "acquisition_moment_rules_breached"
    # Приобретательная давность (статья 234 ГК РФ).
    ACQUISITIVE_PRESCRIPTION_BREACHED = "acquisitive_prescription_breached"
    # Общая собственность (статьи 244–259 ГК РФ).
    COMMON_PROPERTY_RULES_BREACHED = "common_property_rules_breached"
    # Истребование имущества из чужого незаконного владения (статьи 301 и 302 ГК РФ).
    VINDICATION_RULES_BREACHED = "vindication_rules_breached"
    GOOD_FAITH_PURCHASER_PROTECTION_DISREGARDED = "good_faith_purchaser_protection_disregarded"
    # Защита прав владельца, не являющегося собственником (статьи 304 и 305 ГК РФ).
    NEGATORY_OR_POSSESSOR_CLAIM_BREACHED = "negatory_or_possessor_claim_breached"
    # Прекращение права собственности в силу закона (статья 306 ГК РФ).
    OWNERSHIP_TERMINATED_BY_FEDERAL_LAW = "ownership_terminated_by_federal_law"
    LOSSES_FROM_STATUTORY_TERMINATION_PROVEN = "losses_from_statutory_termination_proven"


REQUIRED_PROPERTY_RIGHTS_PREDICATES = frozenset(PropertyRightsEvidencePredicate)


class PropertyRightsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: PropertyRightsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedPropertyRightsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = PROPERTY_RIGHTS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[PropertyRightsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedPropertyRightsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Property-rights evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Property-rights evidence contains duplicate legal source refs.")
        return self


class PropertyRightsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    property_right_asserted: bool
    ownership_powers_breached: bool
    disposal_by_non_owner_detected: bool
    risk_and_burden_rules_breached: bool
    acquisition_moment_rules_breached: bool
    acquisitive_prescription_breached: bool
    common_property_rules_breached: bool
    vindication_rules_breached: bool
    good_faith_purchaser_protection_disregarded: bool
    negatory_or_possessor_claim_breached: bool
    ownership_terminated_by_federal_law: bool
    losses_from_statutory_termination_proven: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "PropertyRightsFactSet":
        if self.good_faith_purchaser_protection_disregarded and not self.vindication_rules_breached:
            raise ValueError(
                "Неучёт защиты добросовестного приобретателя относится только к случаю, когда "
                "нарушение правил об истребовании имущества установлено."
            )
        if self.ownership_powers_breached and not self.property_right_asserted:
            raise ValueError(
                "Нарушение правомочий собственника относится только к заявленному вещному праву."
            )
        if (
            self.losses_from_statutory_termination_proven
            and not self.ownership_terminated_by_federal_law
        ):
            raise ValueError(
                "Убытки от прекращения права собственности в силу закона возможны только "
                "тогда, когда такой закон принят (статья 306 ГК РФ)."
            )
        return self


class PropertyRightsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class PropertyRightsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: PropertyRightsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[PropertyRightsFactProvenance] = Field(default_factory=list)


class PropertyRightsConstraintSet(BaseModel):
    id: str
    model_version: str = PROPERTY_RIGHTS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class PropertyRightsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    property_rights_qualified: bool
    ownership_powers_duty_breached: bool
    # Ключевой вывод для слоя общих положений: имуществом распорядилось лицо,
    # не управомоченное на отчуждение (статья 209 ГК РФ).
    unauthorized_disposal_detected: bool
    risk_and_burden_duty_breached: bool
    acquisition_moment_duty_breached: bool
    acquisitive_prescription_duty_breached: bool
    common_property_duty_breached: bool
    vindication_duty_breached: bool
    good_faith_purchaser_breached: bool
    negatory_claim_duty_breached: bool
    statutory_termination_of_ownership: bool
    # Единственный вывод института, где должник — государство, а не частное лицо
    # (статья 306 ГК РФ).
    state_compensation_duty: bool
    requires_human_property_rights_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_property_rights_evidence(
    evidence: ReviewedPropertyRightsEvidence,
) -> PropertyRightsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Property-rights evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Property-rights evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_PROPERTY_RIGHTS_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed property-rights evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_PROPERTY_RIGHTS_PREDICATES
    }
    return PropertyRightsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=PROPERTY_RIGHTS_MAPPING_VERSION,
        facts=PropertyRightsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            PropertyRightsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_PROPERTY_RIGHTS_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_property_rights_constraint_set(
    mapping: PropertyRightsEvidenceMappingResult,
) -> PropertyRightsConstraintSet:
    return PropertyRightsConstraintSet(
        id=f"property-rights-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "property_rights_qualified == property_right_asserted",
            "ownership_powers_duty_breached == property_rights_qualified AND ownership_powers_breached",
            "unauthorized_disposal_detected == property_rights_qualified AND disposal_by_non_owner_detected",
            "risk_and_burden_duty_breached == property_rights_qualified AND risk_and_burden_rules_breached",
            "acquisition_moment_duty_breached == property_rights_qualified AND acquisition_moment_rules_breached",
            "acquisitive_prescription_duty_breached == property_rights_qualified AND acquisitive_prescription_breached",
            "common_property_duty_breached == property_rights_qualified AND common_property_rules_breached",
            "vindication_duty_breached == property_rights_qualified AND vindication_rules_breached",
            "good_faith_purchaser_breached == property_rights_qualified AND vindication_rules_breached AND good_faith_purchaser_protection_disregarded",
            "negatory_claim_duty_breached == property_rights_qualified AND negatory_or_possessor_claim_breached",
            "statutory_termination_of_ownership == property_rights_qualified AND ownership_terminated_by_federal_law",
            "state_compensation_duty == statutory_termination_of_ownership AND losses_from_statutory_termination_proven",
            "requires_human_property_rights_assessment == ownership_powers_duty_breached OR unauthorized_disposal_detected OR risk_and_burden_duty_breached OR acquisition_moment_duty_breached OR acquisitive_prescription_duty_breached OR common_property_duty_breached OR vindication_duty_breached OR negatory_claim_duty_breached OR statutory_termination_of_ownership",
        ],
    )


def evaluate_property_rights_constraints(
    constraint_set: PropertyRightsConstraintSet,
    facts: PropertyRightsFactSet,
) -> PropertyRightsEvaluation:
    variables = {field_name: Bool(field_name) for field_name in PropertyRightsFactSet.model_fields}
    property_rights_qualified = Bool("property_rights_qualified")
    ownership_powers_duty_breached = Bool("ownership_powers_duty_breached")
    unauthorized_disposal_detected = Bool("unauthorized_disposal_detected")
    risk_and_burden_duty_breached = Bool("risk_and_burden_duty_breached")
    acquisition_moment_duty_breached = Bool("acquisition_moment_duty_breached")
    acquisitive_prescription_duty_breached = Bool("acquisitive_prescription_duty_breached")
    common_property_duty_breached = Bool("common_property_duty_breached")
    vindication_duty_breached = Bool("vindication_duty_breached")
    good_faith_purchaser_breached = Bool("good_faith_purchaser_breached")
    negatory_claim_duty_breached = Bool("negatory_claim_duty_breached")
    statutory_termination_of_ownership = Bool("statutory_termination_of_ownership")
    state_compensation_duty = Bool("state_compensation_duty")
    requires_human_property_rights_assessment = Bool("requires_human_property_rights_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(property_rights_qualified == variables["property_right_asserted"])
    solver.add(
        ownership_powers_duty_breached
        == And(property_rights_qualified, variables["ownership_powers_breached"])
    )
    solver.add(
        unauthorized_disposal_detected
        == And(property_rights_qualified, variables["disposal_by_non_owner_detected"])
    )
    solver.add(
        risk_and_burden_duty_breached
        == And(property_rights_qualified, variables["risk_and_burden_rules_breached"])
    )
    solver.add(
        acquisition_moment_duty_breached
        == And(property_rights_qualified, variables["acquisition_moment_rules_breached"])
    )
    solver.add(
        acquisitive_prescription_duty_breached
        == And(property_rights_qualified, variables["acquisitive_prescription_breached"])
    )
    solver.add(
        common_property_duty_breached
        == And(property_rights_qualified, variables["common_property_rules_breached"])
    )
    solver.add(
        vindication_duty_breached
        == And(property_rights_qualified, variables["vindication_rules_breached"])
    )
    solver.add(
        good_faith_purchaser_breached
        == And(
            property_rights_qualified,
            variables["vindication_rules_breached"],
            variables["good_faith_purchaser_protection_disregarded"],
        )
    )
    solver.add(
        negatory_claim_duty_breached
        == And(property_rights_qualified, variables["negatory_or_possessor_claim_breached"])
    )
    solver.add(
        statutory_termination_of_ownership
        == And(property_rights_qualified, variables["ownership_terminated_by_federal_law"])
    )
    solver.add(
        state_compensation_duty
        == And(
            statutory_termination_of_ownership,
            variables["losses_from_statutory_termination_proven"],
        )
    )
    solver.add(
        requires_human_property_rights_assessment
        == Or(
            ownership_powers_duty_breached,
            unauthorized_disposal_detected,
            risk_and_burden_duty_breached,
            acquisition_moment_duty_breached,
            acquisitive_prescription_duty_breached,
            common_property_duty_breached,
            vindication_duty_breached,
            negatory_claim_duty_breached,
            statutory_termination_of_ownership,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return PropertyRightsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            property_rights_qualified=False,
            ownership_powers_duty_breached=False,
            unauthorized_disposal_detected=False,
            risk_and_burden_duty_breached=False,
            acquisition_moment_duty_breached=False,
            acquisitive_prescription_duty_breached=False,
            common_property_duty_breached=False,
            vindication_duty_breached=False,
            good_faith_purchaser_breached=False,
            negatory_claim_duty_breached=False,
            statutory_termination_of_ownership=False,
            state_compensation_duty=False,
            requires_human_property_rights_assessment=True,
            reasons_ru=["Набор фактов о вещных правах противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Заявлено вещное право: собственнику принадлежат права владения, пользования и "
            "распоряжения своим имуществом, и он вправе по своему усмотрению совершать в "
            "отношении принадлежащего ему имущества любые действия, не противоречащие закону и "
            "не нарушающие права и охраняемые законом интересы других лиц "
            "(статья 209 ГК РФ)."
            if truth(property_rights_qualified)
            else "Вещное право на спорное имущество не заявлено."
        ),
    ]
    if truth(ownership_powers_duty_breached):
        reasons_ru.append(
            "Правомочия владения, пользования и распоряжения осуществляются собственником по "
            "своему усмотрению в пределах, установленных законом, и не должны нарушать права и "
            "охраняемые законом интересы других лиц (статья 209 ГК РФ)."
        )
    if truth(unauthorized_disposal_detected):
        reasons_ru.append(
            "Распоряжение имуществом совершено лицом, не управомоченным на его отчуждение: "
            "право распоряжения принадлежит собственнику, и отчуждение чужого имущества по "
            "общему правилу не влечёт перехода права собственности к приобретателю "
            "(статьи 209 и 302 ГК РФ)."
        )
    if truth(risk_and_burden_duty_breached):
        reasons_ru.append(
            "Собственник несёт бремя содержания принадлежащего ему имущества и риск случайной "
            "гибели или случайного повреждения имущества, если иное не предусмотрено законом "
            "или договором (статьи 210 и 211 ГК РФ)."
        )
    if truth(acquisition_moment_duty_breached):
        reasons_ru.append(
            "Право собственности у приобретателя вещи по договору возникает с момента её "
            "передачи, если иное не предусмотрено законом или договором, а если отчуждение "
            "подлежит государственной регистрации — с момента такой регистрации "
            "(статьи 218 и 223 ГК РФ)."
        )
    if truth(acquisitive_prescription_duty_breached):
        reasons_ru.append(
            "Лицо, не являющееся собственником, но добросовестно, открыто и непрерывно "
            "владеющее как своим собственным недвижимым имуществом в течение пятнадцати лет "
            "либо иным имуществом в течение пяти лет, приобретает право собственности на это "
            "имущество (статья 234 ГК РФ)."
        )
    if truth(common_property_duty_breached):
        reasons_ru.append(
            "Владение, пользование и распоряжение имуществом, находящимся в общей долевой "
            "собственности, осуществляются по соглашению всех её участников, а распоряжение "
            "имуществом в совместной собственности — по согласию всех сособственников "
            "(статьи 244–259 ГК РФ)."
        )
    if truth(vindication_duty_breached):
        reasons_ru.append(
            "Собственник вправе истребовать своё имущество из чужого незаконного владения "
            "(статья 301 ГК РФ)."
        )
    if truth(good_faith_purchaser_breached):
        reasons_ru.append(
            "Если имущество возмездно приобретено у лица, которое не имело права его отчуждать, "
            "о чём приобретатель не знал и не мог знать, собственник вправе истребовать это "
            "имущество только в случаях, когда оно утеряно собственником, похищено либо выбыло "
            "из его владения иным путём помимо его воли; деньги и ценные бумаги на предъявителя "
            "у добросовестного приобретателя истребованы быть не могут (статья 302 ГК РФ)."
        )
    if truth(negatory_claim_duty_breached):
        reasons_ru.append(
            "Собственник может требовать устранения всяких нарушений его права, хотя бы эти "
            "нарушения и не были соединены с лишением владения; такая защита принадлежит также "
            "лицу, владеющему имуществом по иному основанию, предусмотренному законом или "
            "договором, в том числе против самого собственника (статьи 304 и 305 ГК РФ)."
        )
    if truth(statutory_termination_of_ownership):
        reasons_ru.append(
            "Право собственности прекращено принятием закона Российской Федерации. Убытки, "
            "причинённые собственнику принятием этого акта, в том числе стоимость имущества, "
            "возмещаются государством (статья 306 ГК РФ). Это единственный случай в институте, "
            "где обязанным лицом выступает государство, а не частная сторона спора."
        )
    if truth(state_compensation_duty):
        reasons_ru.append(
            "Убытки от прекращения права собственности в силу закона доказаны, поэтому "
            "обязанность их возмещения лежит на государстве; спор о возмещении разрешается "
            "судом (статья 306 ГК РФ)."
        )
    elif truth(statutory_termination_of_ownership):
        reasons_ru.append(
            "Размер убытков от прекращения права собственности не доказан, поэтому обязанность "
            "государства возместить их модель не выводит. Это утверждение о доказанности "
            "убытков, а не о том, что право на возмещение отсутствует."
        )
    return PropertyRightsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        property_rights_qualified=truth(property_rights_qualified),
        ownership_powers_duty_breached=truth(ownership_powers_duty_breached),
        unauthorized_disposal_detected=truth(unauthorized_disposal_detected),
        risk_and_burden_duty_breached=truth(risk_and_burden_duty_breached),
        acquisition_moment_duty_breached=truth(acquisition_moment_duty_breached),
        acquisitive_prescription_duty_breached=truth(acquisitive_prescription_duty_breached),
        common_property_duty_breached=truth(common_property_duty_breached),
        vindication_duty_breached=truth(vindication_duty_breached),
        good_faith_purchaser_breached=truth(good_faith_purchaser_breached),
        negatory_claim_duty_breached=truth(negatory_claim_duty_breached),
        statutory_termination_of_ownership=truth(statutory_termination_of_ownership),
        state_compensation_duty=truth(state_compensation_duty),
        requires_human_property_rights_assessment=truth(requires_human_property_rights_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о праве собственности и его защите и не "
            "заменяет судебную оценку.",
            "Добросовестность приобретателя, обстоятельства выбытия имущества из владения "
            "собственника и давностное владение оцениваются экспертом и судом "
            "(статьи 234, 302 и 305 ГК РФ).",
            "Размер убытков от прекращения права собственности в силу закона модель не "
            "считает: она отвечает о наличии обязанности государства, а не о сумме "
            "возмещения (статья 306 ГК РФ).",
        ],
    )
