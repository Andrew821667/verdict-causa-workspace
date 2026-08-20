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
#: Значение — институты, в предикаты которых дело следует переводить. Они
#: вычислены по статьям, на которые сослался суд, и сужены до тех, по которым
#: набор умеет прогонять дело. Пустым этот список быть не может: дело без
#: единого такого института — это граница модели, и его место в
#: `UNMAPPED_FINAL_CASES_RU` с написанной причиной.
PENDING_TRANSLATION_RU: dict[str, tuple[str, ...]] = {
    "88-10752-2023-cass-ksoj002-108217": (
        "form", "invalidity", "property_rights", "representation", "transactions"
    ),
    "88-11704-2025-cass-ksoj008-167443": (
        "formation", "invalidity", "meeting_decisions", "performance_remedies",
        "property_rights", "termination"
    ),
    "88-11827-2023-cass-ksoj007-89604": (
        "freedom", "paid_services", "performance_remedies", "representation"
    ),
    "88-12081-2024-cass-ksoj007-119496": ("invalidity",),
    "88-12844-2024-cass-ksoj001-173181": (
        "civil_principles", "formation", "freedom", "invalidity", "meeting_decisions",
        "performance_remedies", "property_rights", "temporal_effect", "termination"
    ),
    "88-14968-2026-cass-ksoj004-253200": (
        "civil_principles", "form", "invalidity", "persons", "preliminary", "property_rights",
        "transactions"
    ),
    "88-15461-2025-cass-ksoj003-151203": (
        "formation", "meeting_decisions", "performance_remedies", "property_rights",
        "termination"
    ),
    "88-16698-2026-cass-ksoj001-256023": (
        "invalidity", "liability", "meeting_decisions", "moral_harm", "objects",
        "property_rights"
    ),
    "88-19251-2024-cass-ksoj008-144573": (
        "formation", "invalidity", "liability", "meeting_decisions", "performance_remedies",
        "property_rights", "security", "termination"
    ),
    "88-4580-2026-cass-ksoj008-184804": (
        "liability", "loan", "mandate", "representation", "security"
    ),
    "a03-19562-2024-cass-azs-218301": (
        "civil_principles", "construction_contract", "general_obligations", "interpretation",
        "liability", "obligation_dynamics", "performance_remedies", "security", "transactions",
        "work_contract"
    ),
    "a04-4768-2025-cass-adv-143671": (
        "civil_principles", "construction_contract", "performance_remedies", "sale", "security",
        "supply", "termination"
    ),
    "a12-3652-2019-cass-apv-181344": ("persons", "transactions"),
    "a19-26528-2022-cass-avs-127653": (
        "attribution_delay", "civil_principles", "liability", "performance_remedies",
        "security", "work_contract"
    ),
    "a32-52528-2022-cass-ask-214685": (
        "civil_principles", "form", "formation", "performance_remedies", "sale", "supply",
        "unjust_enrichment"
    ),
    "a33-28136-2024-cass-avs-136444": ("loan", "obligation_dynamics", "sale", "termination"),
    "a33-9999-2023-cass-avs-133159": ("invalidity",),
    "a35-3775-2020-cass-acn-151105": ("invalidity", "objects", "sale"),
    "a39-4009-2023-cass-avv-124719": (
        "formation", "freedom", "interpretation", "obligation_dynamics"
    ),
    "a40-180691-2024-cass-ams-578542": (
        "attribution_delay", "freedom", "general_obligations", "interpretation", "persons",
        "security", "terms"
    ),
    "a40-19629-14-142-170-cass-ams-221014": ("invalidity", "objects"),
    "a40-252357-2016-cass-ams-301832": ("form", "invalidity", "persons", "transactions"),
    "a40-265730-2022-cass-ams-519159": (
        "attribution_delay", "civil_principles", "lease", "liability", "performance_remedies",
        "security"
    ),
    "a40-87930-2024-cass-ams-575831": (
        "civil_principles", "general_obligations", "performance_remedies", "sale", "supply",
        "termination"
    ),
    "a41-25109-2016-cass-ams-262071": (
        "civil_principles", "form", "formation", "invalidity", "transactions"
    ),
    "a43-11257-2024-cass-avv-128073": ("invalidity", "liability", "procedure", "security"),
    "a43-1461-2023-cass-avv-129804": (
        "attribution_delay", "civil_principles", "formation", "freedom", "general_obligations",
        "liability", "performance_remedies", "property_rights", "supply", "temporal_effect"
    ),
    "a43-549-2022-cass-avv-119249": (
        "building_lease", "civil_principles", "insurance_settlement", "leasing", "liability",
        "performance_remedies", "sale", "tort_general", "work_contract"
    ),
    "a51-21000-2015-cass-adv-139014": ("civil_principles", "invalidity"),
    "a53-32148-2023-cass-ask-203585": (
        "civil_principles", "invalidity", "performance_remedies", "persons", "transactions"
    ),
    "a55-1232-2025-cass-apv-244369": (
        "attribution_delay", "construction_contract", "liability", "performance_remedies",
        "security", "work_contract"
    ),
    "a55-19956-2022-cass-apv-227301": (
        "civil_principles", "invalidity", "lease", "persons", "property_rights"
    ),
    "a55-20451-2025-cass-apv-247074": (
        "civil_principles", "formation", "general_obligations", "precontractual", "security",
        "termination"
    ),
    "a55-27686-2023-cass-apv-236669": ("limitation", "performance_remedies", "terms"),
    "a55-6599-2023-cass-apv-236114": ("limitation", "terms"),
    "a59-4738-2023-cass-adv-139015": ("civil_principles", "invalidity"),
    "a60-47243-2018-cass-aur-207691": ("form",),
    "a73-9126-2023-cass-adv-134721": ("freedom", "liability", "obligation_dynamics"),
    "a75-15673-2023-cass-azs-216426": (
        "civil_principles", "invalidity", "persons", "property_rights", "transactions"
    ),
    "a75-15705-2025-cass-azs-221575": (
        "attribution_delay", "civil_principles", "freedom", "general_obligations", "liability",
        "paid_services", "performance_remedies", "sale", "security", "state_supply", "supply",
        "work_contract"
    ),
    "a79-3098-2023-cass-avv-128859": ("civil_principles", "invalidity", "obligation_dynamics"),
    "a82-7717-2024-cass-avv-131271": (
        "civil_principles", "energy_supply", "liability", "limitation", "performance_remedies"
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
        pending_translation=sorted(PENDING_TRANSLATION_RU),
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
            f"{len(results) + len(PENDING_TRANSLATION_RU) + len(UNMAPPED_FINAL_CASES_RU)}. "
            "Очередь названа поимённо в PENDING_TRANSLATION_RU: пока она не пуста, "
            "совпадение модели с судом измерено на части выгрузки, а не на всей.",
        ],
    )
