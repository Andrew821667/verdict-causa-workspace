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

import importlib
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)

REAL_CASE_SUITE_VERSION = "contracts-real-case-scenarios-v0"


class InstituteRunner(BaseModel):
    """Как запустить один институт по подменённым фактам."""

    model_config = {"arbitrary_types_allowed": True}

    evidence_field: str
    map_evidence: Callable[[Any], Any]
    build_constraints: Callable[[Any], Any]
    evaluate: Callable[[Any, Any], Any]


#: Институты, у которых нет стандартной тройки функций, и почему.
#:
#: `case` и `temporal` — не институты кодекса, а служебные блоки запроса:
#: описание дела и его временные рамки. Прогонять по ним решение суда не по
#: чему.
RUNNERLESS_EVIDENCE_RU: dict[str, str] = {
    "case_evidence": "описание дела, а не институт кодекса",
    "temporal_evidence": "временные рамки анализа, а не институт кодекса",
}


def _build_runner(institute: str) -> InstituteRunner:
    """Собрать раннер по стандартным именам института.

    Раннеры перечислялись вручную, и в наборе их было четыре. Из-за этого
    непереводимым считалось любое дело за пределами четырёх институтов — хотя
    смоделировано их больше восьмидесяти. Ограничение было не правовым, а
    списочным, и здесь оно снято: раннер есть у каждого института, который
    выставляет тройку «отобразить доказательства — построить ограничения —
    вычислить вывод».
    """
    module = importlib.import_module(f"causa.institutional.contracts.{institute}")
    return InstituteRunner(
        evidence_field=f"{institute}_evidence",
        map_evidence=getattr(module, f"map_reviewed_{institute}_evidence"),
        build_constraints=getattr(module, f"build_{institute}_constraint_set"),
        evaluate=getattr(module, f"evaluate_{institute}_constraints"),
    )


def _discover_runners() -> dict[str, InstituteRunner]:
    """Найти институты, по фактам которых можно прогнать реальное дело."""
    request_fields = type(build_synthetic_supply_analysis_request()).model_fields
    runners: dict[str, InstituteRunner] = {}
    for field in request_fields:
        if not field.endswith("_evidence") or field in RUNNERLESS_EVIDENCE_RU:
            continue
        runners[field[: -len("_evidence")]] = _build_runner(field[: -len("_evidence")])
    return runners


INSTITUTE_RUNNERS: dict[str, InstituteRunner] = _discover_runners()


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


#: Дела с окончательным исходом, которые ещё не переведены в предикаты.
#:
#: Отличие от `UNMAPPED_FINAL_CASES_RU` принципиальное. Там — граница модели:
#: решающая норма лежит вне того, что смоделировано, и перевод невозможен.
#: Здесь — очередь работы: институт для дела есть и раннер у него есть, а
#: перевода фабулы в предикаты пока нет.
#:
#: Смешивать эти две причины нельзя. Общая запись «не переведено» превратила бы
#: проверку полноты набора в отметку о прочтении: набор рос бы только за счёт
#: дел, на которых модель сходится, а неудобные молча уходили бы в ту же графу,
#: что и дела вне модели.
#:
#: Значение — институты, в предикаты которых дело следует переводить. Пустым
#: этот список быть не может: дело без единого института с раннером — это
#: граница модели, и его место в `UNMAPPED_FINAL_CASES_RU` с написанной
#: причиной.
#:
#: Сейчас очередь пуста: все 42 дела, стоявшие в ней после второй выгрузки,
#: переведены. Словарь оставлен, а не удалён, — следующая выгрузка наполнит его
#: снова, и разделение трёх граф должно пережить пустоту.
PENDING_TRANSLATION_RU: dict[str, tuple[str, ...]] = {}


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
            "ownership_terminated_by_federal_law": False,
            "losses_from_statutory_termination_proven": False,
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
            "term_not_determined_by_parties": False,
            "term_not_covered_by_dispositive_norm": False,
            "standard_terms_asserted": False,
            "standard_terms_published_for_contract_type": False,
            "contract_refers_to_standard_terms": False,
            "standard_terms_meet_custom_requirements": False,
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
    RealCaseScenario(
        case_id="88-26046-2023-cass-ksoj002-125208",
        case_number="88-26046/2023",
        institute="invalidity",
        court_holding_ru=(
            "Сделка, совершённая гражданином, признанным недееспособным вследствие психического "
            "расстройства, ничтожна по пункту 1 статьи 171 ГК РФ. Последствия недействительности "
            "применены, уплаченные по договорам об оказании юридических услуг деньги взысканы с "
            "общества в пользу подопечной."
        ),
        mapping_note_ru=(
            "Иск подан опекуном, а не самой стороной сделки, поэтому "
            "`claimant_is_transaction_party` — False, а `claimant_legally_authorized` — True: "
            "модель различает эти два основания стоять в споре. Решение о признании недееспособной "
            "вынесено до договоров, поэтому `court_decision_entered_into_force` — True. "
            "Юридические услуги в натуре не возвращаются, отсюда `return_in_kind_possible` — "
            "False, и реституция ожидается денежной. Отказ в компенсации морального вреда "
            "институтом недействительности не разбирается: `additional_damages_claimed` оставлен "
            "False, так как это требование лежит в модели морального вреда, а не здесь."
        ),
        facts={
            "transaction_concluded": True,
            "invalidity_claim_made": True,
            "claimant_is_transaction_party": False,
            "claimant_legally_authorized": True,
            "claimant_rights_or_interests_affected": True,
            "court_decision_entered_into_force": True,
            "nullity_consequences_requested": True,
            "nullity_legal_interest_proven": True,
            "good_faith_reliance_created": False,
            "party_confirmed_voidable_transaction": False,
            "ground_known_at_confirmation": False,
            "performance_accepted_under_entrepreneurial_contract": False,
            "claimant_did_not_reciprocate_performance": False,
            "claimant_knew_ground_at_performance_acceptance": False,
            "performance_violates_third_party_or_public_interests": False,
            "violates_law": False,
            "public_interests_or_third_rights_affected": False,
            "law_expressly_makes_void": False,
            "immoral_purpose_proven": False,
            "both_parties_intentional_immoral_purpose": False,
            "sham_intent_proven": False,
            "feigned_intent_proven": False,
            "disguised_transaction_identified": False,
            "incapacitated_person_transaction": True,
            "minor_under_14_transaction": False,
            "benefit_to_incapacitated_or_minor_proven": False,
            "required_consent_absent": False,
            "counterparty_knew_consent_absent": False,
            "authority_restriction_violated": False,
            "counterparty_knew_authority_restriction": False,
            "entity_beyond_statutory_purpose": False,
            "counterparty_knew_beyond_purpose": False,
            "obvious_entity_damage_proven": False,
            "counterparty_knew_obvious_damage": False,
            "material_mistake_proven": False,
            "mistake_risk_assumed": False,
            "deception_proven": False,
            "violence_or_threat_proven": False,
            "adverse_circumstances_proven": False,
            "extremely_unfavorable_terms_proven": False,
            "counterparty_exploited_circumstances": False,
            "unable_to_understand_actions_proven": False,
            "limited_capacity_without_consent": False,
            "minor_14_18_without_consent": False,
            "execution_started": True,
            "void_limitation_period_expired": False,
            "voidable_limitation_period_expired": False,
            "invalid_part_separable": False,
            "remainder_preserves_transaction_purpose": False,
            "party_a_performed": True,
            "party_b_performed": True,
            "return_in_kind_possible": False,
            "value_of_performance_proven": True,
            "additional_damages_claimed": False,
            "additional_damages_causally_linked": False,
            "statutory_disposal_prohibition_violated": False,
            "judicial_disposal_prohibition_violated": False,
            "acquirer_knew_of_disposal_prohibition": False,
        },
        expected_conclusions={
            "capacity_void_ground": True,
            "void_ground_detected": True,
            "contractual_effect_displaced": True,
            "entire_transaction_affected": True,
            "restitution_required": True,
            "restitution_in_kind": False,
            "monetary_restitution_issue": True,
            "nullity_consequences_prerequisites": True,
            "transaction_presumed_effective": False,
        },
    ),
    RealCaseScenario(
        case_id="a45-3827-2019-cass-azs-208498",
        case_number="А45-3827/2019",
        institute="civil_principles",
        court_holding_ru=(
            "Требование аффилированного кредитора к должнику-банкроту не включено в реестр: суды "
            "применили повышенный стандарт доказывания, сочли реальность договоров недоказанной и "
            "установили признаки злоупотребления правом по статье 10 ГК РФ — наращивание фиктивной "
            "задолженности в ущерб независимым кредиторам."
        ),
        mapping_note_ru=(
            "Дело проверяет связку «злоупотребление установлено — в защите отказано». "
            "`abuse_of_right_established` — True по прямому выводу судов. "
            "`protection_refusal_not_applied` — False, потому что отказ в защите как раз применён: "
            "во включении требования отказано. Предикат сформулирован от обратного, и здесь легко "
            "ошибиться знаком. Повышенный стандарт доказывания — процессуальный институт, в "
            "предикаты он не переводится; в модель попадает его материальный результат: "
            "недобросовестность и злоупотребление."
        ),
        facts={
            "civil_rights_exercise_asserted": True,
            "good_faith_principle_breached": True,
            "equality_or_freedom_principle_breached": False,
            "rights_arising_grounds_breached": False,
            "abuse_of_right_established": True,
            "protection_refusal_not_applied": False,
            "protection_methods_breached": False,
            "self_help_limits_breached": False,
            "damages_compensation_rules_breached": False,
            "public_authority_liability_breached": False,
        },
        expected_conclusions={
            "civil_principles_qualified": True,
            "abuse_of_right_detected": True,
            "good_faith_duty_breached": True,
            "protection_refusal_breached": False,
        },
    ),
    RealCaseScenario(
        case_id="a79-1019-2023-cass-avv-122293",
        case_number="А79-1019/2023",
        institute="property_rights",
        court_holding_ru=(
            "В виндикационном иске отказано: истец не доказал право собственности на спорное "
            "сооружение. Договор купли-продажи, на котором основано требование, признан "
            "сфальсифицированным, его копии исключены из доказательств, иных оснований "
            "возникновения права не представлено."
        ),
        mapping_note_ru=(
            "Дело проверяет модель на ложное срабатывание. Виндикация заявлена, поэтому "
            "`property_right_asserted` — True, но ни одно правило вещной модели не нарушено: суд "
            "не устанавливал ни отчуждения неуправомоченным лицом, ни нарушения правил виндикации "
            "— он отказал по недоказанности права истца. Недоказанность права собственности не "
            "имеет отдельного предиката: она проявляется в том, что все предикаты нарушений "
            "остаются False, и ни одна обязанность не признаётся нарушенной."
        ),
        facts={
            "property_right_asserted": True,
            "ownership_powers_breached": False,
            "disposal_by_non_owner_detected": False,
            "risk_and_burden_rules_breached": False,
            "acquisition_moment_rules_breached": False,
            "acquisitive_prescription_breached": False,
            "common_property_rules_breached": False,
            "vindication_rules_breached": False,
            "good_faith_purchaser_protection_disregarded": False,
            "negatory_or_possessor_claim_breached": False,
            "ownership_terminated_by_federal_law": False,
            "losses_from_statutory_termination_proven": False,
        },
        expected_conclusions={
            "property_rights_qualified": True,
            "vindication_duty_breached": False,
            "unauthorized_disposal_detected": False,
            "good_faith_purchaser_breached": False,
            "requires_human_property_rights_assessment": False,
        },
    ),
    RealCaseScenario(
        case_id="a37-976-2025-cass-adv-143227",
        case_number="А37-976/2025",
        institute="formation",
        court_holding_ru=(
            "В иске отказано: проект договора на обслуживание программных продуктов не подписан, "
            "акцепт оферты и согласование существенных условий не доказаны, конклюдентных действий "
            "не совершено. Акт сверки первичным документом не является и задолженность не "
            "подтверждает."
        ),
        mapping_note_ru=(
            "`proposal_addressed_to_counterparty` — False, потому что суд установил: направление "
            "оферты уполномоченным лицом не доказано, скриншоты из 1С этого не подтверждают. "
            "Молчание ответчика на акты и счета переведено как `silence_only` — True при "
            "отсутствии основания считать молчание акцептом. Подписанный акт сверки не переводится "
            "в `performance_accepted_without_objection`: суд прямо сказал, что он не подтверждает "
            "ни исполнения, ни задолженности."
        ),
        facts={
            "proposal_made": True,
            "proposal_addressed_to_counterparty": False,
            "intent_to_be_bound": True,
            "subject_matter_defined_in_offer": True,
            "statutory_essential_terms_defined_in_offer": False,
            "party_declared_essential_terms_defined_in_offer": False,
            "required_form_observed": False,
            "acceptance_received": False,
            "acceptance_full_and_unconditional": False,
            "acceptance_within_period": False,
            "acceptance_by_conduct": False,
            "performance_conduct_started_in_time": False,
            "silence_only": True,
            "silence_acceptance_basis_exists": False,
            "acceptance_on_other_terms": False,
            "performance_accepted_without_objection": False,
            "bad_faith_non_conclusion_objection": False,
        },
        expected_conclusions={
            "valid_offer": False,
            "essential_terms_agreed": False,
            "express_acceptance_valid": False,
            "conduct_acceptance_valid": False,
            "silence_acceptance_valid": False,
            "contract_concluded_prerequisites": False,
            "formation_evidence_gap": True,
            "non_conclusion_objection_barred": False,
        },
    ),
    RealCaseScenario(
        case_id="a51-8801-2025-cass-adv-143320",
        case_number="А51-8801/2025",
        institute="formation",
        court_holding_ru=(
            "В иске о возврате оплаты отказано. Оплата выставленного счёта подтверждает "
            "согласование существенных условий договора подряда; конструкции изготовлены, переданы "
            "и установлены. По пункту 3 статьи 432 ГК РФ сторона, принявшая исполнение, не вправе "
            "недобросовестно ссылаться на незаключённость договора."
        ),
        mapping_note_ru=(
            "`required_form_observed` — True, хотя единого письменного документа стороны не "
            "подписывали: письменная оферта (счёт) акцептована оплатой, и по пункту 3 статьи 434 "
            "во взаимосвязи с пунктом 3 статьи 438 ГК РФ письменная форма считается соблюдённой. "
            "Это правило модель не выводит сама — предикат формы она принимает на вход, поэтому "
            "вывод сделан здесь и записан явно. Если поставить False, модель разойдётся с судом по "
            "`contract_concluded_prerequisites`, и разошлась бы из-за перевода, а не из-за "
            "правила."
        ),
        facts={
            "proposal_made": True,
            "proposal_addressed_to_counterparty": True,
            "intent_to_be_bound": True,
            "subject_matter_defined_in_offer": True,
            "statutory_essential_terms_defined_in_offer": True,
            "party_declared_essential_terms_defined_in_offer": True,
            "required_form_observed": True,
            "acceptance_received": True,
            "acceptance_full_and_unconditional": True,
            "acceptance_within_period": True,
            "acceptance_by_conduct": True,
            "performance_conduct_started_in_time": True,
            "silence_only": False,
            "silence_acceptance_basis_exists": False,
            "acceptance_on_other_terms": False,
            "performance_accepted_without_objection": True,
            "bad_faith_non_conclusion_objection": True,
        },
        expected_conclusions={
            "valid_offer": True,
            "essential_terms_agreed": True,
            "conduct_acceptance_valid": True,
            "contract_concluded_prerequisites": True,
            "non_conclusion_objection_barred": True,
            "formation_evidence_gap": False,
        },
    ),
    RealCaseScenario(
        case_id="a67-8637-2022-cass-azs-203400",
        case_number="А67-8637/2022",
        institute="formation",
        court_holding_ru=(
            "В иске отказано: спецификация №2 сторонами не подписана, поэтому обязательство "
            "поставить товар на всю заявленную сумму не возникло. Частичная оплата и выборка "
            "товара подтверждают обменную сделку лишь в пределах состоявшихся предоставлений, а не "
            "заключение договора на всю сумму спецификации."
        ),
        mapping_note_ru=(
            "Дело разграничивает предложение и договор. Спецификация со счётом — полноценная "
            "оферта, поэтому `valid_offer` ожидается True. Но акцептом её никто не принял: "
            "частичная оплата относится к состоявшемуся обмену, а не к оферте целиком, поэтому "
            "`acceptance_by_conduct` — False. Соблазн поставить его True велик — деньги-то "
            "перечислены, — и именно этот шаг суд и отверг: исполнение в пределах полученного не "
            "превращается в акцепт всей оферты."
        ),
        facts={
            "proposal_made": True,
            "proposal_addressed_to_counterparty": True,
            "intent_to_be_bound": True,
            "subject_matter_defined_in_offer": True,
            "statutory_essential_terms_defined_in_offer": True,
            "party_declared_essential_terms_defined_in_offer": True,
            "required_form_observed": False,
            "acceptance_received": False,
            "acceptance_full_and_unconditional": False,
            "acceptance_within_period": False,
            "acceptance_by_conduct": False,
            "performance_conduct_started_in_time": False,
            "silence_only": False,
            "silence_acceptance_basis_exists": False,
            "acceptance_on_other_terms": False,
            "performance_accepted_without_objection": False,
            "bad_faith_non_conclusion_objection": False,
        },
        expected_conclusions={
            "valid_offer": True,
            "essential_terms_agreed": False,
            "conduct_acceptance_valid": False,
            "contract_concluded_prerequisites": False,
            "formation_evidence_gap": True,
            "non_conclusion_objection_barred": False,
        },
    ),
    RealCaseScenario(
        case_id="a51-10070-2023-cass-adv-136103",
        case_number="А51-10070/2023",
        institute="limitation",
        court_holding_ru=(
            "В иске о признании договора поставки недействительным как крупной сделки отказано. "
            "Сделка совершена в обычной хозяйственной деятельности, ущерб не доказан, а годичный "
            "срок исковой давности по оспоримой сделке пропущен, что является самостоятельным "
            "основанием для отказа (абзац второй пункта 2 статьи 199 ГК РФ)."
        ),
        mapping_note_ru=(
            "Оспаривание крупной сделки идёт по годичному сроку пункта 2 статьи 181 ГК РФ, поэтому "
            "`special_term_applies` и `special_term_elapsed` — True, а общий трёхлетний срок в "
            "предикатах не отмечается. Ответчик заявил о давности до решения — "
            "`limitation_pleaded_by_party_before_judgment` True: без этого заявления суд давность "
            "не применяет. Истец — юридическое лицо, поэтому восстановление срока исключено."
        ),
        facts={
            "claim_subject_to_limitation": True,
            "right_violation_and_defendant_known": True,
            "fixed_performance_term_expired": False,
            "general_three_year_term_elapsed": False,
            "special_term_applies": True,
            "special_term_elapsed": True,
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
            "limitation_period_expired": True,
            "limitation_defense_available": True,
            "limitation_restorable": False,
            "objective_limit_barred": False,
            "claim_not_subject_to_limitation": False,
        },
    ),
    RealCaseScenario(
        case_id="a67-10172-2021-cass-azs-212429",
        case_number="А67-10172/2021",
        institute="limitation",
        court_holding_ru=(
            "Во включении в реестр требований на 1 748 737,59 руб. отказано в связи с пропуском "
            "срока исковой давности, о применении которой заявил конкурсный управляющий. Остальная "
            "часть требования признана обоснованной, но понижена в очерёдности как компенсационное "
            "финансирование аффилированным лицом."
        ),
        mapping_note_ru=(
            "Проверяется отказная часть: товар передан по счетам-фактурам 2017 года, заявление "
            "подано 28.11.2023, поэтому общий трёхлетний срок истёк — "
            "`general_three_year_term_elapsed` True. Понижение очерёдности за компенсационное "
            "финансирование институтом давности не разбирается: это субординация требований по "
            "законодательству о банкротстве, и в предикаты она не переводится. Заявление сделал "
            "конкурсный управляющий — сторона спора, поэтому предикат заявления о давности "
            "установлен."
        ),
        facts={
            "claim_subject_to_limitation": True,
            "right_violation_and_defendant_known": True,
            "fixed_performance_term_expired": True,
            "general_three_year_term_elapsed": True,
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
            "basic_term_elapsed": True,
            "limitation_period_expired": True,
            "limitation_defense_available": True,
            "limitation_reset_by_acknowledgement": False,
            "limitation_suspended": False,
        },
    ),
    RealCaseScenario(
        case_id="88-10752-2023-cass-ksoj002-108217",
        case_number="88-10752/2023",
        institute="representation",
        court_holding_ru=(
            "Договор купли-продажи автомобиля заключён от имени общества гражданином без "
            "полномочий: доверенность не выдавалась, последующего одобрения не было. По пункту 1 "
            "статьи 183 ГК РФ такая сделка не влечёт правовых последствий для представляемого. В "
            "иске о признании её недействительной отказано: истец избрал ненадлежащий способ "
            "защиты."
        ),
        mapping_note_ru=(
            "Порок основания полномочий и отсутствие одобрения — два разных предиката, и здесь "
            "установлены оба: доверенность не выдавалась вовсе (`authority_basis_invalid`), а "
            "одобрения не последовало (`unauthorized_act_without_ratification`). Отказ в иске по "
            "мотиву ненадлежащего способа защиты институтом представительства не разбирается: "
            "выбор способа защиты — процессуальный вопрос, и предиката для него нет. Модель "
            "отвечает на вопрос «связан ли представляемый», а не «тем ли иском истец пошёл»."
        ),
        facts={
            "representation_relation_established": True,
            "authority_basis_invalid": True,
            "prohibited_self_dealing": False,
            "commercial_representation_rules_breached": False,
            "power_of_attorney_form_breached": False,
            "power_of_attorney_term_breached": False,
            "substitution_rules_breached": False,
            "termination_or_notice_breached": False,
            "unauthorized_act_without_ratification": True,
            "ratification_effect_disregarded": False,
        },
        expected_conclusions={
            "representation_qualified": True,
            "authority_basis_duty_breached": True,
            "unauthorized_representation_detected": True,
            "ratification_effect_breached": False,
        },
    ),
    RealCaseScenario(
        case_id="88-4580-2026-cass-ksoj008-184804",
        case_number="88-4580/2026",
        institute="representation",
        court_holding_ru=(
            "Доверенность уполномочивала представителя на покупку квартиры и передачу её в залог, "
            "но не давала права заключать договоры займа и получать деньги. Представляемая сделку "
            "не одобрила. По пунктам 1 и 2 статьи 183 ГК РФ договор считается заключённым от имени "
            "самого представителя, поэтому и во взыскании с представляемой, и в признании договора "
            "недействительным по её иску отказано."
        ),
        mapping_note_ru=(
            "Пара к делу 88-10752/2023, разводящая два порока, которые легко слить в один. Там "
            "доверенности не было вовсе, здесь она есть и действительна — просто не покрывает "
            "заключённую сделку. Поэтому `authority_basis_invalid` — False, а "
            "`unauthorized_act_without_ratification` — True. Поставить оба в True означало бы "
            "объявить порочным само основание полномочий, которого суд не касался."
        ),
        facts={
            "representation_relation_established": True,
            "authority_basis_invalid": False,
            "prohibited_self_dealing": False,
            "commercial_representation_rules_breached": False,
            "power_of_attorney_form_breached": False,
            "power_of_attorney_term_breached": False,
            "substitution_rules_breached": False,
            "termination_or_notice_breached": False,
            "unauthorized_act_without_ratification": True,
            "ratification_effect_disregarded": False,
        },
        expected_conclusions={
            "representation_qualified": True,
            "authority_basis_duty_breached": False,
            "unauthorized_representation_detected": True,
            "ratification_effect_breached": False,
        },
    ),
    RealCaseScenario(
        case_id="88-11827-2023-cass-ksoj007-89604",
        case_number="88-11827/2023",
        institute="representation",
        court_holding_ru=(
            "Договор возмездного оказания услуг заключён от имени товарищества бывшим "
            "председателем без решения правления, но впоследствии общее собрание членов "
            "товарищества одобрило все действия по строительству газопровода, включая этот "
            "договор. По пункту 2 статьи 183 ГК РФ последующее одобрение устраняет порок "
            "отсутствия полномочий, и услуги подлежат оплате."
        ),
        mapping_note_ru=(
            "Третье дело этой тройки: полномочий не было, но одобрение состоялось. "
            "`authority_basis_invalid` — True, как и в деле 88-10752/2023, а "
            "`unauthorized_act_without_ratification` — False, потому что предикат спрашивает о "
            "действии без одобрения, а не о действии без полномочий. Смена председателя правления "
            "в предикаты не переводится: суд прямо сказал, что она значения не имеет."
        ),
        facts={
            "representation_relation_established": True,
            "authority_basis_invalid": True,
            "prohibited_self_dealing": False,
            "commercial_representation_rules_breached": False,
            "power_of_attorney_form_breached": False,
            "power_of_attorney_term_breached": False,
            "substitution_rules_breached": False,
            "termination_or_notice_breached": False,
            "unauthorized_act_without_ratification": False,
            "ratification_effect_disregarded": False,
        },
        expected_conclusions={
            "representation_qualified": True,
            "authority_basis_duty_breached": True,
            "unauthorized_representation_detected": False,
            "ratification_effect_breached": False,
        },
    ),
    RealCaseScenario(
        case_id="88-11704-2025-cass-ksoj008-167443",
        case_number="88-11704/2025",
        institute="meeting_decisions",
        court_holding_ru=(
            "Общее собрание собственников проведено, но решение об установлении размера платы за "
            "содержание жилья на новый период не принято. При отсутствии такого решения размер "
            "платы определяется по тарифу органа местного самоуправления, поэтому в иске к "
            "управляющей организации отказано."
        ),
        mapping_note_ru=(
            "Непринятое решение и ничтожное решение — разные исходы, и модель их различает. Здесь "
            "собрание состоялось и кворум был, но большинства решение не набрало: `quorum_present` "
            "— True, `required_majority_obtained` — False. Условие договора управления о размере "
            "платы держится на решении собрания, поэтому "
            "`meeting_decision_underpins_contract_term` — True, и модель обязана вывести, что у "
            "условия не осталось основания."
        ),
        facts={
            "meeting_decision_asserted": True,
            "meeting_decision_underpins_contract_term": True,
            "quorum_present": True,
            "required_majority_obtained": False,
            "all_participants_took_part": False,
            "question_outside_agenda": False,
            "question_outside_competence": False,
            "contrary_to_public_order_or_morality": False,
            "convocation_or_conduct_procedure_breached": False,
            "participant_equality_breached": False,
            "representative_authority_defect": False,
            "minutes_requirements_breached": False,
            "vote_could_not_affect_outcome": False,
            "no_material_adverse_consequences": False,
            "decision_confirmed_by_later_decision": False,
        },
        expected_conclusions={
            "decision_not_adopted": True,
            "decision_void": False,
            "decision_voidable": False,
            "contract_term_lacks_meeting_basis": True,
            "contract_term_binds_all_participants": False,
            "decision_binds_all_participants": False,
        },
    ),
    RealCaseScenario(
        case_id="88-15461-2025-cass-ksoj003-151203",
        case_number="88-15461/2025",
        institute="meeting_decisions",
        court_holding_ru=(
            "Тарифы на содержание общего имущества установлены решением конференции жилищно- "
            "строительного кооператива, кворум которой не доказан. По пункту 2 статьи 181.5 ГК РФ "
            "решение, принятое при отсутствии необходимого кворума, ничтожно, поэтому действия "
            "управляющей организации по начислению платы по этим тарифам признаны незаконными."
        ),
        mapping_note_ru=(
            "Третий из трёх исходов, которые легко спутать: решение принято, но ничтожно. "
            "`required_majority_obtained` — True (решение оформлено и голоса собраны), а "
            "`quorum_present` — False, и ничтожность выводится именно из кворума, а не из "
            "содержания решения. Отказ в остальной части требований — процессуальный результат, в "
            "предикаты он не переводится."
        ),
        facts={
            "meeting_decision_asserted": True,
            "meeting_decision_underpins_contract_term": True,
            "quorum_present": False,
            "required_majority_obtained": True,
            "all_participants_took_part": False,
            "question_outside_agenda": False,
            "question_outside_competence": False,
            "contrary_to_public_order_or_morality": False,
            "convocation_or_conduct_procedure_breached": False,
            "participant_equality_breached": False,
            "representative_authority_defect": False,
            "minutes_requirements_breached": False,
            "vote_could_not_affect_outcome": False,
            "no_material_adverse_consequences": False,
            "decision_confirmed_by_later_decision": False,
        },
        expected_conclusions={
            "quorum_absent": True,
            "decision_void": True,
            "decision_not_adopted": False,
            "contract_term_lacks_meeting_basis": True,
            "decision_binds_all_participants": False,
        },
    ),
    RealCaseScenario(
        case_id="88-12844-2024-cass-ksoj001-173181",
        case_number="88-12844/2024",
        institute="meeting_decisions",
        court_holding_ru=(
            "Размер платы за содержание общего имущества установлен решением общего собрания "
            "собственников. Управляющая организация не вправе изменять его в одностороннем порядке "
            "и обязана применять тариф собрания, пока решение не оспорено. Начисление по иному "
            "тарифу признано незаконным, назначен перерасчёт."
        ),
        mapping_note_ru=(
            "Основание всей группы дел об управлении домом: решение принято при кворуме и "
            "большинством, пороков процедуры не установлено, поэтому оно обязательно для всех и "
            "связывает условие договора управления. Предикаты пороков оставлены в False по прямому "
            "выводу суда, а не по умолчанию: решение не оспаривалось и недействительным не "
            "признавалось."
        ),
        facts={
            "meeting_decision_asserted": True,
            "meeting_decision_underpins_contract_term": True,
            "quorum_present": True,
            "required_majority_obtained": True,
            "all_participants_took_part": False,
            "question_outside_agenda": False,
            "question_outside_competence": False,
            "contrary_to_public_order_or_morality": False,
            "convocation_or_conduct_procedure_breached": False,
            "participant_equality_breached": False,
            "representative_authority_defect": False,
            "minutes_requirements_breached": False,
            "vote_could_not_affect_outcome": False,
            "no_material_adverse_consequences": False,
            "decision_confirmed_by_later_decision": False,
        },
        expected_conclusions={
            "decision_void": False,
            "decision_voidable": False,
            "decision_not_adopted": False,
            "decision_binds_all_participants": True,
            "contract_term_binds_all_participants": True,
            "contract_term_lacks_meeting_basis": False,
            "requires_human_meeting_decision_assessment": False,
        },
    ),
    RealCaseScenario(
        case_id="88-16698-2026-cass-ksoj001-256023",
        case_number="88-16698/2026",
        institute="meeting_decisions",
        court_holding_ru=(
            "Тариф утверждён решениями внеочередных общих собраний собственников, которые не "
            "оспорены и недействительными не признаны. Управляющая компания обязана была применять "
            "этот тариф, а не тариф органа местного самоуправления; во взыскании задолженности по "
            "завышенному тарифу отказано, встречный иск собственника удовлетворён частично."
        ),
        mapping_note_ru=(
            "Дело повторяет конфигурацию предикатов дела 88-12844/2024: действительное решение "
            "собрания связывает условие договора управления. Совпадение записано намеренно — это "
            "свойство корпуса, а не оплошность перевода: пять дел выгрузки об управлении домом "
            "сводятся к трём различным наборам фактов. Собственная добавка этого дела — прямая "
            "констатация суда, что решения не оспорены, — подтверждает, что предикаты пороков "
            "стоят в False по установленному обстоятельству."
        ),
        facts={
            "meeting_decision_asserted": True,
            "meeting_decision_underpins_contract_term": True,
            "quorum_present": True,
            "required_majority_obtained": True,
            "all_participants_took_part": False,
            "question_outside_agenda": False,
            "question_outside_competence": False,
            "contrary_to_public_order_or_morality": False,
            "convocation_or_conduct_procedure_breached": False,
            "participant_equality_breached": False,
            "representative_authority_defect": False,
            "minutes_requirements_breached": False,
            "vote_could_not_affect_outcome": False,
            "no_material_adverse_consequences": False,
            "decision_confirmed_by_later_decision": False,
        },
        expected_conclusions={
            "decision_void": False,
            "decision_voidable": False,
            "decision_not_adopted": False,
            "decision_binds_all_participants": True,
            "contract_term_binds_all_participants": True,
            "contract_term_lacks_meeting_basis": False,
        },
    ),
    RealCaseScenario(
        case_id="88-19251-2024-cass-ksoj008-144573",
        case_number="88-19251/2024",
        institute="meeting_decisions",
        court_holding_ru=(
            "Плата за содержание и текущий ремонт взыскана по тарифам, установленным решениями "
            "общих собраний собственников. Из расчёта исключена фактически не оказанная услуга "
            "вахты, а коэффициент приведения не применён, поскольку решениями собраний в спорный "
            "период он предусмотрен не был."
        ),
        mapping_note_ru=(
            "Та же конфигурация, что и в делах 88-12844/2024 и 88-16698/2026. Дело показывает "
            "вторую сторону обязательности решения: оно не только связывает управляющую "
            "организацию, но и ограничивает её тем, что в нём записано, — исключение услуги вахты "
            "и отказ применить коэффициент выведены из объёма решения. Отдельного предиката для "
            "объёма решения в модели нет, и это её граница, а не вывод по делу."
        ),
        facts={
            "meeting_decision_asserted": True,
            "meeting_decision_underpins_contract_term": True,
            "quorum_present": True,
            "required_majority_obtained": True,
            "all_participants_took_part": False,
            "question_outside_agenda": False,
            "question_outside_competence": False,
            "contrary_to_public_order_or_morality": False,
            "convocation_or_conduct_procedure_breached": False,
            "participant_equality_breached": False,
            "representative_authority_defect": False,
            "minutes_requirements_breached": False,
            "vote_could_not_affect_outcome": False,
            "no_material_adverse_consequences": False,
            "decision_confirmed_by_later_decision": False,
        },
        expected_conclusions={
            "decision_void": False,
            "decision_not_adopted": False,
            "decision_binds_all_participants": True,
            "contract_term_binds_all_participants": True,
            "contract_term_lacks_meeting_basis": False,
        },
    ),
    RealCaseScenario(
        case_id="88-12081-2024-cass-ksoj007-119496",
        case_number="88-12081/2024",
        institute="invalidity",
        court_holding_ru=(
            "Кредитный договор заключён гражданином, впоследствии признанным недееспособным "
            "вследствие психического расстройства. По пункту 1 статьи 171 ГК РФ сделка ничтожна; "
            "применены последствия недействительности, с гражданина взыскано фактически полученное "
            "по договору за вычетом произведённых им платежей."
        ),
        mapping_note_ru=(
            "Пара к делу 88-26046/2023, разводящая две формы реституции. Там предметом были "
            "юридические услуги, вернуть которые в натуре нельзя, и реституция вышла денежной. "
            "Здесь предмет — деньги, вещь родовая, и возврат в натуре возможен: "
            "`return_in_kind_possible` — True. Контракт данных этого не терпит вместе с "
            "`value_of_performance_proven`: денежная оценка требуется лишь тогда, когда "
            "натурального возврата нет, и попытка объявить оба факта разом была отклонена "
            "проверкой согласованности."
        ),
        facts={
            "transaction_concluded": True,
            "invalidity_claim_made": True,
            "claimant_is_transaction_party": False,
            "claimant_legally_authorized": True,
            "claimant_rights_or_interests_affected": True,
            "court_decision_entered_into_force": True,
            "nullity_consequences_requested": True,
            "nullity_legal_interest_proven": True,
            "good_faith_reliance_created": False,
            "party_confirmed_voidable_transaction": False,
            "ground_known_at_confirmation": False,
            "performance_accepted_under_entrepreneurial_contract": False,
            "claimant_did_not_reciprocate_performance": False,
            "claimant_knew_ground_at_performance_acceptance": False,
            "performance_violates_third_party_or_public_interests": False,
            "violates_law": False,
            "public_interests_or_third_rights_affected": False,
            "law_expressly_makes_void": False,
            "immoral_purpose_proven": False,
            "both_parties_intentional_immoral_purpose": False,
            "sham_intent_proven": False,
            "feigned_intent_proven": False,
            "disguised_transaction_identified": False,
            "incapacitated_person_transaction": True,
            "minor_under_14_transaction": False,
            "benefit_to_incapacitated_or_minor_proven": False,
            "required_consent_absent": False,
            "counterparty_knew_consent_absent": False,
            "authority_restriction_violated": False,
            "counterparty_knew_authority_restriction": False,
            "entity_beyond_statutory_purpose": False,
            "counterparty_knew_beyond_purpose": False,
            "obvious_entity_damage_proven": False,
            "counterparty_knew_obvious_damage": False,
            "material_mistake_proven": False,
            "mistake_risk_assumed": False,
            "deception_proven": False,
            "violence_or_threat_proven": False,
            "adverse_circumstances_proven": False,
            "extremely_unfavorable_terms_proven": False,
            "counterparty_exploited_circumstances": False,
            "unable_to_understand_actions_proven": False,
            "limited_capacity_without_consent": False,
            "minor_14_18_without_consent": False,
            "execution_started": True,
            "void_limitation_period_expired": False,
            "voidable_limitation_period_expired": False,
            "invalid_part_separable": False,
            "remainder_preserves_transaction_purpose": False,
            "party_a_performed": True,
            "party_b_performed": True,
            "return_in_kind_possible": True,
            "value_of_performance_proven": False,
            "additional_damages_claimed": False,
            "additional_damages_causally_linked": False,
            "statutory_disposal_prohibition_violated": False,
            "judicial_disposal_prohibition_violated": False,
            "acquirer_knew_of_disposal_prohibition": False,
        },
        expected_conclusions={
            "capacity_void_ground": True,
            "void_ground_detected": True,
            "contractual_effect_displaced": True,
            "restitution_required": True,
            "restitution_in_kind": True,
            "monetary_restitution_issue": False,
            "nullity_consequences_prerequisites": True,
        },
    ),
    RealCaseScenario(
        case_id="88-14968-2026-cass-ksoj004-253200",
        case_number="88-14968/2026",
        institute="invalidity",
        court_holding_ru=(
            "Предварительный договор купли-продажи доли в праве на дом и участок заключён "
            "гражданкой, признанной недееспособной, без согласия органа опеки. По статье 171 ГК РФ "
            "сделка ничтожна и правовых последствий не порождает; недействительность не зависит от "
            "добросовестности контрагента, а предварительный договор перехода права собственности "
            "не влечёт. В иске о признании права собственности отказано."
        ),
        mapping_note_ru=(
            "Здесь два порока разом, и модель обязана не смешать их. Недееспособность даёт "
            "ничтожность (`incapacitated_person_transaction`), а отсутствие согласия органа опеки "
            "само по себе даёт лишь оспоримость и только при осведомлённости контрагента: "
            "`required_consent_absent` — True, `counterparty_knew_consent_absent` — False, поэтому "
            "оспоримого основания не возникает. Исполнения по договору не было, поэтому реституции "
            "модель не требует — и это совпадает с решением, где ничего не возвращалось."
        ),
        facts={
            "transaction_concluded": True,
            "invalidity_claim_made": True,
            "claimant_is_transaction_party": True,
            "claimant_legally_authorized": False,
            "claimant_rights_or_interests_affected": True,
            "court_decision_entered_into_force": True,
            "nullity_consequences_requested": False,
            "nullity_legal_interest_proven": False,
            "good_faith_reliance_created": False,
            "party_confirmed_voidable_transaction": False,
            "ground_known_at_confirmation": False,
            "performance_accepted_under_entrepreneurial_contract": False,
            "claimant_did_not_reciprocate_performance": False,
            "claimant_knew_ground_at_performance_acceptance": False,
            "performance_violates_third_party_or_public_interests": False,
            "violates_law": False,
            "public_interests_or_third_rights_affected": False,
            "law_expressly_makes_void": False,
            "immoral_purpose_proven": False,
            "both_parties_intentional_immoral_purpose": False,
            "sham_intent_proven": False,
            "feigned_intent_proven": False,
            "disguised_transaction_identified": False,
            "incapacitated_person_transaction": True,
            "minor_under_14_transaction": False,
            "benefit_to_incapacitated_or_minor_proven": False,
            "required_consent_absent": True,
            "counterparty_knew_consent_absent": False,
            "authority_restriction_violated": False,
            "counterparty_knew_authority_restriction": False,
            "entity_beyond_statutory_purpose": False,
            "counterparty_knew_beyond_purpose": False,
            "obvious_entity_damage_proven": False,
            "counterparty_knew_obvious_damage": False,
            "material_mistake_proven": False,
            "mistake_risk_assumed": False,
            "deception_proven": False,
            "violence_or_threat_proven": False,
            "adverse_circumstances_proven": False,
            "extremely_unfavorable_terms_proven": False,
            "counterparty_exploited_circumstances": False,
            "unable_to_understand_actions_proven": False,
            "limited_capacity_without_consent": False,
            "minor_14_18_without_consent": False,
            "execution_started": False,
            "void_limitation_period_expired": False,
            "voidable_limitation_period_expired": False,
            "invalid_part_separable": False,
            "remainder_preserves_transaction_purpose": False,
            "party_a_performed": False,
            "party_b_performed": False,
            "return_in_kind_possible": False,
            "value_of_performance_proven": False,
            "additional_damages_claimed": False,
            "additional_damages_causally_linked": False,
            "statutory_disposal_prohibition_violated": False,
            "judicial_disposal_prohibition_violated": False,
            "acquirer_knew_of_disposal_prohibition": False,
        },
        expected_conclusions={
            "capacity_void_ground": True,
            "void_ground_detected": True,
            "consent_voidable_ground": False,
            "contractual_effect_displaced": True,
            "restitution_required": False,
            "transaction_presumed_effective": False,
            "nullity_consequences_prerequisites": False,
        },
    ),
    RealCaseScenario(
        case_id="a12-3652-2019-cass-apv-181344",
        case_number="А12-3652/2019",
        institute="persons",
        court_holding_ru=(
            "Контрагент на момент заключения договоров был исключён из ЕГРЮЛ. Организация, не "
            "прошедшая государственную регистрацию, правоспособностью юридического лица не "
            "обладает, а её действия сделками признаны быть не могут. В признании недействительным "
            "решения налогового органа отказано."
        ),
        mapping_note_ru=(
            "Правоспособность юридического лица здесь отсутствует не из-за содержания устава, а "
            "из-за статуса в реестре, поэтому установлен `entity_registration_or_status_breached`, "
            "а не `entity_capacity_scope_breached`. Налоговые последствия — доначисление, пени, "
            "штраф — институтом лиц не разбираются: он отвечает на вопрос о правоспособности "
            "стороны, а не о признании расходов."
        ),
        facts={
            "party_capacity_asserted": True,
            "legal_capacity_rules_breached": False,
            "active_capacity_age_rules_breached": False,
            "incapacity_declared_by_court": False,
            "limited_capacity_rules_breached": False,
            "guardianship_consent_missing": False,
            "capacity_restriction_by_agreement": False,
            "entity_capacity_scope_breached": False,
            "entity_registration_or_status_breached": True,
            "entity_body_authority_breached": False,
        },
        expected_conclusions={
            "persons_qualified": True,
            "entity_registration_duty_breached": True,
            "entity_capacity_scope_duty_breached": False,
            "requires_human_persons_assessment": True,
        },
    ),
    RealCaseScenario(
        case_id="a53-32148-2023-cass-ask-203585",
        case_number="А53-32148/2023",
        institute="persons",
        court_holding_ru=(
            "Коммерческая организация наделена общей правоспособностью и вправе совершать любые не "
            "запрещённые законом сделки, если устав не содержит исчерпывающего перечня видов "
            "деятельности. Договор целевого займа, одобренный советом директоров, целям "
            "деятельности общества не противоречит, крупным не является и ущерба не причиняет; в "
            "иске отказано."
        ),
        mapping_note_ru=(
            "Пара к делу А12-3652/2019 и проверка на ложное срабатывание: правоспособность "
            "заявлена, но ни одно правило института не нарушено. Довод истца о противоречии "
            "уставным целям переведён именно как отсутствие нарушения "
            "`entity_capacity_scope_breached`: суд установил, что устав исчерпывающего перечня не "
            "содержит. Одобрение советом директоров даёт False по "
            "`entity_body_authority_breached`."
        ),
        facts={
            "party_capacity_asserted": True,
            "legal_capacity_rules_breached": False,
            "active_capacity_age_rules_breached": False,
            "incapacity_declared_by_court": False,
            "limited_capacity_rules_breached": False,
            "guardianship_consent_missing": False,
            "capacity_restriction_by_agreement": False,
            "entity_capacity_scope_breached": False,
            "entity_registration_or_status_breached": False,
            "entity_body_authority_breached": False,
        },
        expected_conclusions={
            "persons_qualified": True,
            "entity_capacity_scope_duty_breached": False,
            "entity_body_authority_duty_breached": False,
            "entity_registration_duty_breached": False,
            "requires_human_persons_assessment": False,
        },
    ),
    RealCaseScenario(
        case_id="a35-3775-2020-cass-acn-151105",
        case_number="А35-3775/2020",
        institute="objects",
        court_holding_ru=(
            "Предметом договора были пестициды, не внесённые в Государственный каталог и не "
            "прошедшие обязательную сертификацию. Оборот таких препаратов не допускается, поэтому "
            "договор признан ничтожным: в иске о взыскании долга отказано, встречный иск "
            "удовлетворён, уплаченное взыскано, а продавец обязан принять товар."
        ),
        mapping_note_ru=(
            "Дело проверяет ту часть модели объектов, до которой синтетическое дело о поставке не "
            "доходит: ограничение оборотоспособности предмета. Отсутствие государственной "
            "регистрации и сертификации — не самостоятельные предикаты, а способ доказать один: "
            "`object_not_in_civil_circulation`. Несоответствие товара требованиям качества суд "
            "привёл дополнительно, и оно относится к модели купли-продажи, а не к модели объектов."
        ),
        facts={
            "object_of_rights_asserted": True,
            "object_classification_breached": False,
            "object_not_in_civil_circulation": True,
            "immovable_classification_breached": False,
            "divisibility_or_complex_thing_breached": False,
            "principal_and_appurtenance_breached": False,
            "fruits_products_income_breached": False,
            "money_or_securities_rules_breached": False,
            "intangible_benefits_protection_breached": False,
            "honour_and_reputation_protection_breached": False,
        },
        expected_conclusions={
            "objects_qualified": True,
            "object_excluded_from_circulation": True,
            "requires_human_objects_assessment": True,
        },
    ),
    RealCaseScenario(
        case_id="a19-26528-2022-cass-avs-127653",
        case_number="А19-26528/2022",
        institute="attribution_delay",
        court_holding_ru=(
            "Заказчик несвоевременно предоставил нефть для исследования, что повлияло на сроки "
            "выполнения работ. Подрядчик не считается просрочившим, пока обязательство не может "
            "быть исполнено вследствие просрочки кредитора (пункт 3 статьи 405, пункт 1 статьи 406 "
            "ГК РФ); размер неустойки уменьшен."
        ),
        mapping_note_ru=(
            "Просрочка должника формально наступила, поэтому `debtor_delay_established` — True, и "
            "снимает её не отсутствие факта, а встречная просрочка кредитора. Именно так устроено "
            "правило: должник в просрочке лишь тогда, когда кредитор в ней не находится. Вина "
            "заказчика записана отдельным предикатом `creditor_fault_contributed_to_breach`, "
            "потому что она даёт другое последствие — уменьшение ответственности, а не её снятие. "
            "Снижение неустойки по статье 333 ГК РФ разбирает модель ответственности, а не эта."
        ),
        facts={
            "obligation_breach_asserted": True,
            "breach_caused_by_debtor_employees": False,
            "performance_entrusted_to_third_party": False,
            "third_party_caused_breach": False,
            "law_assigns_liability_to_performer": False,
            "creditor_fault_contributed_to_breach": True,
            "creditor_failed_to_mitigate_loss": False,
            "debtor_delay_established": True,
            "performance_lost_interest_for_creditor": False,
            "creditor_delay_established": True,
        },
        expected_conclusions={
            "creditor_in_delay": True,
            "creditor_delay_excuses_debtor": True,
            "debtor_in_delay": False,
            "creditor_fault_established": True,
            "liability_reducible_for_creditor_fault": True,
        },
    ),
    RealCaseScenario(
        case_id="a40-180691-2024-cass-ams-578542",
        case_number="А40-180691/2024",
        institute="attribution_delay",
        court_holding_ru=(
            "Заказчик изменил техническое задание, из-за чего поставщик не мог направить расчётно- "
            "калькуляционные материалы в срок; сами материалы направлены уполномоченному "
            "представителю заказчика вовремя. Поставщик не считается просрочившим, оснований для "
            "начисления неустойки нет."
        ),
        mapping_note_ru=(
            "Изменение технического задания переведено сразу двумя предикатами, и это не "
            "дублирование: оно и создало невозможность исполнить в срок "
            "(`creditor_delay_established`), и является виной кредитора в нарушении "
            "(`creditor_fault_contributed_to_breach`). Направление материалов надлежащему "
            "представителю — вопрос о том, кому вручено исполнение; он относится к модели средств "
            "защиты, и здесь в предикаты не переводится."
        ),
        facts={
            "obligation_breach_asserted": True,
            "breach_caused_by_debtor_employees": False,
            "performance_entrusted_to_third_party": False,
            "third_party_caused_breach": False,
            "law_assigns_liability_to_performer": False,
            "creditor_fault_contributed_to_breach": True,
            "creditor_failed_to_mitigate_loss": False,
            "debtor_delay_established": True,
            "performance_lost_interest_for_creditor": False,
            "creditor_delay_established": True,
        },
        expected_conclusions={
            "creditor_in_delay": True,
            "creditor_delay_excuses_debtor": True,
            "debtor_in_delay": False,
            "creditor_fault_established": True,
            "liability_reducible_for_creditor_fault": True,
        },
    ),
    RealCaseScenario(
        case_id="a55-1232-2025-cass-apv-244369",
        case_number="А55-1232/2025",
        institute="attribution_delay",
        court_holding_ru=(
            "Заказчик не исполнил встречные обязательства: не предоставил информацию, не решил "
            "вопросы выноса опор освещения и переустройства сетей. Просрочка выполнения работ "
            "произошла по его вине, подрядчик просрочившим не считается, неустойка и штраф "
            "начислению не подлежат."
        ),
        mapping_note_ru=(
            "Конфигурация повторяет дела А19-26528/2022 и А40-180691/2024: встречная просрочка "
            "кредитора снимает просрочку должника, а вина кредитора уменьшает ответственность. "
            "Совпадение записано намеренно — в выгрузке пять дел о просрочке кредитора, и "
            "различных наборов фактов среди них два, а не пять. Авария на сетях ресурсоснабжающей "
            "организации в предикаты не переведена: суд положил в основание бездействие заказчика, "
            "а не саму аварию."
        ),
        facts={
            "obligation_breach_asserted": True,
            "breach_caused_by_debtor_employees": False,
            "performance_entrusted_to_third_party": False,
            "third_party_caused_breach": False,
            "law_assigns_liability_to_performer": False,
            "creditor_fault_contributed_to_breach": True,
            "creditor_failed_to_mitigate_loss": False,
            "debtor_delay_established": True,
            "performance_lost_interest_for_creditor": False,
            "creditor_delay_established": True,
        },
        expected_conclusions={
            "creditor_in_delay": True,
            "creditor_delay_excuses_debtor": True,
            "debtor_in_delay": False,
            "creditor_fault_established": True,
        },
    ),
    RealCaseScenario(
        case_id="a40-265730-2022-cass-ams-519159",
        case_number="А40-265730/2022",
        institute="attribution_delay",
        court_holding_ru=(
            "Задолженность по субаренде взыскана за вычетом обеспечительного платежа. Неустойка не "
            "подлежит взысканию, поскольку обязательство не исполнено ввиду просрочки кредитора "
            "(пункт 3 статьи 405, пункт 1 статьи 406 ГК РФ). Во взыскании ущерба отказано: "
            "первоначальное состояние помещения и объём повреждений не подтверждены."
        ),
        mapping_note_ru=(
            "Чистый случай просрочки кредитора, без вины: суд снял неустойку, но ответственность "
            "ни на сколько не уменьшал, поэтому `creditor_fault_contributed_to_breach` — False. "
            "Разница с делами А19-26528/2022 и А40-180691/2024 именно в этом предикате, и она не "
            "косметическая: снятие просрочки и уменьшение ответственности — разные последствия "
            "разных фактов. Недоказанность ущерба относится к модели средств защиты."
        ),
        facts={
            "obligation_breach_asserted": True,
            "breach_caused_by_debtor_employees": False,
            "performance_entrusted_to_third_party": False,
            "third_party_caused_breach": False,
            "law_assigns_liability_to_performer": False,
            "creditor_fault_contributed_to_breach": False,
            "creditor_failed_to_mitigate_loss": False,
            "debtor_delay_established": True,
            "performance_lost_interest_for_creditor": False,
            "creditor_delay_established": True,
        },
        expected_conclusions={
            "creditor_in_delay": True,
            "creditor_delay_excuses_debtor": True,
            "debtor_in_delay": False,
            "creditor_fault_established": False,
            "liability_reducible_for_creditor_fault": False,
        },
    ),
    RealCaseScenario(
        case_id="a75-15705-2025-cass-azs-221575",
        case_number="А75-15705/2025",
        institute="attribution_delay",
        court_holding_ru=(
            "Заказчик дважды необоснованно отказал в приёмке оборудования по формальным "
            "основаниям. Затягивание процедуры приёмки вызвано его действиями и квалифицируется "
            "как просрочка кредитора, поэтому её последствия не могут возлагаться на поставщика; "
            "во взыскании неустойки отказано."
        ),
        mapping_note_ru=(
            "Вторая конфигурация просрочки кредитора без вины, вместе с делом А40-265730/2022. "
            "Отказ в приёмке — действие кредитора, без которого обязательство не может считаться "
            "исполненным, поэтому он переведён как `creditor_delay_established`. Списание "
            "неустойки по Правилам № 783 в предикаты не переводится: это бюджетное регулирование "
            "государственных контрактов, а не норма ГК РФ."
        ),
        facts={
            "obligation_breach_asserted": True,
            "breach_caused_by_debtor_employees": False,
            "performance_entrusted_to_third_party": False,
            "third_party_caused_breach": False,
            "law_assigns_liability_to_performer": False,
            "creditor_fault_contributed_to_breach": False,
            "creditor_failed_to_mitigate_loss": False,
            "debtor_delay_established": True,
            "performance_lost_interest_for_creditor": False,
            "creditor_delay_established": True,
        },
        expected_conclusions={
            "creditor_in_delay": True,
            "creditor_delay_excuses_debtor": True,
            "debtor_in_delay": False,
            "creditor_fault_established": False,
        },
    ),
    RealCaseScenario(
        case_id="a03-19562-2024-cass-azs-218301",
        case_number="А03-19562/2024",
        institute="obligation_dynamics",
        court_holding_ru=(
            "Задолженность заказчика по договору подряда уменьшена на сумму неустойки за просрочку "
            "выполнения работ: на момент возникновения обязательства по оплате у заказчика уже "
            "имелось зачётопригодное требование. Независимо от процедуры зачёта обязательства "
            "считаются прекращёнными ретроспективно — с момента, когда они стали способны к зачёту "
            "(статья 410 ГК РФ)."
        ),
        mapping_note_ru=(
            "Зачёт в модели требует шести условий разом: встречности, однородности, наступления "
            "срока по обоим требованиям, доказанности суммы и отсутствия запрета. Все они выведены "
            "из установленного судом факта зачётопригодности. Суммы требований не равны, поэтому "
            "ожидается частичное прекращение, а не полное, — и это тот случай, где легко "
            "ошибиться: зачёт состоялся, но обязательство погашено не целиком. Ретроспективность "
            "момента прекращения модель не выражает: предикатов о времени в этом институте нет."
        ),
        facts={
            "obligation_exists": True,
            "obligation_breached": True,
            "accrued_claims_exist": True,
            "partial_termination_intended": False,
            "assignment_agreement_concluded": False,
            "assignment_form_observed": False,
            "assigned_claim_exists": False,
            "assigned_claim_identified": False,
            "future_claim_determinable": False,
            "claim_personal_to_creditor": False,
            "assignment_prohibited_by_law": False,
            "contract_restricts_assignment": False,
            "debtor_consent_required": False,
            "debtor_consent_obtained": False,
            "debtor_notified": False,
            "proof_of_transfer_provided": False,
            "debtor_performed_original_before_notice": False,
            "debtor_defense_existed_at_notice": False,
            "debtor_counterclaim_existed_at_notice": False,
            "cedent_transferred_documents": False,
            "claim_invalid": False,
            "cedent_knew_claim_invalid": False,
            "cedent_guaranteed_debtor_performance": False,
            "debtor_failed_after_assignment": False,
            "debt_transfer_agreement_concluded": False,
            "debt_transfer_form_observed": False,
            "new_debtor_identified": False,
            "creditor_consented_debt_transfer": False,
            "original_debtor_released": False,
            "cumulative_debt_assumption_agreed": False,
            "business_debt_assumption": False,
            "new_debtor_defense_exists": False,
            "security_provider_consented_new_debtor": False,
            "contract_transfer_agreed": False,
            "all_parties_consented_contract_transfer": False,
            "performance_rendered": False,
            "performance_accepted_as_proper": False,
            "performance_partial": False,
            "creditor_issued_receipt": False,
            "creditor_returned_debt_instrument": False,
            "creditor_refused_confirmation": False,
            "notary_or_court_deposit_made": False,
            "deposit_ground_creditor_absent_or_evasive": False,
            "deposit_notice_sent": False,
            "accord_agreed": False,
            "accord_form_observed": False,
            "accord_performance_provided": False,
            "set_off_declared": True,
            "set_off_notice_delivered": True,
            "counterclaims_mutual": True,
            "counterclaims_homogeneous": True,
            "active_claim_due": True,
            "passive_claim_due_or_early_allowed": True,
            "set_off_prohibited": False,
            "active_claim_limitation_expired": False,
            "set_off_amount_proven": True,
            "claims_equal_amount": False,
            "novation_agreed": False,
            "novation_intent_clear": False,
            "new_subject_or_basis": False,
            "new_obligation_terms_agreed": False,
            "novation_form_observed": False,
            "third_party_security_exists": False,
            "third_party_security_consented_novation": False,
            "debt_forgiveness_declared": False,
            "debt_forgiveness_notice_delivered": False,
            "debtor_objected_forgiveness": False,
            "third_party_rights_prejudiced": False,
            "forgiveness_gift_intent": False,
            "commercial_parties": True,
            "merger_creditor_and_debtor": False,
            "objective_permanent_impossibility": False,
            "impossibility_risk_on_debtor": False,
            "debtor_in_delay_at_impossibility": False,
            "creditor_caused_impossibility": False,
            "government_act_prevents_performance": False,
            "government_act_invalidated": False,
            "personal_debtor_died": False,
            "personal_creditor_died": False,
            "obligation_personal_to_deceased": False,
            "legal_entity_liquidated": False,
            "statutory_successor_exists": False,
            "other_discharge_ground_proven": False,
        },
        expected_conclusions={
            "setoff_effective": True,
            "setoff_partial_discharge": True,
            "setoff_full_discharge": False,
            "obligation_discharged_full": False,
        },
    ),
    RealCaseScenario(
        case_id="a73-9126-2023-cass-adv-134721",
        case_number="А73-9126/2023",
        institute="obligation_dynamics",
        court_holding_ru=(
            "Перевозчик нарушил срок доставки и направил заявление о зачёте договорной неустойки в "
            "счёт неоплаченной провозной платы. Обязательство перевозчика по уплате неустойки "
            "признано прекращённым зачётом встречного однородного требования (статьи 407 и 410 ГК "
            "РФ), во взыскании штрафа и процентов отказано."
        ),
        mapping_note_ru=(
            "Вторая проверка зачёта, с той же конфигурацией, что и в деле А03-19562/2024: "
            "неустойка 34 220 рублей и провозная плата 2 519 749 рублей однородны и встречны, но "
            "не равны, поэтому прекращение частичное. Закрытие автозимника и переговоры сторон в "
            "предикаты не переводятся: суд положил в основание состоявшийся зачёт, а не "
            "невозможность исполнения."
        ),
        facts={
            "obligation_exists": True,
            "obligation_breached": True,
            "accrued_claims_exist": True,
            "partial_termination_intended": False,
            "assignment_agreement_concluded": False,
            "assignment_form_observed": False,
            "assigned_claim_exists": False,
            "assigned_claim_identified": False,
            "future_claim_determinable": False,
            "claim_personal_to_creditor": False,
            "assignment_prohibited_by_law": False,
            "contract_restricts_assignment": False,
            "debtor_consent_required": False,
            "debtor_consent_obtained": False,
            "debtor_notified": False,
            "proof_of_transfer_provided": False,
            "debtor_performed_original_before_notice": False,
            "debtor_defense_existed_at_notice": False,
            "debtor_counterclaim_existed_at_notice": False,
            "cedent_transferred_documents": False,
            "claim_invalid": False,
            "cedent_knew_claim_invalid": False,
            "cedent_guaranteed_debtor_performance": False,
            "debtor_failed_after_assignment": False,
            "debt_transfer_agreement_concluded": False,
            "debt_transfer_form_observed": False,
            "new_debtor_identified": False,
            "creditor_consented_debt_transfer": False,
            "original_debtor_released": False,
            "cumulative_debt_assumption_agreed": False,
            "business_debt_assumption": False,
            "new_debtor_defense_exists": False,
            "security_provider_consented_new_debtor": False,
            "contract_transfer_agreed": False,
            "all_parties_consented_contract_transfer": False,
            "performance_rendered": False,
            "performance_accepted_as_proper": False,
            "performance_partial": False,
            "creditor_issued_receipt": False,
            "creditor_returned_debt_instrument": False,
            "creditor_refused_confirmation": False,
            "notary_or_court_deposit_made": False,
            "deposit_ground_creditor_absent_or_evasive": False,
            "deposit_notice_sent": False,
            "accord_agreed": False,
            "accord_form_observed": False,
            "accord_performance_provided": False,
            "set_off_declared": True,
            "set_off_notice_delivered": True,
            "counterclaims_mutual": True,
            "counterclaims_homogeneous": True,
            "active_claim_due": True,
            "passive_claim_due_or_early_allowed": True,
            "set_off_prohibited": False,
            "active_claim_limitation_expired": False,
            "set_off_amount_proven": True,
            "claims_equal_amount": False,
            "novation_agreed": False,
            "novation_intent_clear": False,
            "new_subject_or_basis": False,
            "new_obligation_terms_agreed": False,
            "novation_form_observed": False,
            "third_party_security_exists": False,
            "third_party_security_consented_novation": False,
            "debt_forgiveness_declared": False,
            "debt_forgiveness_notice_delivered": False,
            "debtor_objected_forgiveness": False,
            "third_party_rights_prejudiced": False,
            "forgiveness_gift_intent": False,
            "commercial_parties": True,
            "merger_creditor_and_debtor": False,
            "objective_permanent_impossibility": False,
            "impossibility_risk_on_debtor": False,
            "debtor_in_delay_at_impossibility": False,
            "creditor_caused_impossibility": False,
            "government_act_prevents_performance": False,
            "government_act_invalidated": False,
            "personal_debtor_died": False,
            "personal_creditor_died": False,
            "obligation_personal_to_deceased": False,
            "legal_entity_liquidated": False,
            "statutory_successor_exists": False,
            "other_discharge_ground_proven": False,
        },
        expected_conclusions={
            "setoff_effective": True,
            "setoff_partial_discharge": True,
            "setoff_full_discharge": False,
        },
    ),
    RealCaseScenario(
        case_id="a33-28136-2024-cass-avs-136444",
        case_number="А33-28136/2024",
        institute="obligation_dynamics",
        court_holding_ru=(
            "Обязательство покупателя по оплате здания и сушильных камер заменено соглашением о "
            "новации заёмным обязательством на ту же сумму со сроком возврата в 60 месяцев. "
            "Обязательство по оплате прекращено новацией (статья 414 ГК РФ), поэтому оснований для "
            "расторжения договора купли-продажи и возврата имущества нет."
        ),
        mapping_note_ru=(
            "Новация в модели требует определённости воли и нового предмета или основания, и оба "
            "факта установлены судом: обязательство из купли-продажи заменено заёмным. Ключевая "
            "проверка здесь — что модель выводит полное прекращение первоначального обязательства: "
            "именно оно лишает продавца права требовать расторжения за неоплату. "
            "Недобросовестность соглашения о расторжении новации, направленного на вывод имущества "
            "из-под ареста, разбирается началами гражданского права, а не этим институтом."
        ),
        facts={
            "obligation_exists": True,
            "obligation_breached": False,
            "accrued_claims_exist": False,
            "partial_termination_intended": False,
            "assignment_agreement_concluded": False,
            "assignment_form_observed": False,
            "assigned_claim_exists": False,
            "assigned_claim_identified": False,
            "future_claim_determinable": False,
            "claim_personal_to_creditor": False,
            "assignment_prohibited_by_law": False,
            "contract_restricts_assignment": False,
            "debtor_consent_required": False,
            "debtor_consent_obtained": False,
            "debtor_notified": False,
            "proof_of_transfer_provided": False,
            "debtor_performed_original_before_notice": False,
            "debtor_defense_existed_at_notice": False,
            "debtor_counterclaim_existed_at_notice": False,
            "cedent_transferred_documents": False,
            "claim_invalid": False,
            "cedent_knew_claim_invalid": False,
            "cedent_guaranteed_debtor_performance": False,
            "debtor_failed_after_assignment": False,
            "debt_transfer_agreement_concluded": False,
            "debt_transfer_form_observed": False,
            "new_debtor_identified": False,
            "creditor_consented_debt_transfer": False,
            "original_debtor_released": False,
            "cumulative_debt_assumption_agreed": False,
            "business_debt_assumption": False,
            "new_debtor_defense_exists": False,
            "security_provider_consented_new_debtor": False,
            "contract_transfer_agreed": False,
            "all_parties_consented_contract_transfer": False,
            "performance_rendered": False,
            "performance_accepted_as_proper": False,
            "performance_partial": False,
            "creditor_issued_receipt": False,
            "creditor_returned_debt_instrument": False,
            "creditor_refused_confirmation": False,
            "notary_or_court_deposit_made": False,
            "deposit_ground_creditor_absent_or_evasive": False,
            "deposit_notice_sent": False,
            "accord_agreed": False,
            "accord_form_observed": False,
            "accord_performance_provided": False,
            "set_off_declared": False,
            "set_off_notice_delivered": False,
            "counterclaims_mutual": False,
            "counterclaims_homogeneous": False,
            "active_claim_due": False,
            "passive_claim_due_or_early_allowed": False,
            "set_off_prohibited": False,
            "active_claim_limitation_expired": False,
            "set_off_amount_proven": False,
            "claims_equal_amount": False,
            "novation_agreed": True,
            "novation_intent_clear": True,
            "new_subject_or_basis": True,
            "new_obligation_terms_agreed": True,
            "novation_form_observed": True,
            "third_party_security_exists": False,
            "third_party_security_consented_novation": False,
            "debt_forgiveness_declared": False,
            "debt_forgiveness_notice_delivered": False,
            "debtor_objected_forgiveness": False,
            "third_party_rights_prejudiced": False,
            "forgiveness_gift_intent": False,
            "commercial_parties": True,
            "merger_creditor_and_debtor": False,
            "objective_permanent_impossibility": False,
            "impossibility_risk_on_debtor": False,
            "debtor_in_delay_at_impossibility": False,
            "creditor_caused_impossibility": False,
            "government_act_prevents_performance": False,
            "government_act_invalidated": False,
            "personal_debtor_died": False,
            "personal_creditor_died": False,
            "obligation_personal_to_deceased": False,
            "legal_entity_liquidated": False,
            "statutory_successor_exists": False,
            "other_discharge_ground_proven": False,
        },
        expected_conclusions={
            "novation_effective": True,
            "obligation_discharged_full": True,
        },
    ),
    RealCaseScenario(
        case_id="a39-4009-2023-cass-avv-124719",
        case_number="А39-4009/2023",
        institute="obligation_dynamics",
        court_holding_ru=(
            "Задолженность по договору генерального подряда заменена соглашением о новации заёмным "
            "обязательством с процентами и сроком возврата. Воля сторон определённо направлена на "
            "замену первоначального обязательства другим, содержащим все существенные условия "
            "займа, поэтому оснований признать соглашение незаключённым нет."
        ),
        mapping_note_ru=(
            "Та же конфигурация, что и в деле А33-28136/2024. Дело показывает вторую сторону "
            "новации: она проверяется не только как основание прекращения, но и как "
            "самостоятельное соглашение, которое истец пытался объявить незаключённым. Для модели "
            "это один и тот же набор фактов — определённость воли и согласованность условий нового "
            "обязательства. Пропуск срока исковой давности, названный судом дополнительно, "
            "разбирает модель исковой давности."
        ),
        facts={
            "obligation_exists": True,
            "obligation_breached": False,
            "accrued_claims_exist": False,
            "partial_termination_intended": False,
            "assignment_agreement_concluded": False,
            "assignment_form_observed": False,
            "assigned_claim_exists": False,
            "assigned_claim_identified": False,
            "future_claim_determinable": False,
            "claim_personal_to_creditor": False,
            "assignment_prohibited_by_law": False,
            "contract_restricts_assignment": False,
            "debtor_consent_required": False,
            "debtor_consent_obtained": False,
            "debtor_notified": False,
            "proof_of_transfer_provided": False,
            "debtor_performed_original_before_notice": False,
            "debtor_defense_existed_at_notice": False,
            "debtor_counterclaim_existed_at_notice": False,
            "cedent_transferred_documents": False,
            "claim_invalid": False,
            "cedent_knew_claim_invalid": False,
            "cedent_guaranteed_debtor_performance": False,
            "debtor_failed_after_assignment": False,
            "debt_transfer_agreement_concluded": False,
            "debt_transfer_form_observed": False,
            "new_debtor_identified": False,
            "creditor_consented_debt_transfer": False,
            "original_debtor_released": False,
            "cumulative_debt_assumption_agreed": False,
            "business_debt_assumption": False,
            "new_debtor_defense_exists": False,
            "security_provider_consented_new_debtor": False,
            "contract_transfer_agreed": False,
            "all_parties_consented_contract_transfer": False,
            "performance_rendered": False,
            "performance_accepted_as_proper": False,
            "performance_partial": False,
            "creditor_issued_receipt": False,
            "creditor_returned_debt_instrument": False,
            "creditor_refused_confirmation": False,
            "notary_or_court_deposit_made": False,
            "deposit_ground_creditor_absent_or_evasive": False,
            "deposit_notice_sent": False,
            "accord_agreed": False,
            "accord_form_observed": False,
            "accord_performance_provided": False,
            "set_off_declared": False,
            "set_off_notice_delivered": False,
            "counterclaims_mutual": False,
            "counterclaims_homogeneous": False,
            "active_claim_due": False,
            "passive_claim_due_or_early_allowed": False,
            "set_off_prohibited": False,
            "active_claim_limitation_expired": False,
            "set_off_amount_proven": False,
            "claims_equal_amount": False,
            "novation_agreed": True,
            "novation_intent_clear": True,
            "new_subject_or_basis": True,
            "new_obligation_terms_agreed": True,
            "novation_form_observed": True,
            "third_party_security_exists": False,
            "third_party_security_consented_novation": False,
            "debt_forgiveness_declared": False,
            "debt_forgiveness_notice_delivered": False,
            "debtor_objected_forgiveness": False,
            "third_party_rights_prejudiced": False,
            "forgiveness_gift_intent": False,
            "commercial_parties": True,
            "merger_creditor_and_debtor": False,
            "objective_permanent_impossibility": False,
            "impossibility_risk_on_debtor": False,
            "debtor_in_delay_at_impossibility": False,
            "creditor_caused_impossibility": False,
            "government_act_prevents_performance": False,
            "government_act_invalidated": False,
            "personal_debtor_died": False,
            "personal_creditor_died": False,
            "obligation_personal_to_deceased": False,
            "legal_entity_liquidated": False,
            "statutory_successor_exists": False,
            "other_discharge_ground_proven": False,
        },
        expected_conclusions={
            "novation_effective": True,
            "obligation_discharged_full": True,
        },
    ),
    RealCaseScenario(
        case_id="a79-3098-2023-cass-avv-128859",
        case_number="А79-3098/2023",
        institute="obligation_dynamics",
        court_holding_ru=(
            "Участник общества простил ему долг по четырём договорам займа на 20,5 млн рублей. "
            "Прощение долга заинтересованному лицу законом не запрещено, противоправных целей не "
            "установлено, права кредиторов не нарушены: должник остался платёжеспособным и "
            "продолжал исполнять обязательства. В признании соглашения недействительным отказано."
        ),
        mapping_note_ru=(
            "Прощение долга в модели срывается тремя способами: возражением должника, нарушением "
            "прав третьих лиц и запретом дарения между коммерческими организациями. Суд прямо "
            "отверг второй, а первого и третьего в деле нет — прощал гражданин, а не коммерческая "
            "организация, поэтому `commercial_parties` — False. Заинтересованность прощающего как "
            "участника общества отдельного предиката не имеет: суд назвал её объяснением мотива, а "
            "не пороком сделки."
        ),
        facts={
            "obligation_exists": True,
            "obligation_breached": False,
            "accrued_claims_exist": False,
            "partial_termination_intended": False,
            "assignment_agreement_concluded": False,
            "assignment_form_observed": False,
            "assigned_claim_exists": False,
            "assigned_claim_identified": False,
            "future_claim_determinable": False,
            "claim_personal_to_creditor": False,
            "assignment_prohibited_by_law": False,
            "contract_restricts_assignment": False,
            "debtor_consent_required": False,
            "debtor_consent_obtained": False,
            "debtor_notified": False,
            "proof_of_transfer_provided": False,
            "debtor_performed_original_before_notice": False,
            "debtor_defense_existed_at_notice": False,
            "debtor_counterclaim_existed_at_notice": False,
            "cedent_transferred_documents": False,
            "claim_invalid": False,
            "cedent_knew_claim_invalid": False,
            "cedent_guaranteed_debtor_performance": False,
            "debtor_failed_after_assignment": False,
            "debt_transfer_agreement_concluded": False,
            "debt_transfer_form_observed": False,
            "new_debtor_identified": False,
            "creditor_consented_debt_transfer": False,
            "original_debtor_released": False,
            "cumulative_debt_assumption_agreed": False,
            "business_debt_assumption": False,
            "new_debtor_defense_exists": False,
            "security_provider_consented_new_debtor": False,
            "contract_transfer_agreed": False,
            "all_parties_consented_contract_transfer": False,
            "performance_rendered": False,
            "performance_accepted_as_proper": False,
            "performance_partial": False,
            "creditor_issued_receipt": False,
            "creditor_returned_debt_instrument": False,
            "creditor_refused_confirmation": False,
            "notary_or_court_deposit_made": False,
            "deposit_ground_creditor_absent_or_evasive": False,
            "deposit_notice_sent": False,
            "accord_agreed": False,
            "accord_form_observed": False,
            "accord_performance_provided": False,
            "set_off_declared": False,
            "set_off_notice_delivered": False,
            "counterclaims_mutual": False,
            "counterclaims_homogeneous": False,
            "active_claim_due": False,
            "passive_claim_due_or_early_allowed": False,
            "set_off_prohibited": False,
            "active_claim_limitation_expired": False,
            "set_off_amount_proven": False,
            "claims_equal_amount": False,
            "novation_agreed": False,
            "novation_intent_clear": False,
            "new_subject_or_basis": False,
            "new_obligation_terms_agreed": False,
            "novation_form_observed": False,
            "third_party_security_exists": False,
            "third_party_security_consented_novation": False,
            "debt_forgiveness_declared": True,
            "debt_forgiveness_notice_delivered": True,
            "debtor_objected_forgiveness": False,
            "third_party_rights_prejudiced": False,
            "forgiveness_gift_intent": False,
            "commercial_parties": False,
            "merger_creditor_and_debtor": False,
            "objective_permanent_impossibility": False,
            "impossibility_risk_on_debtor": False,
            "debtor_in_delay_at_impossibility": False,
            "creditor_caused_impossibility": False,
            "government_act_prevents_performance": False,
            "government_act_invalidated": False,
            "personal_debtor_died": False,
            "personal_creditor_died": False,
            "obligation_personal_to_deceased": False,
            "legal_entity_liquidated": False,
            "statutory_successor_exists": False,
            "other_discharge_ground_proven": False,
        },
        expected_conclusions={
            "debt_forgiveness_effective": True,
            "obligation_discharged_full": True,
        },
    ),
    RealCaseScenario(
        case_id="a04-4768-2025-cass-adv-143671",
        case_number="А04-4768/2025",
        institute="termination",
        court_holding_ru=(
            "Поставка дробильно-сортировочного комплекса подтверждена актом приёма-передачи, "
            "подписанным без возражений. Покупатель не доказал существенного нарушения договора, а "
            "утрата интереса к товару самостоятельным основанием для расторжения по статье 450 ГК "
            "РФ не является: риск изменения хозяйственных планов лежит на покупателе. Во встречном "
            "иске о расторжении отказано."
        ),
        mapping_note_ru=(
            "Дело проверяет судебный путь расторжения. Существенное нарушение в модели "
            "складывается из трёх фактов: оно заявлено, доказано и повлекло лишение того, на что "
            "сторона рассчитывала. Здесь заявлено, но не доказано, поэтому основание не собрано и "
            "расторжение не наступает — при том что досудебный порядок соблюдён и решение вступило "
            "в силу. Модель обязана не подменить недоказанность нарушения его отсутствием: "
            "`substantial_breach_claimed` остаётся True."
        ),
        facts={
            "contract_formed": True,
            "mutual_agreement_reached": False,
            "agreement_targets_modification": False,
            "agreement_targets_termination": False,
            "agreement_form_observed": False,
            "agreement_effective_date_reached": False,
            "judicial_request_made": True,
            "judicial_request_targets_modification": False,
            "judicial_request_targets_termination": True,
            "substantial_breach_claimed": True,
            "substantial_breach_proven": False,
            "expectation_deprivation_proven": False,
            "other_legal_or_contractual_ground_proven": False,
            "pretrial_proposal_delivered": True,
            "pretrial_refusal_received": True,
            "pretrial_response_period_expired": False,
            "court_decision_entered_into_force": True,
            "unilateral_action_declared": False,
            "unilateral_action_targets_modification": False,
            "unilateral_action_targets_termination": False,
            "unilateral_right_exists": False,
            "unilateral_notice_delivered": False,
            "unilateral_requirements_observed": False,
            "unilateral_exercise_good_faith": False,
            "same_ground_previously_waived": False,
            "circumstances_substantially_changed": False,
            "change_unforeseeable_at_conclusion": False,
            "causes_not_overcome_with_due_care": False,
            "continued_performance_upsets_balance": False,
            "changed_circumstances_risk_not_assumed": False,
            "adjustment_negotiations_failed": False,
            "exceptional_modification_preferred": False,
            "accrued_claims_exist": True,
            "counterperformance_imbalance_proven": False,
            "termination_losses_claimed": False,
            "termination_losses_causally_linked": False,
        },
        expected_conclusions={
            "substantial_breach_ground_satisfied": False,
            "judicial_termination_effective": False,
            "effective_termination": False,
        },
    ),
    RealCaseScenario(
        case_id="a40-87930-2024-cass-ams-575831",
        case_number="А40-87930/2024",
        institute="termination",
        court_holding_ru=(
            "Покупатель отказался от договора поставки мебели в одностороннем порядке, ссылаясь на "
            "существенное нарушение требований к качеству. Экспертиза установила, что существенных "
            "дефектов нет, поэтому права на односторонний отказ по статье 450 ГК РФ не возникло: "
            "первоначальный иск отклонён, встречный удовлетворён, покупатель обязан принять товар "
            "и оплатить его."
        ),
        mapping_note_ru=(
            "Пара к делу А04-4768/2025: там расторжения требовали через суд, здесь заявили "
            "односторонний отказ. Модель различает эти пути и по-разному их обрывает — вместо "
            "несостоявшегося расторжения она выводит `invalid_unilateral_action`: отказ объявлен, "
            "но ни к чему не привёл. Это сильнее, чем просто отсутствие расторжения: заявленный "
            "без права отказ сам по себе является нарушением, и модель это фиксирует."
        ),
        facts={
            "contract_formed": True,
            "mutual_agreement_reached": False,
            "agreement_targets_modification": False,
            "agreement_targets_termination": False,
            "agreement_form_observed": False,
            "agreement_effective_date_reached": False,
            "judicial_request_made": False,
            "judicial_request_targets_modification": False,
            "judicial_request_targets_termination": False,
            "substantial_breach_claimed": True,
            "substantial_breach_proven": False,
            "expectation_deprivation_proven": False,
            "other_legal_or_contractual_ground_proven": False,
            "pretrial_proposal_delivered": False,
            "pretrial_refusal_received": False,
            "pretrial_response_period_expired": False,
            "court_decision_entered_into_force": False,
            "unilateral_action_declared": True,
            "unilateral_action_targets_modification": False,
            "unilateral_action_targets_termination": True,
            "unilateral_right_exists": False,
            "unilateral_notice_delivered": True,
            "unilateral_requirements_observed": False,
            "unilateral_exercise_good_faith": False,
            "same_ground_previously_waived": False,
            "circumstances_substantially_changed": False,
            "change_unforeseeable_at_conclusion": False,
            "causes_not_overcome_with_due_care": False,
            "continued_performance_upsets_balance": False,
            "changed_circumstances_risk_not_assumed": False,
            "adjustment_negotiations_failed": False,
            "exceptional_modification_preferred": False,
            "accrued_claims_exist": True,
            "counterperformance_imbalance_proven": False,
            "termination_losses_claimed": False,
            "termination_losses_causally_linked": False,
        },
        expected_conclusions={
            "substantial_breach_ground_satisfied": False,
            "effective_termination": False,
            "invalid_unilateral_action": True,
        },
    ),
    RealCaseScenario(
        case_id="a40-252357-2016-cass-ams-301832",
        case_number="А40-252357/2016",
        institute="form",
        court_holding_ru=(
            "Договор поставки, товарная накладная и акт приёма-передачи подписаны неустановленным "
            "лицом, не уполномоченным ответчиком. Сделка в письменной форме должна быть подписана "
            "лицом, её совершающим, или должным образом уполномоченным (пункт 1 статьи 160 ГК РФ); "
            "в иске о взыскании долга отказано, встречный иск о недействительности удовлетворён."
        ),
        mapping_note_ru=(
            "Здесь модель формы расходится с итогом дела, и расхождение названо прямо. Письменная "
            "форма не соблюдена, поэтому свидетельские показания недопустимы, но "
            "недействительности из одного этого не следует: пункт 1 статьи 162 ГК РФ такого "
            "последствия не устанавливает, и "
            "`written_noncompliance_invalidates_by_law_or_agreement` — False. Суд признал сделку "
            "недействительной по статьям 53 и 168 ГК РФ — за подписание неуполномоченным лицом, а "
            "не за порок формы. Ожидание записано по институту формы: он отвечает за последствия "
            "несоблюдения формы, а не за все основания недействительности."
        ),
        facts={
            "oral_form_permitted": False,
            "simple_written_form_required": True,
            "notarial_form_required": False,
            "simple_written_form_observed": False,
            "document_signed_by_parties": False,
            "exchange_of_documents": False,
            "electronic_signature_valid": False,
            "notarial_form_observed": False,
            "written_noncompliance_invalidates_by_law_or_agreement": False,
            "performance_or_written_proof_available": False,
            "written_offer_made": False,
            "offer_terms_performed_as_acceptance": False,
        },
        expected_conclusions={
            "written_form_satisfied": False,
            "form_requirement_satisfied": False,
            "witness_testimony_barred": True,
            "transaction_void_for_form": False,
        },
    ),
    RealCaseScenario(
        case_id="a41-25109-2016-cass-ams-262071",
        case_number="А41-25109/2016",
        institute="form",
        court_holding_ru=(
            "Письменный договор энергоснабжения не заключался, но ресурсоснабжающая организация "
            "фактически поставляла тепловую энергию. Отсутствие письменного документа не означает "
            "отсутствия договора как обязательства; несоблюдение простой письменной формы влечёт "
            "недействительность только в случаях, прямо предусмотренных законом или соглашением, а "
            "для энергоснабжения они не установлены. В иске о признании сделки недействительной "
            "отказано."
        ),
        mapping_note_ru=(
            "Дело прямо проверяет то правило, вокруг которого строится вся модель формы: "
            "несоблюдение письменной формы по общему правилу недействительности не влечёт. Акты "
            "приёма-передачи дают `performance_or_written_proof_available` — True, и модель не "
            "поднимает флаг экспертизы: недопустимость свидетельских показаний вреда не причиняет, "
            "когда письменные доказательства есть."
        ),
        facts={
            "oral_form_permitted": False,
            "simple_written_form_required": True,
            "notarial_form_required": False,
            "simple_written_form_observed": False,
            "document_signed_by_parties": False,
            "exchange_of_documents": False,
            "electronic_signature_valid": False,
            "notarial_form_observed": False,
            "written_noncompliance_invalidates_by_law_or_agreement": False,
            "performance_or_written_proof_available": True,
            "written_offer_made": False,
            "offer_terms_performed_as_acceptance": False,
        },
        expected_conclusions={
            "written_form_satisfied": False,
            "witness_testimony_barred": True,
            "transaction_void_for_form": False,
            "requires_human_form_assessment": False,
        },
    ),
    RealCaseScenario(
        case_id="a60-47243-2018-cass-aur-207691",
        case_number="А60-47243/2018",
        institute="form",
        court_holding_ru=(
            "Договор поставки и спецификации подписаны со стороны истца факсимиле при отсутствии "
            "соглашения сторон об использовании факсимильного воспроизведения подписи. Договор "
            "признан незаключённым ввиду несоблюдения письменной формы; в признании его ничтожным "
            "отказано, а предоплата взыскана как неосновательное обогащение, поскольку передача "
            "товара не доказана."
        ),
        mapping_note_ru=(
            "Пара к делу А41-25109/2016, разводящая последствия по одному предикату. Форма не "
            "соблюдена в обоих делах и недействительности не влечёт ни в одном, но здесь "
            "письменных доказательств исполнения нет — ответчик передачу товара не доказал. "
            "Поэтому `performance_or_written_proof_available` — False, и модель поднимает флаг "
            "экспертизы: недопустимость свидетельских показаний становится решающей, когда "
            "доказывать больше нечем. Взыскание предоплаты как неосновательного обогащения "
            "институтом формы не разбирается."
        ),
        facts={
            "oral_form_permitted": False,
            "simple_written_form_required": True,
            "notarial_form_required": False,
            "simple_written_form_observed": False,
            "document_signed_by_parties": False,
            "exchange_of_documents": False,
            "electronic_signature_valid": False,
            "notarial_form_observed": False,
            "written_noncompliance_invalidates_by_law_or_agreement": False,
            "performance_or_written_proof_available": False,
            "written_offer_made": False,
            "offer_terms_performed_as_acceptance": False,
        },
        expected_conclusions={
            "written_form_satisfied": False,
            "transaction_void_for_form": False,
            "witness_testimony_barred": True,
            "requires_human_form_assessment": True,
        },
    ),
    RealCaseScenario(
        case_id="a43-549-2022-cass-avv-119249",
        case_number="А43-549/2022",
        institute="performance_remedies",
        court_holding_ru=(
            "Винто-рулевая колонка судна вышла из строя в гарантийный срок по производственным и "
            "конструктивным причинам, что подтверждено экспертизой. Реальный ущерб в размере 28 "
            "605 765 рублей взыскан с завода-изготовителя. Во взыскании упущенной выгоды отказано: "
            "не доказано, что на период ремонта были запланированы конкретные перевозки, которые "
            "не состоялись."
        ),
        mapping_note_ru=(
            "Дело разводит две части убытков, которые в модели собираются по-разному. Реальный "
            "ущерб доказан, причинная связь установлена экспертизой, поэтому предпосылки "
            "возмещения собраны. Упущенная выгода заявлена, но мер и приготовлений для её "
            "получения не доказано: `lost_profit_claimed` — True при `lost_profit_measures_proven` "
            "— False, и модель отказывает именно в этой части, не трогая реальный ущерб. Отказ во "
            "взыскании процентов на сумму убытков относится к правилам статьи 395 ГК РФ и здесь не "
            "проверяется."
        ),
        facts={
            "obligation_exists": True,
            "breach_established": True,
            "performance_tendered": False,
            "subject_conforms": False,
            "quality_quantity_conform": False,
            "performance_at_due_time": False,
            "performance_at_proper_place": False,
            "performance_to_proper_recipient": False,
            "debtor_requested_authority_proof": False,
            "authority_proof_provided": False,
            "partial_performance_tendered": False,
            "partial_performance_allowed": False,
            "monetary_obligation": False,
            "all_parties_acting_in_business": True,
            "early_performance_tendered": False,
            "early_performance_allowed": False,
            "third_party_performance_tendered": False,
            "debtor_assigned_third_party_performance": False,
            "debtor_monetary_delay": False,
            "third_party_property_right_at_risk": False,
            "personal_performance_required": False,
            "demand_obligation": False,
            "creditor_demand_delivered": False,
            "statutory_or_agreed_grace_elapsed": False,
            "creditor_prerequisite_action_required": False,
            "creditor_prerequisite_action_completed": False,
            "payment_received_by_creditor_bank": False,
            "multiple_homogeneous_debts": False,
            "debtor_designated_debt": False,
            "debt_designation_valid": False,
            "payment_insufficient": False,
            "extra_expenses_caused_by_creditor": False,
            "alternative_obligation": False,
            "choice_holder_selected": False,
            "facultative_obligation": False,
            "facultative_substitute_tendered": False,
            "multiple_debtors": False,
            "solidarity_by_law_or_contract": False,
            "joint_business_obligation": False,
            "one_solidary_debtor_performed_full": False,
            "creditor_claimed_one_solidary_debtor": False,
            "internal_recourse_shares_proven": False,
            "reciprocal_obligations": False,
            "counterperformance_due": False,
            "counterparty_failed_due_performance": False,
            "clear_future_nonperformance": False,
            "suspension_notice_delivered": False,
            "refusal_notice_delivered": False,
            "own_counterperformance_tendered": False,
            "specific_claim_override": False,
            "loss_claimed": True,
            "actual_loss_proven": True,
            "lost_profit_claimed": True,
            "lost_profit_measures_proven": False,
            "causation_proven": True,
            "reasonable_amount_basis": True,
            "exact_amount_not_established": False,
            "creditor_mitigation_taken": True,
            "creditor_contributed_to_loss": False,
            "replacement_transaction_made": False,
            "replacement_transaction_reasonable": False,
            "current_price_available": False,
            "specific_performance_claimed": False,
            "performance_objectively_possible": False,
            "creditor_lost_interest_due_delay": False,
            "substitute_performance_by_creditor": False,
            "substitute_costs_reasonable_documented": False,
            "individual_specific_thing_due": False,
            "thing_transferred_to_protected_third_party": False,
            "monetary_delay": False,
            "article_395_claimed": False,
            "penalty_for_same_monetary_delay": False,
            "article_395_contract_override": False,
            "statutory_rate_basis_proven": False,
            "interest_period_proven": False,
            "damages_above_interest_claimed": False,
            "damages_above_interest_proven": False,
            "third_party_caused_breach": False,
            "debtor_responsible_for_third_party": False,
            "primary_debtor_claimed": False,
            "primary_refused_or_no_response": False,
            "subsidiary_debtor_claimed": False,
            "liability_limit_clause_or_law": False,
            "intentional_breach": False,
            "advance_intentional_liability_exclusion": False,
            "debtor_delay": False,
            "creditor_refused_proper_performance": False,
            "creditor_omitted_required_action": False,
            "creditor_delay_loss_proven": False,
            "indemnity_agreement": False,
            "indemnity_business_context": False,
            "indemnity_clear": False,
            "indemnity_trigger_unrelated_to_breach": False,
            "indemnity_loss_occurred": False,
            "indemnity_amount_or_method_agreed": False,
            "indemnity_bad_faith_event_caused": False,
        },
        expected_conclusions={
            "damages_prerequisites_satisfied": True,
            "lost_profit_supported": False,
            "creditor_fault_reduction_issue": False,
        },
    ),
    RealCaseScenario(
        case_id="a43-1461-2023-cass-avv-129804",
        case_number="А43-1461/2023",
        institute="performance_remedies",
        court_holding_ru=(
            "Продавец после отказа от договора продал гидравлический кран третьему лицу по более "
            "низкой цене и потребовал разницу как убытки. Договор с заводом-изготовителем заключён "
            "в рамках обычной дилерской деятельности, а не во исполнение спорного договора, "
            "поэтому последующая продажа замещающей сделкой не является. Противоправность действий "
            "покупателя, причинная связь и вина не доказаны; во встречном иске об убытках "
            "отказано, аванс и проценты взысканы с продавца."
        ),
        mapping_note_ru=(
            "Замещающая сделка в модели требует двух фактов, и второй здесь отпадает: сделка "
            "совершена (`replacement_transaction_made`), но разумной заменой не является "
            "(`replacement_transaction_reasonable` — False), потому что заключена в обычной "
            "хозяйственной деятельности. Текущая цена как альтернативное основание тоже не "
            "годится: правило требует, чтобы замещающей сделки не было вовсе. Общие предпосылки "
            "возмещения не собраны — причинная связь не доказана."
        ),
        facts={
            "obligation_exists": True,
            "breach_established": True,
            "performance_tendered": False,
            "subject_conforms": False,
            "quality_quantity_conform": False,
            "performance_at_due_time": False,
            "performance_at_proper_place": False,
            "performance_to_proper_recipient": False,
            "debtor_requested_authority_proof": False,
            "authority_proof_provided": False,
            "partial_performance_tendered": False,
            "partial_performance_allowed": False,
            "monetary_obligation": False,
            "all_parties_acting_in_business": True,
            "early_performance_tendered": False,
            "early_performance_allowed": False,
            "third_party_performance_tendered": False,
            "debtor_assigned_third_party_performance": False,
            "debtor_monetary_delay": False,
            "third_party_property_right_at_risk": False,
            "personal_performance_required": False,
            "demand_obligation": False,
            "creditor_demand_delivered": False,
            "statutory_or_agreed_grace_elapsed": False,
            "creditor_prerequisite_action_required": False,
            "creditor_prerequisite_action_completed": False,
            "payment_received_by_creditor_bank": False,
            "multiple_homogeneous_debts": False,
            "debtor_designated_debt": False,
            "debt_designation_valid": False,
            "payment_insufficient": False,
            "extra_expenses_caused_by_creditor": False,
            "alternative_obligation": False,
            "choice_holder_selected": False,
            "facultative_obligation": False,
            "facultative_substitute_tendered": False,
            "multiple_debtors": False,
            "solidarity_by_law_or_contract": False,
            "joint_business_obligation": False,
            "one_solidary_debtor_performed_full": False,
            "creditor_claimed_one_solidary_debtor": False,
            "internal_recourse_shares_proven": False,
            "reciprocal_obligations": False,
            "counterperformance_due": False,
            "counterparty_failed_due_performance": False,
            "clear_future_nonperformance": False,
            "suspension_notice_delivered": False,
            "refusal_notice_delivered": False,
            "own_counterperformance_tendered": False,
            "specific_claim_override": False,
            "loss_claimed": True,
            "actual_loss_proven": False,
            "lost_profit_claimed": False,
            "lost_profit_measures_proven": False,
            "causation_proven": False,
            "reasonable_amount_basis": True,
            "exact_amount_not_established": False,
            "creditor_mitigation_taken": True,
            "creditor_contributed_to_loss": False,
            "replacement_transaction_made": True,
            "replacement_transaction_reasonable": False,
            "current_price_available": False,
            "specific_performance_claimed": False,
            "performance_objectively_possible": False,
            "creditor_lost_interest_due_delay": False,
            "substitute_performance_by_creditor": False,
            "substitute_costs_reasonable_documented": False,
            "individual_specific_thing_due": False,
            "thing_transferred_to_protected_third_party": False,
            "monetary_delay": False,
            "article_395_claimed": False,
            "penalty_for_same_monetary_delay": False,
            "article_395_contract_override": False,
            "statutory_rate_basis_proven": False,
            "interest_period_proven": False,
            "damages_above_interest_claimed": False,
            "damages_above_interest_proven": False,
            "third_party_caused_breach": False,
            "debtor_responsible_for_third_party": False,
            "primary_debtor_claimed": False,
            "primary_refused_or_no_response": False,
            "subsidiary_debtor_claimed": False,
            "liability_limit_clause_or_law": False,
            "intentional_breach": False,
            "advance_intentional_liability_exclusion": False,
            "debtor_delay": False,
            "creditor_refused_proper_performance": False,
            "creditor_omitted_required_action": False,
            "creditor_delay_loss_proven": False,
            "indemnity_agreement": False,
            "indemnity_business_context": False,
            "indemnity_clear": False,
            "indemnity_trigger_unrelated_to_breach": False,
            "indemnity_loss_occurred": False,
            "indemnity_amount_or_method_agreed": False,
            "indemnity_bad_faith_event_caused": False,
        },
        expected_conclusions={
            "replacement_transaction_damages": False,
            "damages_prerequisites_satisfied": False,
            "current_price_damages": False,
        },
    ),
    RealCaseScenario(
        case_id="a82-7717-2024-cass-avv-131271",
        case_number="А82-7717/2024",
        institute="performance_remedies",
        court_holding_ru=(
            "Подача электроэнергии на объект предпринимателя была прекращена без уведомления и "
            "восстановлена по решению суда. В иске об убытках отказано: срок исковой давности "
            "пропущен, причинная связь между отключением и повреждениями здания не доказана, а "
            "упущенная выгода по договору энергоснабжения не взыскивается в силу пункта 1 статьи "
            "547 ГК РФ, ограничивающего ответственность реальным ущербом."
        ),
        mapping_note_ru=(
            "Ограничение ответственности законом — самостоятельный предикат "
            "`liability_limit_clause_or_law`, и он поднимает вопрос независимо от того, доказаны "
            "ли убытки. Здесь не доказано ничего: ни реального ущерба, ни мер для получения "
            "упущенной выгоды, ни причинной связи, — поэтому предпосылки возмещения не собраны и "
            "без ограничения. Модель обязана выдать оба вывода сразу: возмещение не положено по "
            "доказательствам и ограничено по закону. Пропуск давности разбирает модель исковой "
            "давности."
        ),
        facts={
            "obligation_exists": True,
            "breach_established": True,
            "performance_tendered": False,
            "subject_conforms": False,
            "quality_quantity_conform": False,
            "performance_at_due_time": False,
            "performance_at_proper_place": False,
            "performance_to_proper_recipient": False,
            "debtor_requested_authority_proof": False,
            "authority_proof_provided": False,
            "partial_performance_tendered": False,
            "partial_performance_allowed": False,
            "monetary_obligation": False,
            "all_parties_acting_in_business": False,
            "early_performance_tendered": False,
            "early_performance_allowed": False,
            "third_party_performance_tendered": False,
            "debtor_assigned_third_party_performance": False,
            "debtor_monetary_delay": False,
            "third_party_property_right_at_risk": False,
            "personal_performance_required": False,
            "demand_obligation": False,
            "creditor_demand_delivered": False,
            "statutory_or_agreed_grace_elapsed": False,
            "creditor_prerequisite_action_required": False,
            "creditor_prerequisite_action_completed": False,
            "payment_received_by_creditor_bank": False,
            "multiple_homogeneous_debts": False,
            "debtor_designated_debt": False,
            "debt_designation_valid": False,
            "payment_insufficient": False,
            "extra_expenses_caused_by_creditor": False,
            "alternative_obligation": False,
            "choice_holder_selected": False,
            "facultative_obligation": False,
            "facultative_substitute_tendered": False,
            "multiple_debtors": False,
            "solidarity_by_law_or_contract": False,
            "joint_business_obligation": False,
            "one_solidary_debtor_performed_full": False,
            "creditor_claimed_one_solidary_debtor": False,
            "internal_recourse_shares_proven": False,
            "reciprocal_obligations": False,
            "counterperformance_due": False,
            "counterparty_failed_due_performance": False,
            "clear_future_nonperformance": False,
            "suspension_notice_delivered": False,
            "refusal_notice_delivered": False,
            "own_counterperformance_tendered": False,
            "specific_claim_override": False,
            "loss_claimed": True,
            "actual_loss_proven": False,
            "lost_profit_claimed": True,
            "lost_profit_measures_proven": False,
            "causation_proven": False,
            "reasonable_amount_basis": True,
            "exact_amount_not_established": False,
            "creditor_mitigation_taken": True,
            "creditor_contributed_to_loss": False,
            "replacement_transaction_made": False,
            "replacement_transaction_reasonable": False,
            "current_price_available": False,
            "specific_performance_claimed": False,
            "performance_objectively_possible": False,
            "creditor_lost_interest_due_delay": False,
            "substitute_performance_by_creditor": False,
            "substitute_costs_reasonable_documented": False,
            "individual_specific_thing_due": False,
            "thing_transferred_to_protected_third_party": False,
            "monetary_delay": False,
            "article_395_claimed": False,
            "penalty_for_same_monetary_delay": False,
            "article_395_contract_override": False,
            "statutory_rate_basis_proven": False,
            "interest_period_proven": False,
            "damages_above_interest_claimed": False,
            "damages_above_interest_proven": False,
            "third_party_caused_breach": False,
            "debtor_responsible_for_third_party": False,
            "primary_debtor_claimed": False,
            "primary_refused_or_no_response": False,
            "subsidiary_debtor_claimed": False,
            "liability_limit_clause_or_law": True,
            "intentional_breach": False,
            "advance_intentional_liability_exclusion": False,
            "debtor_delay": False,
            "creditor_refused_proper_performance": False,
            "creditor_omitted_required_action": False,
            "creditor_delay_loss_proven": False,
            "indemnity_agreement": False,
            "indemnity_business_context": False,
            "indemnity_clear": False,
            "indemnity_trigger_unrelated_to_breach": False,
            "indemnity_loss_occurred": False,
            "indemnity_amount_or_method_agreed": False,
            "indemnity_bad_faith_event_caused": False,
        },
        expected_conclusions={
            "damages_prerequisites_satisfied": False,
            "lost_profit_supported": False,
            "liability_limit_issue": True,
        },
    ),
    RealCaseScenario(
        case_id="a33-9999-2023-cass-avs-133159",
        case_number="А33-9999/2023",
        institute="invalidity",
        court_holding_ru=(
            "Передача земельных участков по соглашению об отступном одобрена решениями "
            "внеочередного собрания участников общества, направлена на погашение кредиторской "
            "задолженности, рыночная стоимость подтверждена отчётом оценщика. Процедура "
            "согласования соблюдена, доказательств занижения цены и ущерба обществу нет; в иске о "
            "признании сделок недействительными отказано."
        ),
        mapping_note_ru=(
            "Проверка на ложное срабатывание в институте, где оснований недействительности больше "
            "пятидесяти. Одобрение собранием переведено как отсутствие порока согласия: "
            "`required_consent_absent` — False. Явный ущерб обществу и осведомлённость контрагента "
            "о нём — отдельные предикаты, и оба отвергнуты судом. Модель обязана прийти к тому, "
            "что сделка сохраняет силу, не найдя ни одного из оснований."
        ),
        facts={
            "transaction_concluded": True,
            "invalidity_claim_made": True,
            "claimant_is_transaction_party": False,
            "claimant_legally_authorized": False,
            "claimant_rights_or_interests_affected": True,
            "court_decision_entered_into_force": True,
            "nullity_consequences_requested": False,
            "nullity_legal_interest_proven": False,
            "good_faith_reliance_created": False,
            "party_confirmed_voidable_transaction": False,
            "ground_known_at_confirmation": False,
            "performance_accepted_under_entrepreneurial_contract": False,
            "claimant_did_not_reciprocate_performance": False,
            "claimant_knew_ground_at_performance_acceptance": False,
            "performance_violates_third_party_or_public_interests": False,
            "violates_law": False,
            "public_interests_or_third_rights_affected": False,
            "law_expressly_makes_void": False,
            "immoral_purpose_proven": False,
            "both_parties_intentional_immoral_purpose": False,
            "sham_intent_proven": False,
            "feigned_intent_proven": False,
            "disguised_transaction_identified": False,
            "incapacitated_person_transaction": False,
            "minor_under_14_transaction": False,
            "benefit_to_incapacitated_or_minor_proven": False,
            "required_consent_absent": False,
            "counterparty_knew_consent_absent": False,
            "authority_restriction_violated": False,
            "counterparty_knew_authority_restriction": False,
            "entity_beyond_statutory_purpose": False,
            "counterparty_knew_beyond_purpose": False,
            "obvious_entity_damage_proven": False,
            "counterparty_knew_obvious_damage": False,
            "material_mistake_proven": False,
            "mistake_risk_assumed": False,
            "deception_proven": False,
            "violence_or_threat_proven": False,
            "adverse_circumstances_proven": False,
            "extremely_unfavorable_terms_proven": False,
            "counterparty_exploited_circumstances": False,
            "unable_to_understand_actions_proven": False,
            "limited_capacity_without_consent": False,
            "minor_14_18_without_consent": False,
            "execution_started": False,
            "void_limitation_period_expired": False,
            "voidable_limitation_period_expired": False,
            "invalid_part_separable": False,
            "remainder_preserves_transaction_purpose": False,
            "party_a_performed": False,
            "party_b_performed": False,
            "return_in_kind_possible": False,
            "value_of_performance_proven": False,
            "additional_damages_claimed": False,
            "additional_damages_causally_linked": False,
            "statutory_disposal_prohibition_violated": False,
            "judicial_disposal_prohibition_violated": False,
            "acquirer_knew_of_disposal_prohibition": False,
        },
        expected_conclusions={
            "consent_voidable_ground": False,
            "voidable_ground_detected": False,
            "void_ground_detected": False,
            "transaction_presumed_effective": True,
            "contractual_effect_displaced": False,
        },
    ),
    RealCaseScenario(
        case_id="a51-21000-2015-cass-adv-139014",
        case_number="А51-21000/2015",
        institute="invalidity",
        court_holding_ru=(
            "Договоры купли-продажи лечебно-профилактических комплексов одобрены финансовым "
            "управляющим, заключены уполномоченным директором и направлены на погашение "
            "задолженности перед банком; обеспечительные меры к моменту торгов отменены, "
            "контрагенты заинтересованными лицами не являлись, нарушений при проведении торгов не "
            "допущено. В признании сделок и торгов недействительными отказано."
        ),
        mapping_note_ru=(
            "Дело повторяет конфигурацию предикатов дела А33-9999/2023: ни одно из оснований "
            "недействительности не установлено, и сделка сохраняет силу. Совпадение записано "
            "намеренно — оно показывает, что в выгрузке несколько дел об оспаривании сделок "
            "сводятся к одному набору фактов «порока нет». Отмена обеспечительных мер к моменту "
            "торгов и незаинтересованность контрагентов отдельных предикатов не имеют: в модели "
            "нет понятия обеспечительной меры."
        ),
        facts={
            "transaction_concluded": True,
            "invalidity_claim_made": True,
            "claimant_is_transaction_party": False,
            "claimant_legally_authorized": False,
            "claimant_rights_or_interests_affected": True,
            "court_decision_entered_into_force": True,
            "nullity_consequences_requested": False,
            "nullity_legal_interest_proven": False,
            "good_faith_reliance_created": False,
            "party_confirmed_voidable_transaction": False,
            "ground_known_at_confirmation": False,
            "performance_accepted_under_entrepreneurial_contract": False,
            "claimant_did_not_reciprocate_performance": False,
            "claimant_knew_ground_at_performance_acceptance": False,
            "performance_violates_third_party_or_public_interests": False,
            "violates_law": False,
            "public_interests_or_third_rights_affected": False,
            "law_expressly_makes_void": False,
            "immoral_purpose_proven": False,
            "both_parties_intentional_immoral_purpose": False,
            "sham_intent_proven": False,
            "feigned_intent_proven": False,
            "disguised_transaction_identified": False,
            "incapacitated_person_transaction": False,
            "minor_under_14_transaction": False,
            "benefit_to_incapacitated_or_minor_proven": False,
            "required_consent_absent": False,
            "counterparty_knew_consent_absent": False,
            "authority_restriction_violated": False,
            "counterparty_knew_authority_restriction": False,
            "entity_beyond_statutory_purpose": False,
            "counterparty_knew_beyond_purpose": False,
            "obvious_entity_damage_proven": False,
            "counterparty_knew_obvious_damage": False,
            "material_mistake_proven": False,
            "mistake_risk_assumed": False,
            "deception_proven": False,
            "violence_or_threat_proven": False,
            "adverse_circumstances_proven": False,
            "extremely_unfavorable_terms_proven": False,
            "counterparty_exploited_circumstances": False,
            "unable_to_understand_actions_proven": False,
            "limited_capacity_without_consent": False,
            "minor_14_18_without_consent": False,
            "execution_started": False,
            "void_limitation_period_expired": False,
            "voidable_limitation_period_expired": False,
            "invalid_part_separable": False,
            "remainder_preserves_transaction_purpose": False,
            "party_a_performed": False,
            "party_b_performed": False,
            "return_in_kind_possible": False,
            "value_of_performance_proven": False,
            "additional_damages_claimed": False,
            "additional_damages_causally_linked": False,
            "statutory_disposal_prohibition_violated": False,
            "judicial_disposal_prohibition_violated": False,
            "acquirer_knew_of_disposal_prohibition": False,
        },
        expected_conclusions={
            "voidable_ground_detected": False,
            "void_ground_detected": False,
            "transaction_presumed_effective": True,
        },
    ),
    RealCaseScenario(
        case_id="a75-15673-2023-cass-azs-216426",
        case_number="А75-15673/2023",
        institute="invalidity",
        court_holding_ru=(
            "Прокурор требовал признать недействительным договор купли-продажи автомобиля "
            "муниципальным унитарным предприятием как крупную сделку без согласия собственника. По "
            "пункту 2 статьи 173.1 ГК РФ такая сделка может быть признана недействительной только "
            "если доказано, что другая сторона знала или должна была знать об отсутствии согласия. "
            "Осведомлённость общества не доказана, а на момент сделки действовало согласие "
            "собственника; в иске отказано."
        ),
        mapping_note_ru=(
            "Самая точная проверка правила о согласии во всём наборе. Отсутствие согласия здесь "
            "заявлено и переведено как `required_consent_absent` — True, но одного этого мало: "
            "оспоримость возникает только вместе с осведомлённостью контрагента, и "
            "`counterparty_knew_consent_absent` — False. Разница с делами А33-9999/2023 и "
            "А51-21000/2015 именно в первом предикате: там согласие было, здесь спор шёл о его "
            "отсутствии — и всё равно основание не собралось."
        ),
        facts={
            "transaction_concluded": True,
            "invalidity_claim_made": True,
            "claimant_is_transaction_party": False,
            "claimant_legally_authorized": False,
            "claimant_rights_or_interests_affected": True,
            "court_decision_entered_into_force": True,
            "nullity_consequences_requested": False,
            "nullity_legal_interest_proven": False,
            "good_faith_reliance_created": False,
            "party_confirmed_voidable_transaction": False,
            "ground_known_at_confirmation": False,
            "performance_accepted_under_entrepreneurial_contract": False,
            "claimant_did_not_reciprocate_performance": False,
            "claimant_knew_ground_at_performance_acceptance": False,
            "performance_violates_third_party_or_public_interests": False,
            "violates_law": False,
            "public_interests_or_third_rights_affected": False,
            "law_expressly_makes_void": False,
            "immoral_purpose_proven": False,
            "both_parties_intentional_immoral_purpose": False,
            "sham_intent_proven": False,
            "feigned_intent_proven": False,
            "disguised_transaction_identified": False,
            "incapacitated_person_transaction": False,
            "minor_under_14_transaction": False,
            "benefit_to_incapacitated_or_minor_proven": False,
            "required_consent_absent": True,
            "counterparty_knew_consent_absent": False,
            "authority_restriction_violated": False,
            "counterparty_knew_authority_restriction": False,
            "entity_beyond_statutory_purpose": False,
            "counterparty_knew_beyond_purpose": False,
            "obvious_entity_damage_proven": False,
            "counterparty_knew_obvious_damage": False,
            "material_mistake_proven": False,
            "mistake_risk_assumed": False,
            "deception_proven": False,
            "violence_or_threat_proven": False,
            "adverse_circumstances_proven": False,
            "extremely_unfavorable_terms_proven": False,
            "counterparty_exploited_circumstances": False,
            "unable_to_understand_actions_proven": False,
            "limited_capacity_without_consent": False,
            "minor_14_18_without_consent": False,
            "execution_started": False,
            "void_limitation_period_expired": False,
            "voidable_limitation_period_expired": False,
            "invalid_part_separable": False,
            "remainder_preserves_transaction_purpose": False,
            "party_a_performed": False,
            "party_b_performed": False,
            "return_in_kind_possible": False,
            "value_of_performance_proven": False,
            "additional_damages_claimed": False,
            "additional_damages_causally_linked": False,
            "statutory_disposal_prohibition_violated": False,
            "judicial_disposal_prohibition_violated": False,
            "acquirer_knew_of_disposal_prohibition": False,
        },
        expected_conclusions={
            "consent_voidable_ground": False,
            "voidable_ground_detected": False,
            "transaction_presumed_effective": True,
        },
    ),
    RealCaseScenario(
        case_id="a55-19956-2022-cass-apv-227301",
        case_number="А55-19956/2022",
        institute="invalidity",
        court_holding_ru=(
            "Внесение долей в нежилых помещениях в качестве вклада в имущество акционерного "
            "общества оспаривалось кредитором акционера как мнимая сделка. Действия сторон были "
            "последовательными и экономически оправданными, общество реально использует переданное "
            "имущество, сдавая его в аренду. Признаков злоупотребления правом нет, "
            "преимущественное право покупки к внесению вклада не применяется; в иске отказано."
        ),
        mapping_note_ru=(
            "Мнимость в модели — самостоятельное основание ничтожности, и опровергается она одним "
            "фактом: стороны исполнили сделку по-настоящему. Реальное использование имущества "
            "обществом переведено как `sham_intent_proven` — False. Довод о преимущественном праве "
            "покупки предикатов не имеет: это правило общей долевой собственности, а не основание "
            "недействительности."
        ),
        facts={
            "transaction_concluded": True,
            "invalidity_claim_made": True,
            "claimant_is_transaction_party": False,
            "claimant_legally_authorized": False,
            "claimant_rights_or_interests_affected": True,
            "court_decision_entered_into_force": True,
            "nullity_consequences_requested": False,
            "nullity_legal_interest_proven": False,
            "good_faith_reliance_created": False,
            "party_confirmed_voidable_transaction": False,
            "ground_known_at_confirmation": False,
            "performance_accepted_under_entrepreneurial_contract": False,
            "claimant_did_not_reciprocate_performance": False,
            "claimant_knew_ground_at_performance_acceptance": False,
            "performance_violates_third_party_or_public_interests": False,
            "violates_law": False,
            "public_interests_or_third_rights_affected": False,
            "law_expressly_makes_void": False,
            "immoral_purpose_proven": False,
            "both_parties_intentional_immoral_purpose": False,
            "sham_intent_proven": False,
            "feigned_intent_proven": False,
            "disguised_transaction_identified": False,
            "incapacitated_person_transaction": False,
            "minor_under_14_transaction": False,
            "benefit_to_incapacitated_or_minor_proven": False,
            "required_consent_absent": False,
            "counterparty_knew_consent_absent": False,
            "authority_restriction_violated": False,
            "counterparty_knew_authority_restriction": False,
            "entity_beyond_statutory_purpose": False,
            "counterparty_knew_beyond_purpose": False,
            "obvious_entity_damage_proven": False,
            "counterparty_knew_obvious_damage": False,
            "material_mistake_proven": False,
            "mistake_risk_assumed": False,
            "deception_proven": False,
            "violence_or_threat_proven": False,
            "adverse_circumstances_proven": False,
            "extremely_unfavorable_terms_proven": False,
            "counterparty_exploited_circumstances": False,
            "unable_to_understand_actions_proven": False,
            "limited_capacity_without_consent": False,
            "minor_14_18_without_consent": False,
            "execution_started": False,
            "void_limitation_period_expired": False,
            "voidable_limitation_period_expired": False,
            "invalid_part_separable": False,
            "remainder_preserves_transaction_purpose": False,
            "party_a_performed": False,
            "party_b_performed": False,
            "return_in_kind_possible": False,
            "value_of_performance_proven": False,
            "additional_damages_claimed": False,
            "additional_damages_causally_linked": False,
            "statutory_disposal_prohibition_violated": False,
            "judicial_disposal_prohibition_violated": False,
            "acquirer_knew_of_disposal_prohibition": False,
        },
        expected_conclusions={
            "sham_void_ground": False,
            "void_ground_detected": False,
            "transaction_presumed_effective": True,
        },
    ),
    RealCaseScenario(
        case_id="a59-4738-2023-cass-adv-139015",
        case_number="А59-4738/2023",
        institute="invalidity",
        court_holding_ru=(
            "Таможенный орган оспаривал договор купли-продажи судна от 01.06.2010 как направленный "
            "на незаконный вывод денежных средств. Суды признали сделку реальной, возмездной и "
            "исполненной, действительная воля сторон была направлена на приобретение судна. "
            "Оснований по статьям 10, 167, 168, 169 и 170 ГК РФ не установлено, кроме того истцом "
            "пропущен срок исковой давности."
        ),
        mapping_note_ru=(
            "Единственное дело набора, где истечение срока оспаривания ничтожной сделки "
            "установлено прямо: `void_limitation_period_expired` — True. Проверяется, что этот "
            "факт сам по себе закрывает применение последствий недействительности, даже если бы "
            "основание нашлось, — а здесь оно ещё и не найдено. Сделка исполнена обеими сторонами, "
            "но реституция не наступает, потому что нет вытеснения договорного эффекта: возвращать "
            "нечего, когда сделка сохраняет силу."
        ),
        facts={
            "transaction_concluded": True,
            "invalidity_claim_made": True,
            "claimant_is_transaction_party": False,
            "claimant_legally_authorized": False,
            "claimant_rights_or_interests_affected": True,
            "court_decision_entered_into_force": True,
            "nullity_consequences_requested": True,
            "nullity_legal_interest_proven": False,
            "good_faith_reliance_created": False,
            "party_confirmed_voidable_transaction": False,
            "ground_known_at_confirmation": False,
            "performance_accepted_under_entrepreneurial_contract": False,
            "claimant_did_not_reciprocate_performance": False,
            "claimant_knew_ground_at_performance_acceptance": False,
            "performance_violates_third_party_or_public_interests": False,
            "violates_law": False,
            "public_interests_or_third_rights_affected": False,
            "law_expressly_makes_void": False,
            "immoral_purpose_proven": False,
            "both_parties_intentional_immoral_purpose": False,
            "sham_intent_proven": False,
            "feigned_intent_proven": False,
            "disguised_transaction_identified": False,
            "incapacitated_person_transaction": False,
            "minor_under_14_transaction": False,
            "benefit_to_incapacitated_or_minor_proven": False,
            "required_consent_absent": False,
            "counterparty_knew_consent_absent": False,
            "authority_restriction_violated": False,
            "counterparty_knew_authority_restriction": False,
            "entity_beyond_statutory_purpose": False,
            "counterparty_knew_beyond_purpose": False,
            "obvious_entity_damage_proven": False,
            "counterparty_knew_obvious_damage": False,
            "material_mistake_proven": False,
            "mistake_risk_assumed": False,
            "deception_proven": False,
            "violence_or_threat_proven": False,
            "adverse_circumstances_proven": False,
            "extremely_unfavorable_terms_proven": False,
            "counterparty_exploited_circumstances": False,
            "unable_to_understand_actions_proven": False,
            "limited_capacity_without_consent": False,
            "minor_14_18_without_consent": False,
            "execution_started": True,
            "void_limitation_period_expired": True,
            "voidable_limitation_period_expired": False,
            "invalid_part_separable": False,
            "remainder_preserves_transaction_purpose": False,
            "party_a_performed": True,
            "party_b_performed": True,
            "return_in_kind_possible": True,
            "value_of_performance_proven": False,
            "additional_damages_claimed": False,
            "additional_damages_causally_linked": False,
            "statutory_disposal_prohibition_violated": False,
            "judicial_disposal_prohibition_violated": False,
            "acquirer_knew_of_disposal_prohibition": False,
        },
        expected_conclusions={
            "void_ground_detected": False,
            "nullity_consequences_prerequisites": False,
            "transaction_presumed_effective": True,
            "restitution_required": False,
        },
    ),
    RealCaseScenario(
        case_id="a43-11257-2024-cass-avv-128073",
        case_number="А43-11257/2024",
        institute="invalidity",
        court_holding_ru=(
            "Земельный участок продан с публичных торгов при действующем запрете на его "
            "отчуждение, наложенном определением суда по делу о банкротстве. Правовым последствием "
            "сделки, совершённой после принятия обеспечительных мер, является не её ничтожность, а "
            "возникновение у кредитора прав залогодержателя при осведомлённости приобретателя о "
            "запрете. Существенных нарушений порядка торгов не установлено; в иске отказано."
        ),
        mapping_note_ru=(
            "Дело, которым закрыт открытый вопрос о нарушении запрета с иным законным "
            "последствием. Прежде перевод обходил модель: `violates_law` ставился в False, хотя "
            "запрет был нарушен, — иначе модель вывела бы оспоримость там, где закон её прямо "
            "исключает. Обход держался на том, что переводчик знал, какие запреты ведут к "
            "недействительности, а какие нет. Теперь этого знания от него не требуется: "
            "`violates_law` поставлен в True честно, а `judicial_disposal_prohibition_violated` "
            "называет запрет пунктом 2 статьи 174.1, и модель сама снимает основания статьи 168. "
            "Запрет наложен определением суда в пользу кредитора — это пункт 2, а не пункт 1: "
            "запрет из закона дал бы ничтожность в части. Осведомлённость приобретателя суд "
            "условием назвал, но не установил — иск отклонён по другому основанию, — поэтому "
            "предикат оставлен в False, и права кредитора против приобретателя модель не выводит."
        ),
        facts={
            "transaction_concluded": True,
            "invalidity_claim_made": True,
            "claimant_is_transaction_party": False,
            "claimant_legally_authorized": False,
            "claimant_rights_or_interests_affected": True,
            "court_decision_entered_into_force": True,
            "nullity_consequences_requested": False,
            "nullity_legal_interest_proven": False,
            "good_faith_reliance_created": False,
            "party_confirmed_voidable_transaction": False,
            "ground_known_at_confirmation": False,
            "performance_accepted_under_entrepreneurial_contract": False,
            "claimant_did_not_reciprocate_performance": False,
            "claimant_knew_ground_at_performance_acceptance": False,
            "performance_violates_third_party_or_public_interests": False,
            "violates_law": True,
            "public_interests_or_third_rights_affected": False,
            "law_expressly_makes_void": False,
            "immoral_purpose_proven": False,
            "both_parties_intentional_immoral_purpose": False,
            "sham_intent_proven": False,
            "feigned_intent_proven": False,
            "disguised_transaction_identified": False,
            "incapacitated_person_transaction": False,
            "minor_under_14_transaction": False,
            "benefit_to_incapacitated_or_minor_proven": False,
            "required_consent_absent": False,
            "counterparty_knew_consent_absent": False,
            "authority_restriction_violated": False,
            "counterparty_knew_authority_restriction": False,
            "entity_beyond_statutory_purpose": False,
            "counterparty_knew_beyond_purpose": False,
            "obvious_entity_damage_proven": False,
            "counterparty_knew_obvious_damage": False,
            "material_mistake_proven": False,
            "mistake_risk_assumed": False,
            "deception_proven": False,
            "violence_or_threat_proven": False,
            "adverse_circumstances_proven": False,
            "extremely_unfavorable_terms_proven": False,
            "counterparty_exploited_circumstances": False,
            "unable_to_understand_actions_proven": False,
            "limited_capacity_without_consent": False,
            "minor_14_18_without_consent": False,
            "execution_started": False,
            "void_limitation_period_expired": False,
            "voidable_limitation_period_expired": False,
            "invalid_part_separable": False,
            "remainder_preserves_transaction_purpose": False,
            "party_a_performed": False,
            "party_b_performed": False,
            "return_in_kind_possible": False,
            "value_of_performance_proven": False,
            "additional_damages_claimed": False,
            "additional_damages_causally_linked": False,
            "statutory_disposal_prohibition_violated": False,
            "judicial_disposal_prohibition_violated": True,
            "acquirer_knew_of_disposal_prohibition": False,
        },
        expected_conclusions={
            "unlawful_void_ground": False,
            "unlawful_voidable_ground": False,
            "void_ground_detected": False,
            "transaction_presumed_effective": True,
            "judicial_prohibition_does_not_void": True,
            "secured_creditor_rights_survive": False,
        },
    ),
    RealCaseScenario(
        case_id="a40-19629-14-142-170-cass-ams-221014",
        case_number="А40-19629/14-142-170",
        institute="invalidity",
        court_holding_ru=(
            "Нежилое помещение в доме священника при церкви относится к имуществу религиозного "
            "назначения. По пункту 2 статьи 129 ГК РФ такие объекты ограничены в обороте и могут "
            "отчуждаться только в собственность религиозных организаций, поэтому договор с иным "
            "лицом ничтожен. Иск удовлетворён, стороны обязаны возвратить друг другу полученное по "
            "сделке."
        ),
        mapping_note_ru=(
            "Единственное дело набора, где ничтожность выведена из нарушения закона, а не из "
            "порока субъекта: `violates_law` вместе с затронутым публичным интересом и прямым "
            "указанием закона на ничтожность. Двусторонняя реституция ожидается в натуре — "
            "помещение возвращается продавцу, деньги покупателю, — поэтому денежная оценка "
            "исполнения не требуется. Истец стороной сделки не является: религиозная организация "
            "стоит в споре по охраняемому законом интересу."
        ),
        facts={
            "transaction_concluded": True,
            "invalidity_claim_made": True,
            "claimant_is_transaction_party": False,
            "claimant_legally_authorized": False,
            "claimant_rights_or_interests_affected": True,
            "court_decision_entered_into_force": True,
            "nullity_consequences_requested": True,
            "nullity_legal_interest_proven": True,
            "good_faith_reliance_created": False,
            "party_confirmed_voidable_transaction": False,
            "ground_known_at_confirmation": False,
            "performance_accepted_under_entrepreneurial_contract": False,
            "claimant_did_not_reciprocate_performance": False,
            "claimant_knew_ground_at_performance_acceptance": False,
            "performance_violates_third_party_or_public_interests": False,
            "violates_law": True,
            "public_interests_or_third_rights_affected": True,
            "law_expressly_makes_void": True,
            "immoral_purpose_proven": False,
            "both_parties_intentional_immoral_purpose": False,
            "sham_intent_proven": False,
            "feigned_intent_proven": False,
            "disguised_transaction_identified": False,
            "incapacitated_person_transaction": False,
            "minor_under_14_transaction": False,
            "benefit_to_incapacitated_or_minor_proven": False,
            "required_consent_absent": False,
            "counterparty_knew_consent_absent": False,
            "authority_restriction_violated": False,
            "counterparty_knew_authority_restriction": False,
            "entity_beyond_statutory_purpose": False,
            "counterparty_knew_beyond_purpose": False,
            "obvious_entity_damage_proven": False,
            "counterparty_knew_obvious_damage": False,
            "material_mistake_proven": False,
            "mistake_risk_assumed": False,
            "deception_proven": False,
            "violence_or_threat_proven": False,
            "adverse_circumstances_proven": False,
            "extremely_unfavorable_terms_proven": False,
            "counterparty_exploited_circumstances": False,
            "unable_to_understand_actions_proven": False,
            "limited_capacity_without_consent": False,
            "minor_14_18_without_consent": False,
            "execution_started": True,
            "void_limitation_period_expired": False,
            "voidable_limitation_period_expired": False,
            "invalid_part_separable": False,
            "remainder_preserves_transaction_purpose": False,
            "party_a_performed": True,
            "party_b_performed": True,
            "return_in_kind_possible": True,
            "value_of_performance_proven": False,
            "additional_damages_claimed": False,
            "additional_damages_causally_linked": False,
            "statutory_disposal_prohibition_violated": False,
            "judicial_disposal_prohibition_violated": False,
            "acquirer_knew_of_disposal_prohibition": False,
        },
        expected_conclusions={
            "unlawful_void_ground": True,
            "void_ground_detected": True,
            "contractual_effect_displaced": True,
            "restitution_required": True,
            "restitution_in_kind": True,
            "nullity_consequences_prerequisites": True,
        },
    ),
    RealCaseScenario(
        case_id="a32-52528-2022-cass-ask-214685",
        case_number="А32-52528/2022",
        institute="civil_principles",
        court_holding_ru=(
            "Факт поставки товара через цепочку третьих лиц подтверждён товарной накладной, "
            "подписанной директором истца с печатью, поэтому оснований для возврата предоплаты "
            "нет. Уклонение директора истца от явки в суд и представление недостоверных сведений "
            "расценены как злоупотребление правом, что является самостоятельным основанием для "
            "отказа в иске (статья 10 ГК РФ)."
        ),
        mapping_note_ru=(
            "Злоупотребление правом здесь — второе основание отказа рядом с первым, доказанной "
            "поставкой, и в предикатах остаётся только оно: доказанность поставки разбирает модель "
            "поставки. `protection_refusal_not_applied` — False, потому что отказ в защите как раз "
            "применён; предикат сформулирован от обратного, и знак в нём легко перепутать. "
            "Процессуальное поведение стороны в предикаты не переводится — в модель попадает его "
            "материальный результат."
        ),
        facts={
            "civil_rights_exercise_asserted": True,
            "good_faith_principle_breached": True,
            "equality_or_freedom_principle_breached": False,
            "rights_arising_grounds_breached": False,
            "abuse_of_right_established": True,
            "protection_refusal_not_applied": False,
            "protection_methods_breached": False,
            "self_help_limits_breached": False,
            "damages_compensation_rules_breached": False,
            "public_authority_liability_breached": False,
        },
        expected_conclusions={
            "abuse_of_right_detected": True,
            "good_faith_duty_breached": True,
            "protection_refusal_breached": False,
            "civil_principles_qualified": True,
        },
    ),
    RealCaseScenario(
        case_id="a55-20451-2025-cass-apv-247074",
        case_number="А55-20451/2025",
        institute="civil_principles",
        court_holding_ru=(
            "Стороны обменивались сканами договора поставки, но оригинал не направлялся и через "
            "электронный документооборот договор не загружался; переговоры приостановились, "
            "требований полтора года не предъявлялось. Договор признан незаключённым, а требование "
            "штрафа по несуществующему обязательству — злоупотреблением правом, поэтому в защите "
            "права отказано полностью на основании статьи 10 ГК РФ."
        ),
        mapping_note_ru=(
            "Третье дело о злоупотреблении правом, и в предикатах оно совпадает с делами "
            "А45-3827/2019 и А32-52528/2022. Совпадение записано намеренно: три разных фабулы — "
            "банкротное требование аффилированного кредитора, уклонение директора от явки и штраф "
            "по незаключённому договору — дают модели один и тот же набор фактов. Это говорит о "
            "грубости модели начал гражданского права, а не о сходстве споров, и признать это "
            "честнее, чем изобретать различие, которого в предикатах нет."
        ),
        facts={
            "civil_rights_exercise_asserted": True,
            "good_faith_principle_breached": True,
            "equality_or_freedom_principle_breached": False,
            "rights_arising_grounds_breached": False,
            "abuse_of_right_established": True,
            "protection_refusal_not_applied": False,
            "protection_methods_breached": False,
            "self_help_limits_breached": False,
            "damages_compensation_rules_breached": False,
            "public_authority_liability_breached": False,
        },
        expected_conclusions={
            "abuse_of_right_detected": True,
            "good_faith_duty_breached": True,
            "protection_refusal_breached": False,
            "civil_principles_qualified": True,
        },
    ),
    RealCaseScenario(
        case_id="a55-27686-2023-cass-apv-236669",
        case_number="А55-27686/2023",
        institute="terms",
        court_holding_ru=(
            "Обязательства по договору технологического присоединения прекратились 11.11.2013 в "
            "связи с истечением срока действия технических условий. Начало течения срока исковой "
            "давности исчислено с 12.11.2013 по статьям 191–193 ГК РФ, окончание — 14.11.2016, "
            "поскольку 12.11.2016 приходилось на субботу. Иск подан 29.08.2023, срок пропущен, в "
            "иске отказано."
        ),
        mapping_note_ru=(
            "Дело проверяет модель исчисления сроков на ложное срабатывание в самой её тонкой "
            "части — переносе окончания срока с выходного дня на следующий рабочий (статья 193 ГК "
            "РФ). Суд применил правило и не ошибся, поэтому все предикаты нарушений остаются в "
            "False, и модель обязана не найти порока там, где расчёт верен. Сам пропуск срока — "
            "вывод модели исковой давности, а не этой: здесь проверяется правильность исчисления, "
            "а не последствие пропуска."
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
            "non_working_day_duty_breached": False,
            "term_start_duty_breached": False,
            "requires_human_terms_assessment": False,
        },
    ),
    RealCaseScenario(
        case_id="a55-6599-2023-cass-apv-236114",
        case_number="А55-6599/2023",
        institute="limitation",
        court_holding_ru=(
            "Региональный оператор взыскивал плату за обращение с твёрдыми коммунальными отходами "
            "за 2019–2023 годы. Факт оказания услуг не доказан: помещения имели черновую отделку и "
            "не использовались. По требованиям за 2019 год, кроме того, истёк срок исковой "
            "давности, о применении которой заявил ответчик, что является самостоятельным "
            "основанием для отказа."
        ),
        mapping_note_ru=(
            "Повременные платежи считаются по каждому периоду отдельно, и суд перечислил "
            "двенадцать дат начала течения срока — по одной на месяц 2019 года. Модель такой "
            "разбивки не выражает: у неё один срок на требование. Перевод сделан по отказной части "
            "целиком — общий трёхлетний срок по платежам 2019 года к подаче иска истёк. "
            "Недоказанность оказания услуг относится к модели возмездных услуг и в предикаты "
            "давности не переводится."
        ),
        facts={
            "claim_subject_to_limitation": True,
            "right_violation_and_defendant_known": True,
            "fixed_performance_term_expired": True,
            "general_three_year_term_elapsed": True,
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
            "basic_term_elapsed": True,
            "limitation_period_expired": True,
            "limitation_defense_available": True,
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
    pending_translation: list[str] = Field(default_factory=list)
    distinct_fact_configurations: int = 0
    repeated_configurations: dict[str, list[str]] = Field(default_factory=dict)
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


def fact_configurations() -> dict[tuple[str, frozenset[str]], list[str]]:
    """Сгруппировать дела по институту и набору установленных фактов.

    Пятьдесят четыре дела — не пятьдесят четыре проверки. Разные фабулы могут
    давать модели один и тот же набор предикатов: пять дел выгрузки об
    управлении домом сводятся к трём наборам, пять дел о просрочке кредитора —
    к двум, три дела о злоупотреблении правом — к одному.

    Совпадение не ошибка перевода, а свойство корпуса вместе с грубостью
    модели, и прятать его нельзя: без этой меры «сошлись все 54» звучало бы как
    54 независимых подтверждения, которых на деле меньше.
    """
    groups: dict[tuple[str, frozenset[str]], list[str]] = {}
    for scenario in REAL_CASE_SCENARIOS:
        established = frozenset(name for name, value in scenario.facts.items() if value)
        groups.setdefault((scenario.institute, established), []).append(scenario.case_number)
    return groups


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
    configurations = fact_configurations()
    repeated = {
        institute + ": " + ", ".join(sorted(established)[:3] or ["предикатов нет"]): numbers
        for (institute, established), numbers in configurations.items()
        if len(numbers) > 1
    }
    return RealCaseReport(
        total=len(results),
        passed=passed,
        failed_case_ids=[entry.case_id for entry in results if not entry.passed],
        results=results,
        unmapped_final_cases=sorted(UNMAPPED_FINAL_CASES_RU),
        pending_translation=sorted(PENDING_TRANSLATION_RU),
        distinct_fact_configurations=len(configurations),
        repeated_configurations=repeated,
        notes_ru=[
            "Ожидаемый итог взят из решения по конкретному делу, а не из текста закона "
            "в моём прочтении и не из разъяснения Пленума.",
            "Проверяется вывод одного института: дело даёт факты для него, а не для "
            "всего конвейера.",
            "Перевод фабулы в предикаты — интерпретация; там, где предикат выведен не "
            "буквально, рассуждение записано в mapping_note_ru.",
            *(
                f"Вне модели — {case_id}: {reason}"
                for case_id, reason in sorted(UNMAPPED_FINAL_CASES_RU.items())
            ),
            f"В очереди на перевод: {len(PENDING_TRANSLATION_RU)} дел с окончательным "
            f"исходом. Доля сверенных дел — {len(results)} из "
            f"{len(results) + len(PENDING_TRANSLATION_RU) + len(UNMAPPED_FINAL_CASES_RU)}."
            + (
                " Очередь названа поимённо в PENDING_TRANSLATION_RU: пока она не пуста, "
                "совпадение модели с судом измерено на части выгрузки, а не на всей."
                if PENDING_TRANSLATION_RU
                else ""
            ),
            f"Различных наборов фактов: {len(configurations)} на {len(results)} дел. "
            "Совпадающие наборы — свойство корпуса вместе с грубостью модели, а не "
            "ошибка перевода: разные фабулы могут давать одни и те же предикаты. Без "
            "этой меры «сошлись все» читалось бы как столько же независимых "
            "подтверждений, сколько дел.",
        ],
    )


class ScenarioFactGap(BaseModel):
    """Расхождение состава предикатов одного дела с контрактом данных института."""

    case_id: str
    case_number: str
    institute: str
    missing: list[str] = Field(default_factory=list)
    unknown: list[str] = Field(default_factory=list)


class ScenarioFactCoverageReport(BaseModel):
    version: str = "contracts-scenario-fact-coverage-v0"
    total: int = 0
    complete: bool = True
    gaps: list[ScenarioFactGap] = Field(default_factory=list)
    institutes_affected: list[str] = Field(default_factory=list)


def audit_scenario_fact_coverage() -> ScenarioFactCoverageReport:
    """Сверить состав предикатов каждого дела с контрактом данных его института.

    **Зачем отдельный аудит.** Институт, получивший новый предикат, ломает все
    дела своего института разом: их факты записаны явным словарём, а не через
    хелпер с умолчанием. Прежняя проверка падала на первом же деле с сообщением
    из одного `case_id` — и чинить приходилось по одному делу за
    одиннадцатиминутный прогон, не зная ни сколько дел затронуто, ни каких
    предикатов не хватает.

    Отчёт называет и то и другое сразу и стоит доли секунды: запускать его
    следует сразу после правки института, не дожидаясь полного прогона.
    """
    request = build_synthetic_supply_analysis_request()
    gaps: list[ScenarioFactGap] = []
    for scenario in REAL_CASE_SCENARIOS:
        runner = INSTITUTE_RUNNERS[scenario.institute]
        evidence = getattr(request, runner.evidence_field)
        contract = {assertion.predicate.value for assertion in evidence.assertions}
        missing = sorted(contract - scenario.facts.keys())
        unknown = sorted(scenario.facts.keys() - contract)
        if missing or unknown:
            gaps.append(
                ScenarioFactGap(
                    case_id=scenario.case_id,
                    case_number=scenario.case_number,
                    institute=scenario.institute,
                    missing=missing,
                    unknown=unknown,
                )
            )
    return ScenarioFactCoverageReport(
        total=len(REAL_CASE_SCENARIOS),
        complete=not gaps,
        gaps=gaps,
        institutes_affected=sorted({gap.institute for gap in gaps}),
    )


def render_scenario_fact_coverage_ru(report: ScenarioFactCoverageReport) -> str:
    """Отчёт об аудите по-русски — он же текст падения теста."""
    if report.complete:
        return f"Состав предикатов сходится с контрактом данных во всех {report.total} делах."
    lines = [
        f"Состав предикатов разошёлся с контрактом данных: {len(report.gaps)} дел "
        f"из {report.total}.",
        "Институты: " + ", ".join(report.institutes_affected) + ".",
        "",
    ]
    for gap in report.gaps:
        lines.append(f"{gap.case_number} ({gap.institute}, {gap.case_id}):")
        if gap.missing:
            lines.append("  не задано в деле: " + ", ".join(gap.missing))
        if gap.unknown:
            lines.append("  нет в контракте данных: " + ", ".join(gap.unknown))
    missing_by_institute = {
        institute: sorted(
            {name for gap in report.gaps if gap.institute == institute for name in gap.missing}
        )
        for institute in report.institutes_affected
    }
    for institute, names in missing_by_institute.items():
        if not names:
            continue
        lines.extend(
            [
                "",
                f"Строки для дел института «{institute}» "
                f"({len([g for g in report.gaps if g.institute == institute])} шт.):",
            ]
        )
        lines.extend(f'            "{name}": False,' for name in names)
    if any(missing_by_institute.values()):
        lines.extend(
            [
                "",
                "False здесь — предположение, а не вывод: новый предикат обычно не "
                "относится к делу, которое переводили до его появления. Проверьте "
                "по фабуле каждого дела, прежде чем вставлять.",
            ]
        )
    return "\n".join(lines)
