"""Прогон модели на реальных делах из полученной выгрузки судебной практики.

Отличие от двух предыдущих наборов — в источнике ожидания:

| набор | откуда взят ожидаемый итог |
|---|---|
| `case_scenarios` | текст ГК РФ в моём прочтении |
| `practice_scenarios` | опубликованные разъяснения Пленума, сверенные по выдаче поиска |
| `real_case_scenarios` | **решения по конкретным делам** из выгрузки `data/practice/cases.jsonl` |

Каждое дело здесь — запись выгрузки: фабула написана выгружающей стороной как
обстоятельства, установленные судом, а перевод в предикаты института сделан
здесь. Разделение сохранено намеренно: если бы предикаты проставляла
выгружающая сторона, ожидание перестало бы быть независимым от модели.

**Что здесь проверяется и что нет.** Дело даёт факты для одного института, и
проверяется вывод этого института. Полный конвейер `run_reviewed_contract_analysis`
не запускается: он требует согласованных данных по семи контрактам сразу, а дело
их не содержит. Дополнять недостающее пришлось бы мне — и проверка вернулась бы
к сверке модели с моими же предположениями.

**Перевод фабулы в предикаты — это тоже интерпретация.** Там, где предикат
выведен из фабулы не буквально, рассуждение записано в `mapping_note_ru`, а не
спрятано. Несовпадение вывода модели с решением суда поэтому означает одно из
двух: ошибку модели или ошибку перевода, — и разбирать его нужно с обеих сторон.
"""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from causa.institutional.contracts.freedom import (
    build_freedom_constraint_set,
    evaluate_freedom_constraints,
    map_reviewed_freedom_evidence,
)
from causa.institutional.contracts.limitation import (
    build_limitation_constraint_set,
    evaluate_limitation_constraints,
    map_reviewed_limitation_evidence,
)
from causa.institutional.contracts.property_rights import (
    build_property_rights_constraint_set,
    evaluate_property_rights_constraints,
    map_reviewed_property_rights_evidence,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)
from causa.institutional.contracts.terms import (
    build_terms_constraint_set,
    evaluate_terms_constraints,
    map_reviewed_terms_evidence,
)

REAL_CASE_SUITE_VERSION = "contracts-real-case-scenarios-v0"


class InstituteRunner(BaseModel):
    """Как запустить один институт по подменённым фактам."""

    model_config = {"arbitrary_types_allowed": True}

    evidence_field: str
    map_evidence: Callable[[Any], Any]
    build_constraints: Callable[[Any], Any]
    evaluate: Callable[[Any, Any], Any]


INSTITUTE_RUNNERS: dict[str, InstituteRunner] = {
    "terms": InstituteRunner(
        evidence_field="terms_evidence",
        map_evidence=map_reviewed_terms_evidence,
        build_constraints=build_terms_constraint_set,
        evaluate=evaluate_terms_constraints,
    ),
    "limitation": InstituteRunner(
        evidence_field="limitation_evidence",
        map_evidence=map_reviewed_limitation_evidence,
        build_constraints=build_limitation_constraint_set,
        evaluate=evaluate_limitation_constraints,
    ),
    "property_rights": InstituteRunner(
        evidence_field="property_rights_evidence",
        map_evidence=map_reviewed_property_rights_evidence,
        build_constraints=build_property_rights_constraint_set,
        evaluate=evaluate_property_rights_constraints,
    ),
    "freedom": InstituteRunner(
        evidence_field="freedom_evidence",
        map_evidence=map_reviewed_freedom_evidence,
        build_constraints=build_freedom_constraint_set,
        evaluate=evaluate_freedom_constraints,
    ),
}


class RealCaseScenario(BaseModel):
    """Реальное дело, переведённое в факты одного института."""

    #: Идентификатор записи в `data/practice/cases.jsonl`.
    case_id: str
    case_number: str
    institute: str
    #: Правовая позиция суда по этому делу — источник ожидания.
    court_holding_ru: str
    #: Как фабула переведена в предикаты и что при этом достроено.
    mapping_note_ru: str
    facts: dict[str, bool]
    expected_conclusions: dict[str, bool]


#: Дела с окончательным исходом, которые в набор не вошли, и почему.
#:
#: Отказ от перевода — такой же результат, как перевод: он показывает границу
#: применимости модели к реальной практике.
UNMAPPED_FINAL_CASES_RU: dict[str, str] = {
    "vs-41-kg21-49-k4": (
        "Спор разрешён по Закону об ОСАГО: право на денежное возмещение возникло из "
        "ненадлежащей организации восстановительного ремонта. Решающая норма лежит вне "
        "ГК РФ, и ни один институт пакета её не моделирует. Статьи 421, 432, 927 и 929 "
        "суд привёл как общее основание, а не как основание отказа."
    ),
}


REAL_CASE_SCENARIOS: tuple[RealCaseScenario, ...] = (
    RealCaseScenario(
        case_id="vs-4-kg22-2-k1",
        case_number="4-КГ22-2-К1",
        institute="terms",
        court_holding_ru=(
            "Срок передачи объекта долевого строительства может быть определён "
            "комбинацией календарной даты и периода, отсчитываемого от получения "
            "разрешения на ввод дома в эксплуатацию. Такое условие закону не "
            "противоречит; квартира передана в пределах срока, нарушения нет."
        ),
        mapping_note_ru=(
            "Дело проверяет модель на ложное срабатывание: составной срок правомерен, "
            "и ни одно из правил исчисления сроков не нарушено. Предикат "
            "`term_asserted` установлен, поскольку спор шёл именно об исчислении срока; "
            "все предикаты нарушений — в False по прямому выводу суда."
        ),
        facts={
            "term_asserted": True,
            "term_definition_breached": False,
            "term_event_certainty_breached": False,
            "term_start_rules_breached": False,
            "term_end_rules_breached": False,
            "non_working_day_rule_breached": False,
            "limitation_term_calculation_breached": False,
            "performance_deadline_breached": False,
            "organisation_operating_hours_breached": False,
            "written_notice_dispatch_breached": False,
        },
        expected_conclusions={
            "terms_qualified": True,
            "term_calculation_defective": False,
            "term_event_certainty_duty_breached": False,
            "performance_deadline_duty_breached": False,
            "requires_human_terms_assessment": False,
        },
    ),
    RealCaseScenario(
        case_id="vs-18-kg17-121",
        case_number="18-КГ17-121",
        institute="limitation",
        court_holding_ru=(
            "При изъятии товара у покупателя третьим лицом срок исковой давности по "
            "требованию к продавцу о возмещении убытков исчисляется с момента "
            "вступления в законную силу решения суда об изъятии товара. Иск "
            "удовлетворён."
        ),
        mapping_note_ru=(
            "Начало течения срока суд отнёс к вступлению в силу решения об изъятии, "
            "и от этого момента трёхлетний срок не истёк — отсюда "
            "`general_three_year_term_elapsed = False`. Заявление о применении "
            "давности достроено: спор о начале течения срока предполагает, что "
            "возражение было сделано, иначе суду не пришлось бы определять этот "
            "момент. Достройка сделана в сторону, невыгодную модели: при заявленной "
            "давности модель обязана не признать её основанием к отказу."
        ),
        facts={
            "claim_subject_to_limitation": True,
            "right_violation_and_defendant_known": True,
            "fixed_performance_term_expired": False,
            "general_three_year_term_elapsed": False,
            "special_term_applies": False,
            "special_term_elapsed": False,
            "objective_ten_year_limit_exceeded": False,
            "suspension_ground_in_final_six_months": False,
            "debtor_acknowledged_debt": False,
            "judicial_protection_period_ongoing": False,
            "limitation_pleaded_by_party_before_judgment": True,
            "claimant_is_individual_with_valid_excuse": False,
            "is_additional_claim": False,
            "main_claim_time_barred": False,
        },
        expected_conclusions={
            "limitation_period_started": True,
            "limitation_period_expired": False,
            "limitation_defense_available": False,
            "claim_not_subject_to_limitation": False,
        },
    ),
    RealCaseScenario(
        case_id="vs-5-kg24-43-k2",
        case_number="5-КГ24-43-К2",
        institute="property_rights",
        court_holding_ru=(
            "При виндикации выморочного имущества у добросовестного приобретателя "
            "подлежат оценке действия публичного собственника по выявлению и "
            "оформлению имущества. Приобретатель полагался на данные ЕГРН и "
            "нотариальное свидетельство, приобрёл возмездно; в иске отказано."
        ),
        mapping_note_ru=(
            "Правовая суть отказа — защита добросовестного приобретателя по статье 302 "
            "ГК РФ была оставлена нижестоящими судами без оценки. Это и есть предикат "
            "`good_faith_purchaser_protection_disregarded`.\n\n"
            "Первый перевод оставлял `vindication_rules_breached` в False: я исходил из "
            "того, что суд не отверг виндикацию как ненадлежащий способ защиты. Модель "
            "отвергла такой набор фактов — её проверка согласованности требует, чтобы "
            "неучёт защиты приобретателя сопровождался нарушением правил об "
            "истребовании. Проверка права: имущество было истребовано у возмездного "
            "добросовестного приобретателя вопреки статье 302, то есть правила "
            "истребования нарушены. Ошибка была в переводе, а не в модели."
        ),
        facts={
            "property_right_asserted": True,
            "ownership_powers_breached": False,
            "disposal_by_non_owner_detected": True,
            "risk_and_burden_rules_breached": False,
            "acquisition_moment_rules_breached": False,
            "acquisitive_prescription_breached": False,
            "common_property_rules_breached": False,
            "vindication_rules_breached": True,
            "good_faith_purchaser_protection_disregarded": True,
            "negatory_or_possessor_claim_breached": False,
        },
        expected_conclusions={
            "property_rights_qualified": True,
            "good_faith_purchaser_breached": True,
            "unauthorized_disposal_detected": True,
            "vindication_duty_breached": True,
            "requires_human_property_rights_assessment": True,
        },
    ),
    RealCaseScenario(
        case_id="vs-310-es15-4563",
        case_number="310-ЭС15-4563",
        institute="freedom",
        court_holding_ru=(
            "Имущественные последствия расторжения договора лизинга могут быть "
            "урегулированы соглашением сторон в установленных законом пределах свободы "
            "договора. Условия дополнительного соглашения императивным нормам не "
            "противоречат, неосновательного обогащения нет; в иске отказано."
        ),
        mapping_note_ru=(
            "Суд прямо назвал соглашение сторон соответствующим императивным нормам — "
            "это `contract_conforms_mandatory_rules`. Заключение договора никем не "
            "понуждалось, условия последствий расторжения законом не предписаны: "
            "именно поэтому стороны были вправе установить их сами."
        ),
        facts={
            "contract_conclusion_compelled_by_law": False,
            "contract_type_unnamed": False,
            "mixed_contract_elements": False,
            "terms_prescribed_by_mandatory_norm": False,
            "contract_conforms_mandatory_rules": True,
            "new_mandatory_law_after_conclusion": False,
            "new_law_given_retroactive_effect": False,
            "contract_gratuitous_by_nature": False,
            "price_agreed_by_parties": True,
            "regulated_price_mandated": False,
            "comparable_price_available": False,
        },
        expected_conclusions={
            "contract_conclusion_free": True,
            "terms_by_party_discretion": True,
            "contract_valid_against_mandatory_rules": True,
            "contract_presumed_onerous": True,
            "price_determined": True,
            "requires_human_freedom_assessment": False,
        },
    ),
)


class RealCaseResult(BaseModel):
    case_id: str
    case_number: str
    institute: str
    passed: bool
    expected_conclusions: dict[str, bool]
    observed_conclusions: dict[str, bool]
    mismatched: list[str] = Field(default_factory=list)


class RealCaseReport(BaseModel):
    version: str = REAL_CASE_SUITE_VERSION
    total: int = 0
    passed: int = 0
    failed_case_ids: list[str] = Field(default_factory=list)
    results: list[RealCaseResult] = Field(default_factory=list)
    unmapped_final_cases: list[str] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


def _flip(evidence, updates: dict[str, bool]):
    """Подменить значения утверждений, не трогая состав предикатов."""
    unknown = updates.keys() - {assertion.predicate.value for assertion in evidence.assertions}
    if unknown:
        raise ValueError(f"Предикаты вне контракта данных: {sorted(unknown)}.")
    return evidence.model_copy(
        update={
            "assertions": tuple(
                assertion.model_copy(update={"value": updates[assertion.predicate.value]})
                if assertion.predicate.value in updates
                else assertion
                for assertion in evidence.assertions
            )
        }
    )


def run_real_case_scenario(scenario: RealCaseScenario):
    """Прогнать один институт по фактам реального дела."""
    runner = INSTITUTE_RUNNERS[scenario.institute]
    request = build_synthetic_supply_analysis_request()
    evidence = _flip(getattr(request, runner.evidence_field), scenario.facts)
    mapping = runner.map_evidence(evidence)
    return runner.evaluate(runner.build_constraints(mapping), mapping.facts)


def run_real_case_suite() -> RealCaseReport:
    """Сверить выводы институтов с решениями по реальным делам."""
    results: list[RealCaseResult] = []
    for scenario in REAL_CASE_SCENARIOS:
        evaluation = run_real_case_scenario(scenario)
        observed = {name: getattr(evaluation, name) for name in scenario.expected_conclusions}
        mismatched = sorted(
            name
            for name, expected in scenario.expected_conclusions.items()
            if observed[name] != expected
        )
        results.append(
            RealCaseResult(
                case_id=scenario.case_id,
                case_number=scenario.case_number,
                institute=scenario.institute,
                passed=not mismatched,
                expected_conclusions=scenario.expected_conclusions,
                observed_conclusions=observed,
                mismatched=mismatched,
            )
        )
    passed = sum(entry.passed for entry in results)
    return RealCaseReport(
        total=len(results),
        passed=passed,
        failed_case_ids=[entry.case_id for entry in results if not entry.passed],
        results=results,
        unmapped_final_cases=sorted(UNMAPPED_FINAL_CASES_RU),
        notes_ru=[
            "Ожидаемый итог взят из решения по конкретному делу, а не из текста закона "
            "в моём прочтении и не из разъяснения Пленума.",
            "Проверяется вывод одного института: дело даёт факты для него, а не для "
            "всего конвейера.",
            "Перевод фабулы в предикаты — интерпретация; там, где предикат выведен не "
            "буквально, рассуждение записано в mapping_note_ru.",
            *(
                f"Не переведено — {case_id}: {reason}"
                for case_id, reason in sorted(UNMAPPED_FINAL_CASES_RU.items())
            ),
        ],
    )
