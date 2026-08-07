"""Слой сверки фактов между институтами пакета.

Один и тот же факт дела описывается предикатами нескольких институтов: например,
недееспособность стороны — предикатом `incapacity_declared_by_court` модели лиц
и предикатом `incapacitated_person_transaction` модели недействительности. До
появления этого слоя такие пары не сверялись: рецензент мог утвердить факт в
одном институте и отрицать в другом, а анализ молча выбирал одну из версий и
выдавал уверенный вывод.

Слой устроен как второй узел без собственного проверенного контракта данных.
В отличие от слоя общих положений, его входы — не выводы институтов, а сами
проверенные **факты** (плюс вывод модели заключения договора, поскольку
заключённость выводится из нескольких фактов сразу).

Слой ничего не исправляет и не выбирает версию: он называет противоречие и
поднимает флаг экспертизы. Устранение противоречия — работа рецензента, а не
решателя.
"""

from pydantic import BaseModel, ConfigDict, Field
from z3 import And, Bool, Not, Or, Solver, sat

GENERAL_CONSISTENCY_MODEL_VERSION = "contracts-general-cross-institute-consistency-v0"


class GeneralConsistencyInputs(BaseModel):
    """Входы слоя — проверенные факты разных институтов, описывающие одно и то же."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Лица (статьи 17–53) и недействительность (статьи 166–181).
    persons_incapacity_declared: bool
    invalidity_incapacitated_person_transaction: bool
    persons_entity_capacity_breached: bool
    invalidity_entity_beyond_statutory_purpose: bool
    persons_limited_capacity_without_consent: bool
    invalidity_limited_capacity_without_consent: bool
    persons_age_capacity_breached: bool
    invalidity_minor_under_14_transaction: bool
    # Сделки (статья 157.1) и недействительность (статья 173.1).
    transactions_statutory_consent_absent: bool
    invalidity_required_consent_absent: bool
    # Объекты (статья 129) и недействительность (пункт 2 статьи 168).
    objects_not_in_civil_circulation: bool
    invalidity_violates_law: bool
    # Заключение договора (статьи 432–443) и смежные институты.
    formation_contract_concluded: bool
    invalidity_transaction_concluded: bool
    termination_contract_formed: bool
    formation_required_form_observed: bool
    form_written_form_required: bool
    form_written_form_observed: bool
    form_noncompliance_invalidates: bool
    invalidity_public_interests_affected: bool


class GeneralConsistencyConstraintSet(BaseModel):
    id: str
    model_version: str = GENERAL_CONSISTENCY_MODEL_VERSION
    source_evidence: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class GeneralConsistencyEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    capacity_invalidity_conflict: bool
    entity_capacity_invalidity_conflict: bool
    limited_capacity_invalidity_conflict: bool
    minor_capacity_invalidity_conflict: bool
    consent_invalidity_conflict: bool
    circulation_lawfulness_conflict: bool
    formation_invalidity_conclusion_conflict: bool
    formation_termination_conclusion_conflict: bool
    formation_form_observance_conflict: bool
    circulation_public_interest_conflict: bool
    contradictions_detected: bool
    requires_human_consistency_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def build_general_consistency_inputs(
    persons_facts,
    invalidity_facts,
    transactions_facts,
    objects_facts,
    form_facts,
    formation_facts,
    termination_facts,
    formation_evaluation,
) -> GeneralConsistencyInputs:
    """Собрать входы слоя из проверенных фактов институтов."""
    return GeneralConsistencyInputs(
        persons_incapacity_declared=persons_facts.incapacity_declared_by_court,
        invalidity_incapacitated_person_transaction=(
            invalidity_facts.incapacitated_person_transaction
        ),
        persons_entity_capacity_breached=persons_facts.entity_capacity_scope_breached,
        invalidity_entity_beyond_statutory_purpose=invalidity_facts.entity_beyond_statutory_purpose,
        persons_limited_capacity_without_consent=(
            persons_facts.limited_capacity_rules_breached
            and persons_facts.guardianship_consent_missing
        ),
        invalidity_limited_capacity_without_consent=invalidity_facts.limited_capacity_without_consent,
        persons_age_capacity_breached=persons_facts.active_capacity_age_rules_breached,
        invalidity_minor_under_14_transaction=invalidity_facts.minor_under_14_transaction,
        transactions_statutory_consent_absent=transactions_facts.statutory_consent_not_obtained,
        invalidity_required_consent_absent=invalidity_facts.required_consent_absent,
        objects_not_in_civil_circulation=objects_facts.object_not_in_civil_circulation,
        invalidity_violates_law=invalidity_facts.violates_law,
        formation_contract_concluded=formation_evaluation.contract_concluded_prerequisites,
        invalidity_transaction_concluded=invalidity_facts.transaction_concluded,
        termination_contract_formed=termination_facts.contract_formed,
        formation_required_form_observed=formation_facts.required_form_observed,
        form_written_form_required=form_facts.simple_written_form_required,
        form_written_form_observed=form_facts.simple_written_form_observed,
        form_noncompliance_invalidates=(
            form_facts.written_noncompliance_invalidates_by_law_or_agreement
        ),
        invalidity_public_interests_affected=(
            invalidity_facts.public_interests_or_third_rights_affected
        ),
    )


def build_general_consistency_constraint_set(
    inputs: GeneralConsistencyInputs,
    case_id: str,
) -> GeneralConsistencyConstraintSet:
    return GeneralConsistencyConstraintSet(
        id=f"general-consistency-constraint-set:{case_id}",
        source_evidence=[
            "persons_evidence",
            "invalidity_evidence",
            "transactions_evidence",
            "objects_evidence",
            "form_evidence",
            "formation_evidence",
            "termination_evidence",
        ],
        expressions=[
            "capacity_invalidity_conflict == persons_incapacity_declared AND NOT invalidity_incapacitated_person_transaction",
            "entity_capacity_invalidity_conflict == persons_entity_capacity_breached AND NOT invalidity_entity_beyond_statutory_purpose",
            "limited_capacity_invalidity_conflict == persons_limited_capacity_without_consent AND NOT invalidity_limited_capacity_without_consent",
            "minor_capacity_invalidity_conflict == invalidity_minor_under_14_transaction AND NOT persons_age_capacity_breached",
            "consent_invalidity_conflict == transactions_statutory_consent_absent AND NOT invalidity_required_consent_absent",
            "circulation_lawfulness_conflict == objects_not_in_civil_circulation AND NOT invalidity_violates_law",
            "formation_invalidity_conclusion_conflict == NOT formation_contract_concluded AND invalidity_transaction_concluded",
            "formation_termination_conclusion_conflict == NOT formation_contract_concluded AND termination_contract_formed",
            "formation_form_observance_conflict == formation_required_form_observed AND form_written_form_required AND NOT form_written_form_observed AND form_noncompliance_invalidates",
            "circulation_public_interest_conflict == objects_not_in_civil_circulation AND NOT invalidity_public_interests_affected",
            "contradictions_detected == capacity_invalidity_conflict OR entity_capacity_invalidity_conflict OR limited_capacity_invalidity_conflict OR minor_capacity_invalidity_conflict OR consent_invalidity_conflict OR circulation_lawfulness_conflict OR formation_invalidity_conclusion_conflict OR formation_termination_conclusion_conflict OR formation_form_observance_conflict OR circulation_public_interest_conflict",
            "requires_human_consistency_assessment == contradictions_detected",
        ],
    )


def evaluate_general_consistency_constraints(
    constraint_set: GeneralConsistencyConstraintSet,
    inputs: GeneralConsistencyInputs,
) -> GeneralConsistencyEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in GeneralConsistencyInputs.model_fields
    }
    capacity_invalidity_conflict = Bool("capacity_invalidity_conflict")
    entity_capacity_invalidity_conflict = Bool("entity_capacity_invalidity_conflict")
    limited_capacity_invalidity_conflict = Bool("limited_capacity_invalidity_conflict")
    minor_capacity_invalidity_conflict = Bool("minor_capacity_invalidity_conflict")
    consent_invalidity_conflict = Bool("consent_invalidity_conflict")
    circulation_lawfulness_conflict = Bool("circulation_lawfulness_conflict")
    formation_invalidity_conclusion_conflict = Bool("formation_invalidity_conclusion_conflict")
    formation_termination_conclusion_conflict = Bool("formation_termination_conclusion_conflict")
    formation_form_observance_conflict = Bool("formation_form_observance_conflict")
    circulation_public_interest_conflict = Bool("circulation_public_interest_conflict")
    contradictions_detected = Bool("contradictions_detected")
    requires_human_consistency_assessment = Bool("requires_human_consistency_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(inputs, field_name))
    solver.add(
        capacity_invalidity_conflict
        == And(
            variables["persons_incapacity_declared"],
            Not(variables["invalidity_incapacitated_person_transaction"]),
        )
    )
    solver.add(
        entity_capacity_invalidity_conflict
        == And(
            variables["persons_entity_capacity_breached"],
            Not(variables["invalidity_entity_beyond_statutory_purpose"]),
        )
    )
    solver.add(
        limited_capacity_invalidity_conflict
        == And(
            variables["persons_limited_capacity_without_consent"],
            Not(variables["invalidity_limited_capacity_without_consent"]),
        )
    )
    solver.add(
        minor_capacity_invalidity_conflict
        == And(
            variables["invalidity_minor_under_14_transaction"],
            Not(variables["persons_age_capacity_breached"]),
        )
    )
    solver.add(
        consent_invalidity_conflict
        == And(
            variables["transactions_statutory_consent_absent"],
            Not(variables["invalidity_required_consent_absent"]),
        )
    )
    solver.add(
        circulation_lawfulness_conflict
        == And(
            variables["objects_not_in_civil_circulation"],
            Not(variables["invalidity_violates_law"]),
        )
    )
    solver.add(
        formation_invalidity_conclusion_conflict
        == And(
            Not(variables["formation_contract_concluded"]),
            variables["invalidity_transaction_concluded"],
        )
    )
    solver.add(
        formation_termination_conclusion_conflict
        == And(
            Not(variables["formation_contract_concluded"]),
            variables["termination_contract_formed"],
        )
    )
    solver.add(
        formation_form_observance_conflict
        == And(
            variables["formation_required_form_observed"],
            variables["form_written_form_required"],
            Not(variables["form_written_form_observed"]),
            variables["form_noncompliance_invalidates"],
        )
    )
    solver.add(
        circulation_public_interest_conflict
        == And(
            variables["objects_not_in_civil_circulation"],
            Not(variables["invalidity_public_interests_affected"]),
        )
    )
    solver.add(
        contradictions_detected
        == Or(
            capacity_invalidity_conflict,
            entity_capacity_invalidity_conflict,
            limited_capacity_invalidity_conflict,
            minor_capacity_invalidity_conflict,
            consent_invalidity_conflict,
            circulation_lawfulness_conflict,
            formation_invalidity_conclusion_conflict,
            formation_termination_conclusion_conflict,
            formation_form_observance_conflict,
            circulation_public_interest_conflict,
        )
    )
    solver.add(requires_human_consistency_assessment == contradictions_detected)

    satisfiable = solver.check() == sat
    if not satisfiable:
        return GeneralConsistencyEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            capacity_invalidity_conflict=False,
            entity_capacity_invalidity_conflict=False,
            limited_capacity_invalidity_conflict=False,
            minor_capacity_invalidity_conflict=False,
            consent_invalidity_conflict=False,
            circulation_lawfulness_conflict=False,
            formation_invalidity_conclusion_conflict=False,
            formation_termination_conclusion_conflict=False,
            formation_form_observance_conflict=False,
            circulation_public_interest_conflict=False,
            contradictions_detected=True,
            requires_human_consistency_assessment=True,
            reasons_ru=["Проверенные факты институтов несовместимы между собой."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru: list[str] = []
    if truth(capacity_invalidity_conflict):
        reasons_ru.append(
            "Противоречие между институтами: модель лиц утверждает, что сторона признана судом "
            "недееспособной (статья 29 ГК РФ), а модель недействительности отрицает совершение "
            "сделки недееспособным гражданином (статья 171 ГК РФ). Один и тот же факт дела "
            "описан по-разному."
        )
    if truth(entity_capacity_invalidity_conflict):
        reasons_ru.append(
            "Противоречие между институтами: модель лиц утверждает выход за пределы "
            "правоспособности юридического лица (статья 49 ГК РФ), а модель недействительности "
            "отрицает совершение сделки за пределами уставных целей (статья 173 ГК РФ)."
        )
    if truth(limited_capacity_invalidity_conflict):
        reasons_ru.append(
            "Противоречие между институтами: модель лиц утверждает совершение сделки "
            "ограниченно дееспособным гражданином без согласия попечителя (статья 30 ГК РФ), а "
            "модель недействительности этот факт отрицает (статья 176 ГК РФ)."
        )
    if truth(minor_capacity_invalidity_conflict):
        reasons_ru.append(
            "Противоречие между институтами: модель недействительности утверждает совершение "
            "сделки малолетним (статья 172 ГК РФ), а модель лиц не фиксирует нарушение правил "
            "о дееспособности по возрасту (статья 28 ГК РФ)."
        )
    if truth(consent_invalidity_conflict):
        reasons_ru.append(
            "Противоречие между институтами: модель сделок утверждает отсутствие необходимого "
            "в силу закона согласия на совершение сделки (статья 157.1 ГК РФ), а модель "
            "недействительности этот факт отрицает (статья 173.1 ГК РФ)."
        )
    if truth(circulation_lawfulness_conflict):
        reasons_ru.append(
            "Противоречие между институтами: модель объектов утверждает, что объект изъят из "
            "оборота либо ограничен в обороте (статья 129 ГК РФ), а модель недействительности "
            "отрицает нарушение сделкой требований закона (статья 168 ГК РФ). Отчуждение "
            "такого объекта требованиям закона противоречит."
        )
    if truth(formation_invalidity_conclusion_conflict):
        reasons_ru.append(
            "Противоречие между институтами: модель заключения договора не находит оснований "
            "считать договор заключённым (статья 432 ГК РФ), а модель недействительности "
            "исходит из совершённой сделки. Незаключённая сделка не может быть оценена на "
            "недействительность."
        )
    if truth(formation_termination_conclusion_conflict):
        reasons_ru.append(
            "Противоречие между институтами: модель заключения договора не находит оснований "
            "считать договор заключённым (статья 432 ГК РФ), а модель изменения и расторжения "
            "исходит из заключённого договора (статьи 450–453 ГК РФ)."
        )
    if truth(formation_form_observance_conflict):
        reasons_ru.append(
            "Противоречие между институтами: модель заключения договора утверждает соблюдение "
            "требуемой формы (статья 432 ГК РФ), а модель формы сделки — что письменная форма "
            "требовалась, не соблюдена и закон либо соглашение сторон связывают с этим "
            "недействительность (статьи 158–162 ГК РФ)."
        )
    if truth(circulation_public_interest_conflict):
        reasons_ru.append(
            "Противоречие между институтами: модель объектов утверждает, что объект изъят из "
            "оборота либо ограничен в обороте (статья 129 ГК РФ), а модель недействительности "
            "отрицает посягательство сделки на публичные интересы. Ничтожность по пункту 2 "
            "статьи 168 ГК РФ требует и нарушения закона, и такого посягательства."
        )
    if not reasons_ru:
        reasons_ru.append(
            "Проверенные факты институтов согласованы между собой: описания одних и тех же "
            "обстоятельств дела в разных моделях совпадают."
        )
    return GeneralConsistencyEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        capacity_invalidity_conflict=truth(capacity_invalidity_conflict),
        entity_capacity_invalidity_conflict=truth(entity_capacity_invalidity_conflict),
        limited_capacity_invalidity_conflict=truth(limited_capacity_invalidity_conflict),
        minor_capacity_invalidity_conflict=truth(minor_capacity_invalidity_conflict),
        consent_invalidity_conflict=truth(consent_invalidity_conflict),
        circulation_lawfulness_conflict=truth(circulation_lawfulness_conflict),
        formation_invalidity_conclusion_conflict=truth(formation_invalidity_conclusion_conflict),
        formation_termination_conclusion_conflict=truth(formation_termination_conclusion_conflict),
        formation_form_observance_conflict=truth(formation_form_observance_conflict),
        circulation_public_interest_conflict=truth(circulation_public_interest_conflict),
        contradictions_detected=truth(contradictions_detected),
        requires_human_consistency_assessment=truth(requires_human_consistency_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Слой только называет противоречие между проверенными фактами институтов и не "
            "выбирает, какая из версий верна: устранение противоречия — работа рецензента.",
            "Отсутствие противоречий в этом слое не означает правильности фактов: слой "
            "сверяет описания между собой, а не с материалами дела.",
        ],
    )
