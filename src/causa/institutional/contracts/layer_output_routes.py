"""Аудит связности по выводам: куда идёт каждый вывод института, питающего слой.

## Зачем второй уровень

[Аудит связности](layer_connectivity.py) отвечает, **питает ли институт** слой
общих положений. Он не отвечает, доходит ли до слоя **каждый** вывод института,
меняющий судьбу требования. Разница проявилась на `attribution_delay`: институт
питал слой с выпуска 1.0.0, а исключение статьи 403 ГК РФ — закон возлагает
ответственность на непосредственного исполнителя — оставалось при институте до
выпуска 1.31.0, и никто его не называл.

Здесь записан маршрут каждого вывода шестнадцати питающих институтов.

## Что вычисляется, а что записано

Два маршрута не записываются вручную, а **вычисляются** из кода, чтобы запись не
могла с ним разойтись:

* **в слой** — поля оценки, которые читает `build_general_effects_inputs`;
  определяются по обращениям к атрибутам при сборке входов;
* **составляющая** — выводы, от которых по объявленным правилам института
  зависит (прямо или через другие выводы) хотя бы один вывод, идущий в слой.

Всё остальное записано в `LAYER_OUTPUT_ROUTES` с маршрутом и причиной. Тест
требует, чтобы запись покрывала ровно остаток — не больше и не меньше, — чтобы
причина маршрута «через другой вход» называла настоящий вход слоя и чтобы
открытый долг совпадал с закреплённым перечнем.

## Маршруты

`OutputRoute.VIA_INPUT`
    Тот же правовой результат приходит в слой другим входом. Причина называет
    вход. Если связь держится на том, что рецензент отметит последствие отдельным
    признаком, это сказано прямо: сверки между блоками нет.

`OutputRoute.DEFAULT`
    Вывод совпадает с умолчанием слоя: договор действует, должник отвечает,
    обязательство не прекращено. Провести его — ничего не изменить.

`OutputRoute.REMEDY`
    Средство защиты, размер, форма возврата или порядок требования, а не судьба
    требования. Слой выводит последствия, а не считает суммы.

`OutputRoute.EVIDENCE`
    Правило о доказательствах, пробел доказательств или сигнал о противоречивых
    данных внутри института.

`OutputRoute.CONTENT`
    Меняет содержание обязательства или лицо в нём, а не существование и
    исполнимость требования. Слой не различает ролей сторон, поэтому «кому
    принадлежит требование» для него не вопрос судьбы.

`OutputRoute.OTHER_RELATION`
    Касается другого отношения: вещного права, третьих лиц, обеспечения,
    публичного возмещения.

`OutputRoute.OPEN`
    Меняет судьбу требования и до слоя не доходит. Это открытый долг, а не
    решение, и перечень обязан уменьшаться.
"""

from enum import Enum


class OutputRoute(str, Enum):
    VIA_INPUT = "через другой вход"
    DEFAULT = "умолчание слоя"
    REMEDY = "средство защиты или размер"
    EVIDENCE = "доказывание"
    CONTENT = "содержание, а не судьба"
    OTHER_RELATION = "другое отношение"
    OPEN = "открытый долг"


_VIA, _DEFAULT, _REMEDY = OutputRoute.VIA_INPUT, OutputRoute.DEFAULT, OutputRoute.REMEDY
_EVIDENCE, _CONTENT = OutputRoute.EVIDENCE, OutputRoute.CONTENT
_OTHER, _OPEN = OutputRoute.OTHER_RELATION, OutputRoute.OPEN

_VOIDABLE_VIA_INVALIDITY = (
    "сделка оспорима; когда суд признаёт её недействительной, рецензент института "
    "недействительности отмечает это, и слой получает последствие через "
    "contractual_effect_displaced — сверки между блоками нет"
)
_VOID_VIA_INVALIDITY = (
    "последствие — ничтожность — слой получает через институт недействительности "
    "(contractual_effect_displaced), если рецензент назвал основание ничтожности; "
    "сверки между блоками нет"
)
_NO_AUTHORITY_VIA_REPRESENTATION = (
    "последствие — сделка совершена без полномочия (статья 183) — слой получает через "
    "unauthorized_representation_detected, когда рецензент отмечает неодобренное "
    "действие без полномочия; сверки между признаками нет"
)
_TERM_COMPUTATION_OPEN = (
    "от исчисления срока зависит, своевременно ли исполнение, а значит, и вывод о "
    "нарушении (breach_issue). Для срока давности порок проведён в слой "
    "(term_calculation_defective), для срока исполнения — нет: институт не различает, к "
    "какому сроку относится порок"
)
_CONDITION_OPEN = (
    "статус условия решает, возникли ли права и обязанности (статья 157): не наступило "
    "отлагательное — требовать нечего, наступило отменительное — обязательство "
    "прекращено, недобросовестно воспрепятствовали — условие признаётся наступившим. "
    "Институт называет нарушение правила, а не статус условия, и слой о нём не знает"
)
_MODIFICATION = (
    "изменение договора меняет содержание обязательств на будущее (статья 453 пункт 1: "
    "обязательства сохраняются в изменённом виде), а не их существование; по какой "
    "редакции условий построен вывод о нарушении, слой не проверяет"
)
_PARTY_CHANGE = (
    "перемена лица меняет, кому принадлежит требование или на ком лежит долг, а не его "
    "судьбу; кто вправе требовать и с кого — вопрос стороны спора, а слой ролей не "
    "различает"
)
_SECURITY = (
    "судьба обеспечения, данного третьим лицом, — отношение с этим лицом, а не судьба "
    "основного требования"
)
_RULE_OF_PRINCIPLE = (
    "общий принцип без собственного последствия для требования; отказ в защите за "
    "злоупотребление правом слой получает через abuse_of_right_detected"
)


#: Маршрут каждого вывода, который не идёт в слой и не входит в правило
#: проведённого вывода.
LAYER_OUTPUT_ROUTES: dict[str, dict[str, tuple[OutputRoute, str]]] = {
    "formation": {
        "counteroffer_detected": (
            _VIA,
            "ответ на иных условиях — новая оферта (статья 443); итог переговоров — "
            "согласованы ли существенные условия — слой получает через "
            "contract_concluded_prerequisites",
        ),
        "formation_evidence_gap": (
            _EVIDENCE,
            "называет, чего не хватает для вывода о заключении; сам отрицательный итог "
            "слой уже получает — contract_concluded_prerequisites ложно",
        ),
    },
    "invalidity": {
        "secured_creditor_rights_survive": (
            _OTHER,
            "права кредитора или залогодержателя на имущество, распоряжение которым "
            "запрещено судом (пункт 2 статьи 174.1), — отношение с приобретателем, а не "
            "судьба договорного требования",
        ),
        "nullity_consequence_claimant_has_standing": (
            _REMEDY,
            "кто вправе требовать применения последствий ничтожности — порядок "
            "требования о реституции; ничтожность действует независимо от признания "
            "судом, и слой получает её через contractual_effect_displaced",
        ),
        "nullity_consequences_prerequisites": (
            _REMEDY,
            "условия требования о последствиях ничтожности, включая его давность "
            "(пункт 1 статьи 181), — защита по требованию о реституции, а не "
            "действительность договора",
        ),
        "transaction_presumed_effective": (
            _DEFAULT,
            "сделка действует, пока действие не вытеснено, — то же слой выводит сам из "
            "contractual_effect_displaced",
        ),
        "entire_transaction_affected": (
            _VIA,
            "недействительность всей сделки слой выводит сам из contractual_effect_displaced "
            "и partial_invalidity_only; сверки конвейера и предварительная сверка входов "
            "берут этот вывод для существования обязанности и основного обязательства",
        ),
        "restitution_in_kind": (
            _REMEDY,
            "форма возврата — в натуре (пункт 2 статьи 167); режим реституции слой "
            "получает через restitution_required",
        ),
        "monetary_restitution_issue": (
            _REMEDY,
            "форма возврата — возмещение стоимости (пункт 2 статьи 167); режим "
            "реституции слой получает через restitution_required",
        ),
        "public_recovery_issue": (
            _REMEDY,
            "взыскание полученного в доход Российской Федерации (статья 169) суд "
            "применяет в случаях, предусмотренных законом; слой называет режим "
            "реституции, а не её получателя",
        ),
        "additional_damages_issue": (
            _REMEDY,
            "убытки сверх реституции — размер и средство защиты",
        ),
    },
    "form": {
        "notarial_form_satisfied": (
            _DEFAULT,
            "нотариальная форма соблюдена или не требуется — договор не ничтожен из-за "
            "формы, как слой и предполагает",
        ),
        "form_requirement_satisfied": (
            _DEFAULT,
            "форма соблюдена — совпадает с умолчанием слоя: transaction_void_for_form ложно",
        ),
        "witness_testimony_barred": (
            _EVIDENCE,
            "несоблюдение простой письменной формы лишает права ссылаться на "
            "свидетельские показания (пункт 1 статьи 162) — ограничение средств "
            "доказывания, а не действительность",
        ),
        "oral_form_valid": (
            _DEFAULT,
            "устная форма допустима — договор не ничтожен из-за формы, как слой и предполагает",
        ),
    },
    "limitation": {
        "objective_limit_barred": (
            _VIA,
            "тот же признак — десять лет со дня нарушения (пункт 2 статьи 196) — уже "
            "входит в правило истечения давности и доходит до слоя через "
            "limitation_defense_available",
        ),
        "limitation_reset_by_acknowledgement": (
            _VIA,
            "признание долга прерывает течение давности (статья 203); модель учитывает его "
            "в правиле истечения давности, и до слоя оно доходит через "
            "limitation_defense_available",
        ),
        "limitation_suspended": (
            _VIA,
            "приостановление в последние шесть месяцев (статья 202) уже учтено в правиле "
            "истечения давности и доходит до слоя через limitation_defense_available",
        ),
        "additional_claim_barred_with_main": (
            _VIA,
            "с истечением давности по главному требованию истекает и по дополнительным "
            "(статья 207); слой и так распространяет давность на все договорные "
            "требования через limitation_defense_available",
        ),
    },
    "constraint": {
        "damages_remedy_available": (
            _REMEDY,
            "возможность взыскать убытки (статья 393) — средство защиты и размер; сам "
            "вывод о нарушении слой получает через breach_issue",
        ),
        "causation_evidence_gap": (
            _EVIDENCE,
            "называет недоказанную причинную связь; вывод о нарушении слой получает "
            "отдельно — breach_issue",
        ),
        "limitation_bar": (
            _VIA,
            "давность слой получает от института давности — limitation_defense_available; "
            "второй вход о том же создал бы два источника одного факта",
        ),
    },
    "representation": {
        "authority_basis_duty_breached": (_VIA, _NO_AUTHORITY_VIA_REPRESENTATION),
        "self_dealing_duty_breached": (
            _VIA,
            "сделка представителя в отношении себя лично может быть признана "
            "недействительной по иску представляемого (пункт 3 статьи 182); "
            + _VOIDABLE_VIA_INVALIDITY,
        ),
        "commercial_representation_duty_breached": (
            _OTHER,
            "обязанности коммерческого представителя перед представляемыми (статья 184) "
            "— отношение представителя с ними, а не судьба требования из договора",
        ),
        "power_of_attorney_form_duty_breached": (_VIA, _NO_AUTHORITY_VIA_REPRESENTATION),
        "power_of_attorney_term_duty_breached": (_VIA, _NO_AUTHORITY_VIA_REPRESENTATION),
        "substitution_duty_breached": (_VIA, _NO_AUTHORITY_VIA_REPRESENTATION),
        "termination_notice_duty_breached": (
            _VIA,
            "сохраняет ли сделка силу после прекращения доверенности (пункт 2 статьи 189), "
            "рецензент отражает в признаке неуполномоченного действия, и слой получает "
            "это через unauthorized_representation_detected; сверки между признаками нет",
        ),
        "ratification_effect_breached": (
            _VIA,
            "одобренная сделка действует с момента совершения (пункт 2 статьи 183); есть "
            "ли неодобренное действие, слой получает через "
            "unauthorized_representation_detected",
        ),
    },
    "property_rights": {
        "ownership_powers_duty_breached": (
            _OTHER,
            "правомочия собственника (статья 209) — предмет вещного, а не договорного "
            "требования; распоряжение неуправомоченным лицом слой получает отдельно — "
            "unauthorized_disposal_detected",
        ),
        "risk_and_burden_duty_breached": (
            _OTHER,
            "бремя содержания и риск случайной гибели несёт собственник (статьи 210, "
            "211); в договоре переход риска решают правила его типа (например, статья "
            "459), а не слой общих положений",
        ),
        "acquisition_moment_duty_breached": (
            _OTHER,
            "момент возникновения права собственности у приобретателя (статья 223) — "
            "вещное право, а не договорное требование",
        ),
        "acquisitive_prescription_duty_breached": (
            _OTHER,
            "приобретательная давность (статья 234) — вещное право, а не договорное требование",
        ),
        "common_property_duty_breached": (
            _VIA,
            "распоряжение общим имуществом без согласия участников может быть признано "
            "недействительным (пункт 3 статьи 253); " + _VOIDABLE_VIA_INVALIDITY,
        ),
        "vindication_duty_breached": (
            _OTHER,
            "истребование имущества из чужого незаконного владения (статьи 301, 302) — "
            "вещный иск, а не договорное требование",
        ),
        "good_faith_purchaser_breached": (
            _VIA,
            "защита добросовестного приобретателя проигнорирована в разборе; сама защита "
            "выводится отдельно и доходит до слоя через good_faith_acquirer_protected "
            "(статья 302)",
        ),
        "negatory_claim_duty_breached": (
            _OTHER,
            "защита от нарушений, не связанных с лишением владения (статьи 304, 305), — "
            "вещный иск, а не договорное требование",
        ),
        "statutory_termination_of_ownership": (
            _VIA,
            "если прекращение права законом делает исполнение невозможным, слой получает "
            "прекращение обязательства через obligation_discharged_full (статьи 416, 417)",
        ),
        "state_compensation_duty": (
            _OTHER,
            "возмещение убытков государством при прекращении права законом (статья 306) — "
            "публичное возмещение, а не договорное требование",
        ),
    },
    "civil_principles": {
        "good_faith_duty_breached": (_VIA, _RULE_OF_PRINCIPLE),
        "equality_and_freedom_duty_breached": (
            _VIA,
            "нарушение равенства или свободы договора последствие для договора получает "
            "через недействительность (статья 168) — contractual_effect_displaced",
        ),
        "rights_arising_duty_breached": (
            _VIA,
            "возникло ли обязательство (статья 8), слой получает через заключённость и "
            "недействительность — contract_concluded_prerequisites и "
            "contractual_effect_displaced",
        ),
        "protection_refusal_breached": (
            _VIA,
            "отказ в защите при злоупотреблении правом (пункт 2 статьи 10) слой выводит "
            "сам из abuse_of_right_detected",
        ),
        "protection_methods_duty_breached": (
            _REMEDY,
            "способы защиты гражданских прав (статья 12) — средство защиты",
        ),
        "self_help_duty_breached": (
            _REMEDY,
            "самозащита гражданских прав (статья 14) — способ защиты, а не судьба требования",
        ),
        "damages_compensation_duty_breached": (
            _REMEDY,
            "возмещение убытков (статья 15) — размер и средство защиты",
        ),
        "public_authority_liability_duty_breached": (
            _OTHER,
            "убытки от действий государственных органов (статья 16) — публичное "
            "возмещение, а не договорное требование",
        ),
    },
    "transactions": {
        "transaction_definition_duty_breached": (
            _VIA,
            "есть ли сделка (статья 153), слой получает через заключённость — "
            "contract_concluded_prerequisites",
        ),
        "parties_count_duty_breached": (
            _VIA,
            "договор требует согласованной воли сторон (статья 154); это слой получает "
            "через contract_concluded_prerequisites",
        ),
        "unilateral_transaction_duty_breached": (
            _VIA,
            "односторонние сделки, меняющие судьбу договора, — отказ, зачёт, прощение — "
            "слой получает через effective_termination и obligation_discharged_full",
        ),
        "unilateral_regulation_duty_breached": (
            _VIA,
            "общие положения к односторонним сделкам (статья 156) — то же: отказ, зачёт и "
            "прощение доходят через effective_termination и obligation_discharged_full",
        ),
        "conditional_transaction_duty_breached": (_OPEN, _CONDITION_OPEN),
        "condition_interference_duty_breached": (_OPEN, _CONDITION_OPEN),
        "consent_procedure_duty_breached": (
            _VIA,
            "порядок дачи согласия (статья 157.1) — отсутствие необходимого согласия слой "
            "получает через consent_missing_for_transaction",
        ),
        "silence_as_consent_breached": (
            _VIA,
            "молчание не является согласием (пункт 2 статьи 157.1); отсутствие согласия "
            "слой уже получает через consent_missing_for_transaction",
        ),
    },
    "terms": {
        "term_definition_duty_breached": (_OPEN, _TERM_COMPUTATION_OPEN),
        "term_event_certainty_duty_breached": (_OPEN, _TERM_COMPUTATION_OPEN),
        "term_start_duty_breached": (_OPEN, _TERM_COMPUTATION_OPEN),
        "term_end_duty_breached": (_OPEN, _TERM_COMPUTATION_OPEN),
        "non_working_day_duty_breached": (_OPEN, _TERM_COMPUTATION_OPEN),
        "performance_deadline_duty_breached": (_OPEN, _TERM_COMPUTATION_OPEN),
        "organisation_operating_hours_duty_breached": (_OPEN, _TERM_COMPUTATION_OPEN),
        "written_notice_dispatch_duty_breached": (_OPEN, _TERM_COMPUTATION_OPEN),
    },
    "persons": {
        "legal_capacity_duty_breached": (
            _VIA,
            "правоспособность гражданина (статья 17) — есть ли сторона договора; слой "
            "получает это через contract_concluded_prerequisites",
        ),
        "active_capacity_age_duty_breached": (
            _VIA,
            "сделка малолетнего ничтожна (статья 172); " + _VOID_VIA_INVALIDITY,
        ),
        "limited_capacity_duty_breached": (
            _VIA,
            "сделка ограниченно дееспособного без согласия попечителя (статья 176); "
            + _VOIDABLE_VIA_INVALIDITY,
        ),
        "guardianship_consent_duty_breached": (
            _VIA,
            "сделка без согласия попечителя (статьи 175, 176); " + _VOIDABLE_VIA_INVALIDITY,
        ),
        "capacity_restriction_duty_breached": (
            _VIA,
            "отказ от правоспособности или дееспособности ничтожен (пункт 3 статьи 22); "
            + _VOID_VIA_INVALIDITY,
        ),
        "entity_capacity_scope_duty_breached": (
            _VIA,
            "сделка юридического лица вне его правоспособности (статья 173); "
            + _VOIDABLE_VIA_INVALIDITY,
        ),
        "entity_registration_duty_breached": (
            _VIA,
            "правоспособность юридического лица возникает с внесения сведений о нём в "
            "реестр (пункт 3 статьи 49, статья 51); есть ли сторона договора, слой "
            "получает через contract_concluded_prerequisites",
        ),
        "entity_body_authority_duty_breached": (
            _VIA,
            "сделка органа с превышением полномочий (статья 174); " + _VOIDABLE_VIA_INVALIDITY,
        ),
    },
    "objects": {
        "object_classification_duty_breached": (
            _CONTENT,
            "вид объекта (статья 128) определяет применимые правила, но судьбу "
            "требования меняет только изъятие объекта из оборота — "
            "object_excluded_from_circulation",
        ),
        "immovable_classification_duty_breached": (
            _VIA,
            "отнесение к недвижимости (статья 130) влечёт требования о форме и "
            "регистрации; их несоблюдение слой получает через transaction_void_for_form",
        ),
        "divisibility_duty_breached": (
            _CONTENT,
            "делимость и сложные вещи (статьи 133, 134) — предмет исполнения, а не судьба "
            "требования",
        ),
        "principal_and_appurtenance_duty_breached": (
            _CONTENT,
            "принадлежность следует судьбе главной вещи (статья 135) — объём исполнения, "
            "а не судьба требования",
        ),
        "fruits_products_income_duty_breached": (
            _CONTENT,
            "кому принадлежат плоды и доходы (статья 136) — объём исполнения, а не судьба "
            "требования",
        ),
        "money_or_securities_duty_breached": (
            _VIA,
            "правила о деньгах и ценных бумагах определяют предмет и способ исполнения; "
            "недействительность, если её влечёт нарушение, приходит через "
            "contractual_effect_displaced",
        ),
        "intangible_benefits_duty_breached": (
            _OTHER,
            "защита нематериальных благ (статья 150) — внедоговорное отношение",
        ),
        "honour_and_reputation_duty_breached": (
            _OTHER,
            "защита чести и деловой репутации (статья 152) — внедоговорное отношение",
        ),
    },
    "termination": {
        "mutual_modification_effective": (_CONTENT, _MODIFICATION),
        "judicial_modification_prerequisites": (_CONTENT, _MODIFICATION),
        "judicial_modification_effective": (_CONTENT, _MODIFICATION),
        "unilateral_modification_effective": (_CONTENT, _MODIFICATION),
        "effective_modification": (_CONTENT, _MODIFICATION),
        "invalid_unilateral_action": (
            _DEFAULT,
            "отказ без права на него последствий не влечёт (статья 450.1): договор "
            "продолжает действовать, как слой и предполагает",
        ),
        "competing_effective_paths": (
            _EVIDENCE,
            "сигнал противоречивых данных: одновременно действуют изменение и "
            "расторжение; институт поднимает флаг, слою выводить нечего",
        ),
        "contract_continues_unchanged": (
            _DEFAULT,
            "договор продолжает действовать без изменений — умолчание слоя",
        ),
        "future_obligations_terminated": (
            _VIA,
            "тождествен effective_termination, который уже вход слоя",
        ),
        "restitution_issue": (
            _REMEDY,
            "возврат при неравноценности после расторжения (пункт 4 статьи 453) — средство защиты",
        ),
        "termination_losses_issue": (
            _REMEDY,
            "убытки при расторжении из-за существенного нарушения (пункт 5 статьи 453) — "
            "размер и средство защиты",
        ),
    },
    "attribution_delay": {
        "debtor_answerable_for_employees": (
            _DEFAULT,
            "должник отвечает за своих работников (статья 402) — совпадает с умолчанием "
            "слоя: за установленное нарушение отвечает должник",
        ),
        "debtor_answerable_for_third_party": (
            _DEFAULT,
            "общее правило статьи 403 — должник отвечает за третье лицо — совпадает с "
            "умолчанием слоя; меняет судьбу только исключение, и оно в слое",
        ),
        "creditor_fault_established": (
            _REMEDY,
            "вина кредитора меняет размер ответственности, а не её наличие: суд вправе "
            "уменьшить размер (статья 404)",
        ),
        "liability_reducible_for_creditor_fault": (
            _REMEDY,
            "то же основание размера ответственности (статья 404)",
        ),
        "debtor_in_delay": (
            _VIA,
            "сама просрочка — форма нарушения, и факт нарушения слой получает от модели "
            "обязательства — breach_issue",
        ),
        "creditor_may_refuse_performance": (
            _REMEDY,
            "отказ кредитора от исполнения, утратившего интерес (пункт 2 статьи 405), — "
            "выбор средства защиты",
        ),
    },
    "obligation_dynamics": {
        "assignment_enforceable_against_debtor": (_CONTENT, _PARTY_CHANGE),
        "assignment_contract_breach_issue": (
            _REMEDY,
            "уступка денежного требования вопреки договорному запрету действительна, но "
            "цедент отвечает перед должником (пункт 3 статьи 388) — ответственность, а не "
            "судьба требования",
        ),
        "debtor_defenses_preserved": (
            _REMEDY,
            "возражения должника против нового кредитора (статья 386) — защита в споре, а "
            "не судьба требования",
        ),
        "debtor_setoff_against_assignee_issue": (
            _VIA,
            "если зачёт против нового кредитора состоится (статья 412), прекращение слой "
            "получает через obligation_discharged_full",
        ),
        "cedent_document_transfer_issue": (
            _OTHER,
            "передача документов цедентом цессионарию (пункт 3 статьи 385) — отношение "
            "цедента с цессионарием",
        ),
        "cedent_invalid_claim_warranty_issue": (
            _OTHER,
            "ответственность цедента за недействительность требования (статья 390) — "
            "отношение цедента с цессионарием",
        ),
        "cedent_performance_guarantee_issue": (
            _OTHER,
            "ответственность цедента за неисполнение должником (пункт 1 статьи 390) — "
            "отношение цедента с цессионарием",
        ),
        "debt_transfer_effective": (_CONTENT, _PARTY_CHANGE),
        "original_debtor_released_effective": (_CONTENT, _PARTY_CHANGE),
        "cumulative_debtors": (_CONTENT, _PARTY_CHANGE),
        "new_debtor_defenses_preserved": (
            _REMEDY,
            "возражения нового должника (статья 392) — защита в споре, а не судьба требования",
        ),
        "third_party_security_terminated_on_transfer": (_OTHER, _SECURITY),
        "contract_transfer_effective": (_CONTENT, _PARTY_CHANGE),
        "parties_changed_not_discharged": (
            _DEFAULT,
            "перемена лиц обязательство не прекращает — совпадает с умолчанием слоя",
        ),
        "creditor_confirmation_issue": (
            _VIA,
            "отказ кредитора выдать расписку даёт должнику право задержать исполнение, и "
            "кредитор считается просрочившим (пункт 2 статьи 408); просрочку кредитора "
            "слой получает через creditor_delay_excuses_debtor",
        ),
        "notary_deposit_notice_issue": (
            _EVIDENCE,
            "извещение кредитора о внесении в депозит (пункт 2 статьи 327) — порядок, не "
            "отменяющий исполнения; прекращение слой получает через "
            "obligation_discharged_full",
        ),
        "accord_agreement_only": (
            _DEFAULT,
            "соглашение об отступном без предоставления обязательства не прекращает "
            "(статья 409) — умолчание слоя",
        ),
        "new_obligation_created_by_novation": (
            _CONTENT,
            "новое обязательство заменяет прежнее (статья 414); прекращение прежнего слой "
            "получает через obligation_discharged_full",
        ),
        "original_accessories_terminated_by_novation": (_OTHER, _SECURITY),
        "third_party_security_survives_novation": (_OTHER, _SECURITY),
        "creditor_caused_impossibility_issue": (
            _REMEDY,
            "при невозможности по вине кредитора он не вправе требовать возвращения "
            "исполненного (пункт 2 статьи 416) — режим возврата, а не судьба требования",
        ),
        "government_act_losses_issue": (
            _REMEDY,
            "убытки от акта государственного органа (пункт 1 статьи 417) — размер и "
            "средство защиты",
        ),
        "government_act_restoration_issue": (
            _VIA,
            "при признании акта недействительным обязательство восстанавливается (пункт 3 "
            "статьи 417); правило прекращения уже исключает такой акт, и слой получает это "
            "через obligation_discharged_full",
        ),
        "competing_discharge_paths": (
            _EVIDENCE,
            "сигнал противоречивых данных: названо несколько оснований прекращения сразу; "
            "институт поднимает флаг, слою выводить нечего",
        ),
    },
    "meeting_decisions": {},
}


def open_output_debt() -> dict[str, list[str]]:
    """Выводы, которые меняют судьбу требования и до слоя не доходят."""
    return {
        institute: sorted(name for name, (route, _) in routes.items() if route is OutputRoute.OPEN)
        for institute, routes in LAYER_OUTPUT_ROUTES.items()
        if any(route is OutputRoute.OPEN for route, _ in routes.values())
    }


def measure_layer_outputs() -> dict[str, dict[str, frozenset[str]]]:
    """Измерить выводы питающих институтов: какие идут в слой, какие — составляющие.

    Проведённые выводы определяются по обращениям к атрибутам при сборке входов
    слоя, составляющие — по объявленным правилам институтов на демонстрационном
    деле. Ни то, ни другое не записывается вручную.
    """
    import inspect

    from causa.institutional.contracts.general_effects import build_general_effects_inputs
    from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult
    from causa.institutional.contracts.synthetic_reviewed_analysis import (
        build_synthetic_supply_analysis_artifact,
    )
    from causa.reasoning.rule_parity import parse_rule, symbols_of

    class _Reads:
        def __init__(self) -> None:
            self.read: set[str] = set()

        def __getattr__(self, name: str) -> bool:
            self.read.add(name)
            return False

    parameters = list(inspect.signature(build_general_effects_inputs).parameters)
    readers = [_Reads() for _ in parameters]
    build_general_effects_inputs(*readers)
    result = build_synthetic_supply_analysis_artifact().result

    measured = {}
    for parameter, reader in zip(parameters, readers, strict=True):
        institute = parameter.removesuffix("_evaluation")
        evaluation = ReviewedContractAnalysisResult.model_fields[parameter].annotation
        outputs = {
            name
            for name, field in evaluation.model_fields.items()
            if field.annotation is bool
            and name != "satisfiable"
            and not name.startswith("requires_human")
        }
        constraint_set = getattr(
            result, "constraint_set" if institute == "constraint" else f"{institute}_constraint_set"
        )
        rules = dict(filter(None, (parse_rule(line) for line in constraint_set.expressions)))
        components: set[str] = set()
        pending = list(reader.read)
        while pending:
            name = pending.pop()
            for symbol in symbols_of(rules[name]) if name in rules else ():
                if symbol not in components:
                    components.add(symbol)
                    pending.append(symbol)
        measured[institute] = {
            "outputs": frozenset(outputs),
            "wired": frozenset(reader.read),
            "components": frozenset((components & outputs) - reader.read),
        }
    return measured
