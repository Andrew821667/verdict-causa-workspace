"""Формальная модель исчисления сроков по статьям 190–194 ГК РФ.

Модель разделяет определение срока календарной датой, истечением периода
времени или указанием на неизбежное событие, начало течения срока, его
окончание в годах, месяцах, неделях и полумесяцах, перенос окончания срока на
ближайший следующий рабочий день, совершение действия до двадцати четырёх часов
последнего дня срока, прекращение соответствующих операций в организации и
сдачу письменных заявлений в организацию связи.

Ключевой вывод для слоя общих положений — `term_calculation_defective`: срок
исковой давности исчислен с нарушением правил главы 11 ГК РФ. Исковая давность
исчисляется по этим правилам, поэтому при пороке исчисления вывод модели
статей 195–208 об истечении срока не может быть положен в основание отказа в
иске: слой снимает препятствие к судебной защите и помечает вывод о давности
как недостоверный.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


TERMS_EVIDENCE_SCHEMA_VERSION = "contracts.terms-evidence.v0"
TERMS_MAPPING_VERSION = "contracts-reviewed-terms-to-facts-v0"
TERMS_MODEL_VERSION = "contracts-terms-articles-190-194-v0"


class TermsEvidencePredicate(str, Enum):
    # Определение срока (статья 190 ГК РФ).
    TERM_ASSERTED = "term_asserted"
    TERM_DEFINITION_BREACHED = "term_definition_breached"
    TERM_EVENT_CERTAINTY_BREACHED = "term_event_certainty_breached"
    # Начало и окончание срока (статьи 191–193 ГК РФ).
    TERM_START_RULES_BREACHED = "term_start_rules_breached"
    TERM_END_RULES_BREACHED = "term_end_rules_breached"
    NON_WORKING_DAY_RULE_BREACHED = "non_working_day_rule_breached"
    # Исчисление срока исковой давности по правилам главы 11 ГК РФ.
    LIMITATION_TERM_CALCULATION_BREACHED = "limitation_term_calculation_breached"
    # Порядок совершения действий в последний день срока (статья 194 ГК РФ).
    PERFORMANCE_DEADLINE_BREACHED = "performance_deadline_breached"
    ORGANISATION_OPERATING_HOURS_BREACHED = "organisation_operating_hours_breached"
    WRITTEN_NOTICE_DISPATCH_BREACHED = "written_notice_dispatch_breached"


REQUIRED_TERMS_PREDICATES = frozenset(TermsEvidencePredicate)


class TermsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: TermsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedTermsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = TERMS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[TermsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedTermsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Terms evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Terms evidence contains duplicate legal source refs.")
        return self


class TermsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    term_asserted: bool
    term_definition_breached: bool
    term_event_certainty_breached: bool
    term_start_rules_breached: bool
    term_end_rules_breached: bool
    non_working_day_rule_breached: bool
    limitation_term_calculation_breached: bool
    performance_deadline_breached: bool
    organisation_operating_hours_breached: bool
    written_notice_dispatch_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "TermsFactSet":
        if self.term_event_certainty_breached and not self.term_definition_breached:
            raise ValueError(
                "Порок неизбежности события относится только к случаю, когда определение "
                "срока нарушено."
            )
        if self.limitation_term_calculation_breached and not self.term_asserted:
            raise ValueError(
                "Нарушение исчисления срока исковой давности относится только к заявленному сроку."
            )
        return self


class TermsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class TermsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: TermsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[TermsFactProvenance] = Field(default_factory=list)


class TermsConstraintSet(BaseModel):
    id: str
    model_version: str = TERMS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class TermsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    terms_qualified: bool
    term_definition_duty_breached: bool
    term_event_certainty_duty_breached: bool
    term_start_duty_breached: bool
    term_end_duty_breached: bool
    non_working_day_duty_breached: bool
    # Ключевой вывод для слоя общих положений: срок исковой давности исчислен с
    # нарушением правил главы 11 ГК РФ (статьи 190–194).
    term_calculation_defective: bool
    performance_deadline_duty_breached: bool
    organisation_operating_hours_duty_breached: bool
    written_notice_dispatch_duty_breached: bool
    requires_human_terms_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_terms_evidence(evidence: ReviewedTermsEvidence) -> TermsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Terms evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Terms evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(predicate.value for predicate in REQUIRED_TERMS_PREDICATES - assertions.keys())
    if missing:
        raise ValueError(
            "Reviewed terms evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_TERMS_PREDICATES
    }
    return TermsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=TERMS_MAPPING_VERSION,
        facts=TermsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            TermsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_TERMS_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_terms_constraint_set(mapping: TermsEvidenceMappingResult) -> TermsConstraintSet:
    return TermsConstraintSet(
        id=f"terms-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "terms_qualified == term_asserted",
            "term_definition_duty_breached == terms_qualified AND term_definition_breached",
            "term_event_certainty_duty_breached == terms_qualified AND term_definition_breached AND term_event_certainty_breached",
            "term_start_duty_breached == terms_qualified AND term_start_rules_breached",
            "term_end_duty_breached == terms_qualified AND term_end_rules_breached",
            "non_working_day_duty_breached == terms_qualified AND non_working_day_rule_breached",
            "term_calculation_defective == terms_qualified AND limitation_term_calculation_breached",
            "performance_deadline_duty_breached == terms_qualified AND performance_deadline_breached",
            "organisation_operating_hours_duty_breached == terms_qualified AND organisation_operating_hours_breached",
            "written_notice_dispatch_duty_breached == terms_qualified AND written_notice_dispatch_breached",
            "requires_human_terms_assessment == term_definition_duty_breached OR term_start_duty_breached OR term_end_duty_breached OR non_working_day_duty_breached OR term_calculation_defective OR performance_deadline_duty_breached OR organisation_operating_hours_duty_breached OR written_notice_dispatch_duty_breached",
        ],
    )


def evaluate_terms_constraints(
    constraint_set: TermsConstraintSet,
    facts: TermsFactSet,
) -> TermsEvaluation:
    variables = {field_name: Bool(field_name) for field_name in TermsFactSet.model_fields}
    terms_qualified = Bool("terms_qualified")
    term_definition_duty_breached = Bool("term_definition_duty_breached")
    term_event_certainty_duty_breached = Bool("term_event_certainty_duty_breached")
    term_start_duty_breached = Bool("term_start_duty_breached")
    term_end_duty_breached = Bool("term_end_duty_breached")
    non_working_day_duty_breached = Bool("non_working_day_duty_breached")
    term_calculation_defective = Bool("term_calculation_defective")
    performance_deadline_duty_breached = Bool("performance_deadline_duty_breached")
    organisation_operating_hours_duty_breached = Bool("organisation_operating_hours_duty_breached")
    written_notice_dispatch_duty_breached = Bool("written_notice_dispatch_duty_breached")
    requires_human_terms_assessment = Bool("requires_human_terms_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(terms_qualified == variables["term_asserted"])
    solver.add(
        term_definition_duty_breached == And(terms_qualified, variables["term_definition_breached"])
    )
    solver.add(
        term_event_certainty_duty_breached
        == And(
            terms_qualified,
            variables["term_definition_breached"],
            variables["term_event_certainty_breached"],
        )
    )
    solver.add(
        term_start_duty_breached == And(terms_qualified, variables["term_start_rules_breached"])
    )
    solver.add(term_end_duty_breached == And(terms_qualified, variables["term_end_rules_breached"]))
    solver.add(
        non_working_day_duty_breached
        == And(terms_qualified, variables["non_working_day_rule_breached"])
    )
    solver.add(
        term_calculation_defective
        == And(terms_qualified, variables["limitation_term_calculation_breached"])
    )
    solver.add(
        performance_deadline_duty_breached
        == And(terms_qualified, variables["performance_deadline_breached"])
    )
    solver.add(
        organisation_operating_hours_duty_breached
        == And(terms_qualified, variables["organisation_operating_hours_breached"])
    )
    solver.add(
        written_notice_dispatch_duty_breached
        == And(terms_qualified, variables["written_notice_dispatch_breached"])
    )
    solver.add(
        requires_human_terms_assessment
        == Or(
            term_definition_duty_breached,
            term_start_duty_breached,
            term_end_duty_breached,
            non_working_day_duty_breached,
            term_calculation_defective,
            performance_deadline_duty_breached,
            organisation_operating_hours_duty_breached,
            written_notice_dispatch_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return TermsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            terms_qualified=False,
            term_definition_duty_breached=False,
            term_event_certainty_duty_breached=False,
            term_start_duty_breached=False,
            term_end_duty_breached=False,
            non_working_day_duty_breached=False,
            term_calculation_defective=False,
            performance_deadline_duty_breached=False,
            organisation_operating_hours_duty_breached=False,
            written_notice_dispatch_duty_breached=False,
            requires_human_terms_assessment=True,
            reasons_ru=["Набор фактов об исчислении срока противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Заявлен срок: установленный законом, иными правовыми актами, сделкой или "
            "назначаемый судом срок определяется календарной датой или истечением периода "
            "времени, который исчисляется годами, месяцами, неделями, днями или часами "
            "(статья 190 ГК РФ)."
            if truth(terms_qualified)
            else "Срок в деле не заявлен."
        ),
    ]
    if truth(term_definition_duty_breached):
        reasons_ru.append(
            "Срок определён с нарушением: он определяется календарной датой, истечением "
            "периода времени либо указанием на событие (статья 190 ГК РФ)."
        )
    if truth(term_event_certainty_duty_breached):
        reasons_ru.append(
            "Срок определён указанием на событие, которое не должно неизбежно наступить, "
            "тогда как срок может определяться указанием лишь на такое событие, которое "
            "должно неизбежно наступить (статья 190 ГК РФ)."
        )
    if truth(term_start_duty_breached):
        reasons_ru.append(
            "Начало срока определено неверно: течение срока, определённого периодом времени, "
            "начинается на следующий день после календарной даты или наступления события, "
            "которыми определено его начало (статья 191 ГК РФ)."
        )
    if truth(term_end_duty_breached):
        reasons_ru.append(
            "Окончание срока определено неверно: срок, исчисляемый годами, истекает в "
            "соответствующие месяц и число последнего года срока; к срокам, исчисляемым "
            "полугодами, кварталами, месяцами, неделями и полумесяцами, применяются "
            "соответствующие правила (статья 192 ГК РФ)."
        )
    if truth(non_working_day_duty_breached):
        reasons_ru.append(
            "Не применено правило о нерабочем дне: если последний день срока приходится на "
            "нерабочий день, днём окончания срока считается ближайший следующий за ним "
            "рабочий день (статья 193 ГК РФ)."
        )
    if truth(term_calculation_defective):
        reasons_ru.append(
            "Срок исковой давности исчислен с нарушением правил об исчислении сроков: "
            "определение срока, начало его течения, окончание и перенос на ближайший "
            "следующий рабочий день подчиняются статьям 190–193 ГК РФ, поэтому вывод об "
            "истечении срока исковой давности не может считаться установленным."
        )
    if truth(performance_deadline_duty_breached):
        reasons_ru.append(
            "Нарушен порядок совершения действий в последний день срока: если срок установлен "
            "для совершения какого-либо действия, оно может быть выполнено до двадцати "
            "четырёх часов последнего дня срока (статья 194 ГК РФ)."
        )
    if truth(organisation_operating_hours_duty_breached):
        reasons_ru.append(
            "Не учтено правило об операциях в организации: если действие должно быть "
            "совершено в организации, срок истекает в тот час, когда в этой организации по "
            "установленным правилам прекращаются соответствующие операции "
            "(статья 194 ГК РФ)."
        )
    if truth(written_notice_dispatch_duty_breached):
        reasons_ru.append(
            "Не учтена сдача письменных заявлений и извещений в организацию связи: сданные "
            "до двадцати четырёх часов последнего дня срока, они считаются совершёнными в "
            "срок (статья 194 ГК РФ)."
        )
    return TermsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        terms_qualified=truth(terms_qualified),
        term_definition_duty_breached=truth(term_definition_duty_breached),
        term_event_certainty_duty_breached=truth(term_event_certainty_duty_breached),
        term_start_duty_breached=truth(term_start_duty_breached),
        term_end_duty_breached=truth(term_end_duty_breached),
        non_working_day_duty_breached=truth(non_working_day_duty_breached),
        term_calculation_defective=truth(term_calculation_defective),
        performance_deadline_duty_breached=truth(performance_deadline_duty_breached),
        organisation_operating_hours_duty_breached=truth(
            organisation_operating_hours_duty_breached
        ),
        written_notice_dispatch_duty_breached=truth(written_notice_dispatch_duty_breached),
        requires_human_terms_assessment=truth(requires_human_terms_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила об исчислении сроков и не заменяет "
            "судебную оценку.",
            "Неизбежность события, которым определён срок, режим рабочих и нерабочих дней и "
            "фактическое время совершения действия оцениваются экспертом и судом "
            "(статьи 190, 193 и 194 ГК РФ).",
        ],
    )
