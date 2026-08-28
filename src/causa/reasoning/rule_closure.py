"""Закрытие вопросов сверки: чем оказалось каждое объявленное условие.

Сверка объявленного правила с исполняемым оставила 40 имён без соответствия и
честно назвала их вопросами: она не знает права и не берётся судить, должно ли
условие быть в модели. Здесь эти вопросы закрыты, и закрыты не мнением.

## Что оказалось

Ни одно из 40 имён не было забытым условием. Все они — либо переименования, либо
сводки нескольких предикатов под одним словом. Модель проверяет то же самое, а в
большинстве правил — больше: исполняемое правило почти всегда строже
объявленного.

Поэтому доказывается не равенство, а следование: **исполняемое влечёт
объявленное**. Если бы условие потерялось, следование бы рухнуло, и решатель
выдал бы набор фактов, на котором исполняемое правило срабатывает, а объявленное
— нет. Равенство здесь требовать нельзя: оно объявило бы дефектом каждое
уточнение, добавленное к правилу после того, как объявление написали.

## Почему таблица привязана к правилу, а не к имени

Одно и то же слово в разных правилах означает разное. `delivered_notice` в
отказе от договора купли-продажи — это уведомление об одностороннем отказе, а в
приостановлении встречного исполнения — уведомление о приостановлении. Таблица,
привязанная к имени, слила бы их в одно и доказала бы неверное.

## Граница

Доказывается соответствие объявленного и исполняемого, а не правильность
исполняемого. Утверждение «правило верно передаёт норму ГК РФ» лежит вне
решателя: оно записано рядом с каждым условием по-русски, со ссылкой на статью,
и проверяется юристом, а не Z3.
"""

import ast
from pathlib import Path

from pydantic import BaseModel, Field
from z3 import Not, Solver, sat

from causa.reasoning.rule_parity import (
    Node,
    compile_to_z3,
    parse_expression,
)

RULE_CLOSURE_VERSION = "rule-closure-v0"

#: Историческое объявление правила — тот текст, который сверка признала
#: расходящимся с исполняемым и переписала.
#:
#: Хранится здесь, а не только в документации: закрытие вопроса обязано
#: опираться на то, что действительно объявлялось, и оставаться проверяемым
#: после того, как документ перепишут.
DECLARED_RULES: dict[str, str] = {
    "eviction_remedy": (
        "withdrawal_on_pretransfer_ground AND NOT buyer_knowledge AND NOT preventable_procedure_gap"
    ),
    "installment_refusal": "installment_default AND seller_refusal AND NOT more_than_half_paid",
    "notice_defense": "late_notice AND proven_prejudice AND NOT seller_knowledge",
    "quality_remedy": "defect AND timely_claim AND applicable_causation_burden",
    "sale_contract": (
        "concluded AND transfer_ownership_duty AND acceptance_duty AND payment_duty "
        "AND goods_subject AND name AND quantity"
    ),
    "sale_refusal": "statutory_refusal_ground AND delivered_notice",
    "title_return": "retained_title AND unmet_condition AND seller_return_demand",
    "transfer_duty": "completed AND (delivery OR availability OR carrier_handover)",
    "article_520_cover": (
        "unremedied_nonconformity AND substitute_purchase AND documented_expenses"
    ),
    "article_520_withholding": "unremedied_quality_or_completeness AND payment_withheld",
    "negotiation_response_breach": ("disagreements_received AND NOT timely_response_or_refusal"),
    "counterperformance_suspension": (
        "reciprocal_due AND nonperformance_risk AND delivered_notice"
    ),
    "damages": (
        "breach AND claimed_loss AND proven_loss_type AND causation AND reasonable_amount_basis"
    ),
    "indemnity": (
        "business_agreement AND clear_nonbreach_trigger AND occurred_loss AND amount_method "
        "AND NOT bad_faith"
    ),
    "proper_performance": (
        "obligation_exists AND tendered "
        "AND conforming_subject_quality_quantity_time_place_recipient"
    ),
    "third_party_acceptance": (
        "third_party_tendered AND statutory_acceptance_ground AND NOT personal_performance"
    ),
    "assignment_effective": (
        "obligation_exists AND assignment_agreement AND form AND identifiable_claim "
        "AND transferable_claim AND required_consent"
    ),
    "contract_transfer_effective": (
        "obligation_exists AND contract_transfer_agreed AND all_parties_consent AND required_forms"
    ),
    "debt_forgiveness_effective": (
        "obligation_exists AND forgiveness_notice AND NOT objection "
        "AND NOT third_party_prejudice AND NOT commercial_gift_bar"
    ),
    "notary_deposit_discharge": ("obligation_exists AND deposit_made AND statutory_deposit_ground"),
    "novation_effective": (
        "obligation_exists AND agreement AND clear_replacement_intent AND new_subject_or_basis "
        "AND new_terms AND form"
    ),
    "setoff_effective": (
        "obligation_exists AND declaration_delivered AND mutual_homogeneous_due_claims "
        "AND amount_proven AND NOT bar"
    ),
    "accessory_security_displaced_by_main_invalidity": (
        "main_obligation_invalid AND accessory_security_created"
    ),
    "guarantee_demand_payable": (
        "effective_independent_guarantee AND timely_compliant_demand AND NOT abuse"
    ),
    "penalty_security_enforceable": (
        "valid_main_obligation AND breach AND written_penalty AND trigger"
    ),
    "pledge_foreclosure_prerequisites": (
        "pledge_valid_between_parties AND breach AND foreclosure_ground AND amount_proven "
        "AND NOT bar"
    ),
    "pledge_valid_between_parties": (
        "valid_main_obligation AND pledge_created AND form AND asset AND authority"
    ),
    "security_payment_credit_available": "active_security_payment AND secured_event",
    "surety_enforceable": ("valid_main_obligation AND written_surety AND scope AND NOT terminated"),
    "judicial_termination_prerequisites": (
        "contract_formed AND judicial_request_targets_termination AND pretrial_order_satisfied "
        "AND judicial_ground"
    ),
}

#: Исполняемое правило, которым обернулось объявленное.
#:
#: В пятнадцати случаях переименовали не условие, а само правило. Соответствие
#: ведётся вручную и с причиной: вывести его по сходству имён значило бы
#: доказывать соответствие тому правилу, которое случайно похоже названо.
EXECUTED_RULE_OF: dict[str, str] = {
    "eviction_remedy": "eviction_loss_remedy_available",
    "installment_refusal": "installment_refusal_available",
    "notice_defense": "notice_defense_available",
    "quality_remedy": "quality_remedies_available",
    "sale_contract": "sale_contract_qualified",
    "sale_refusal": "sale_contract_refusal_effective",
    "title_return": "title_return_remedy",
    "transfer_duty": "transfer_duty_performed",
    "article_520_cover": "cover_purchase_cost_recovery",
    "article_520_withholding": "payment_withholding_available",
    "counterperformance_suspension": "counterperformance_suspension_available",
    "damages": "damages_prerequisites_satisfied",
    "indemnity": "indemnity_prerequisites_satisfied",
    "third_party_acceptance": "third_party_performance_acceptance_required",
}


#: Чем оказалось каждое из 40 имён, оставшихся без соответствия.
#:
#: Ключ — объявленное правило, потому что одно слово в разных правилах значит
#: разное. Значение — выражение над предикатами модели и обоснование по-русски
#: со ссылкой на норму.
OPEN_QUESTION_MEANINGS_RU: dict[str, dict[str, tuple[str, str]]] = {
    "eviction_remedy": {
        "withdrawal_on_pretransfer_ground": (
            "withdrawal_ground_predates_transfer",
            "Переименование. Статья 461 ГК РФ отвечает за изъятие по основанию, "
            "возникшему до передачи товара; модель называет это условие прямо, "
            "объявление — через предлог.",
        ),
        "buyer_knowledge": (
            "buyer_knew_withdrawal_ground",
            "Переименование. Осведомлённость покупателя об основании изъятия "
            "освобождает продавца от ответственности (пункт 1 статьи 461 ГК РФ); "
            "имя уточнено, чтобы не путать с осведомлённостью о чём угодно ещё.",
        ),
        "preventable_procedure_gap": (
            "third_party_eviction_claim_filed AND NOT buyer_joined_seller_to_eviction_case "
            "AND seller_could_prevent_withdrawal",
            "Сводка трёх фактов в одно слово. Статья 462 ГК РФ снимает "
            "ответственность продавца, если покупатель не привлёк его к делу и "
            "продавец доказал, что мог бы предотвратить изъятие. Объявление "
            "прятало за словом «пробел» и непривлечение, и предотвратимость.",
        ),
    },
    "installment_refusal": {
        "installment_default": (
            "installment_payment_due AND NOT installment_payment_made",
            "Сводка. Просрочка очередного платежа — это наступивший срок и "
            "неуплата (пункт 2 статьи 489 ГК РФ), два факта, а не один.",
        ),
        "more_than_half_paid": (
            "paid_amount_exceeds_half_price",
            "Переименование. Пункт 2 статьи 489 ГК РФ запрещает отказ, когда "
            "сумма полученных платежей превышает половину цены товара.",
        ),
    },
    "notice_defense": {
        "late_notice": (
            "NOT prompt_notice_given",
            "Переименование с обратным знаком. Модель хранит положительный факт "
            "— извещение дано своевременно (статья 483 ГК РФ), — а объявление "
            "называло его отрицание. Хранить положительный факт правильнее: "
            "бремя доказать своевременность лежит на покупателе.",
        ),
    },
    "quality_remedy": {
        "applicable_causation_burden": (
            "(seller_warranty_given AND warranty_period_active "
            "AND NOT seller_proved_posttransfer_defect_cause "
            "OR NOT (seller_warranty_given AND warranty_period_active) "
            "AND buyer_proved_pretransfer_defect_cause)",
            "Сводка целого правила распределения бремени. Пункт 1 статьи 476 ГК "
            "РФ возлагает доказывание на покупателя, пункт 2 — на продавца, если "
            "дана гарантия и срок не истёк. Объявление называло это одним словом "
            "«применимое бремя», из-за чего было неясно, чьё именно.",
        ),
    },
    "sale_contract": {
        "goods_subject": (
            "goods_existing_or_future",
            "Переименование. Пункт 2 статьи 455 ГК РФ допускает продажу как "
            "имеющегося, так и будущего товара; модель называет это условие "
            "прямо, объявление — обобщённо.",
        ),
    },
    "sale_refusal": {
        "statutory_refusal_ground": (
            "(seller_refused_goods_transfer AND buyer_chose_contract_refusal_for_nontransfer "
            "OR (accessories_required AND NOT accessories_transferred "
            "OR documents_required AND NOT documents_transferred) "
            "AND buyer_set_reasonable_document_term AND seller_failed_document_term "
            "AND buyer_refused_goods_for_documents "
            "OR quality_defect AND defect_material "
            "AND (seller_warranty_given AND warranty_period_active "
            "AND NOT seller_proved_posttransfer_defect_cause "
            "OR NOT (seller_warranty_given AND warranty_period_active) "
            "AND buyer_proved_pretransfer_defect_cause) "
            "AND defect_discovered_within_applicable_period "
            "AND buyer_chose_contract_refusal_for_defect "
            "OR incomplete_goods AND buyer_requested_completion "
            "AND NOT seller_completed_reasonable_time "
            "AND buyer_chose_contract_refusal_for_incompleteness "
            "OR buyer_failed_acceptance AND seller_chose_contract_refusal_for_nonacceptance "
            "OR installment_sale AND installment_payment_due AND NOT installment_payment_made "
            "AND NOT paid_amount_exceeds_half_price AND seller_chose_installment_refusal "
            "OR insurance_duty_allocated AND insurance_duty_due AND NOT insurance_obtained "
            "AND counterparty_chose_insurance_refusal)",
            "Сводка семи самостоятельных оснований отказа в одно слово: "
            "непередача товара (статья 463), непередача принадлежностей и "
            "документов (статья 464), существенный недостаток (пункт 2 статьи "
            "475), некомплектность (пункт 2 статьи 480), непринятие товара "
            "(статья 484), просрочка платежа в рассрочку (пункт 2 статьи 489) и "
            "неисполнение обязанности страхования (статья 490). Объявление "
            "называло их «законным основанием», не перечисляя, — и по нему нельзя "
            "было проверить, все ли учтены.",
        ),
        "delivered_notice": (
            "unilateral_refusal_notice_delivered",
            "Переименование. Здесь имеется в виду уведомление об одностороннем "
            "отказе (пункт 1 статьи 450.1 ГК РФ), а не уведомление вообще.",
        ),
    },
    "title_return": {
        "retained_title": (
            "title_retention_agreed",
            "Переименование. Статья 491 ГК РФ говорит о сохранении права "
            "собственности за продавцом по условию договора; модель хранит факт "
            "согласования такого условия.",
        ),
        "unmet_condition": (
            "NOT title_condition_met",
            "Переименование с обратным знаком. Модель хранит наступление условия "
            "перехода права (обычно оплаты), объявление — его ненаступление.",
        ),
    },
    "transfer_duty": {
        "availability": (
            "NOT delivery_obligation AND NOT shipment_contract AND goods_made_available",
            "Сводка. Предоставление товара в распоряжение покупателя (абзац "
            "третий пункта 1 статьи 458 ГК РФ) — не третий равноправный способ, а "
            "остаточный: он применяется, когда нет ни обязанности доставки, ни "
            "условия о перевозке. Объявление перечисляло три способа через ИЛИ и "
            "теряло эту очерёдность.",
        ),
    },
    "article_520_cover": {
        "unremedied_nonconformity": (
            "(quantity_shortfall AND NOT actual_replenishment_completed "
            "OR quality_defect AND NOT defect_promptly_cured_or_replaced "
            "OR incomplete_goods AND NOT incompleteness_promptly_cured_or_replaced)",
            "Сводка трёх видов неисполнения с их устранением. Пункт 1 статьи 520 "
            "ГК РФ даёт право на приобретение у другого лица при недопоставке "
            "(статья 511), невыполнении требований о замене недоброкачественного "
            "товара (статья 518) и о доукомплектовании (статья 519).",
        ),
        "substitute_purchase": (
            "buyer_acquired_substitute",
            "Переименование. Пункт 1 статьи 520 ГК РФ говорит о приобретении "
            "непоставленных товаров у других лиц; слово «замещающая покупка» в "
            "объявлении путало эту статью с замещающей сделкой пункта 1 статьи 393.1.",
        ),
    },
    "article_520_withholding": {
        "unremedied_quality_or_completeness": (
            "(quality_defect AND NOT defect_promptly_cured_or_replaced "
            "OR incomplete_goods AND NOT incompleteness_promptly_cured_or_replaced)",
            "Сводка. Пункт 2 статьи 520 ГК РФ даёт право отказаться от оплаты "
            "товаров ненадлежащего качества и некомплектных — только этих двух "
            "видов, недопоставка сюда не входит. Объявление их не разделяло.",
        ),
    },
    "negotiation_response_breach": {
        "timely_response_or_refusal": (
            "thirty_day_response_or_refusal",
            "Переименование. Пункт 1 статьи 507 ГК РФ задаёт именно "
            "тридцатидневный срок; слово «своевременный» его скрывало.",
        ),
    },
    "counterperformance_suspension": {
        "nonperformance_risk": (
            "(counterparty_failed_due_performance OR clear_future_nonperformance)",
            "Сводка двух оснований. Пункт 2 статьи 328 ГК РФ допускает "
            "приостановление и при состоявшемся неисполнении, и при "
            "обстоятельствах, очевидно свидетельствующих о том, что исполнение не "
            "будет произведено в срок.",
        ),
    },
    "damages": {
        "proven_loss_type": (
            "(actual_loss_proven OR lost_profit_claimed AND lost_profit_measures_proven)",
            "Сводка с несимметричным доказыванием. Реальный ущерб доказывается "
            "сам по себе, а упущенная выгода требует ещё и доказательств "
            "приготовлений и мер для её получения (пункт 4 статьи 393 ГК РФ). "
            "Объявление называло обе части одним словом «доказанный вид убытков» "
            "и стирало это различие.",
        ),
    },
    "indemnity": {
        "business_agreement": (
            "indemnity_agreement AND indemnity_business_context",
            "Сводка. Пункт 1 статьи 406.1 ГК РФ допускает возмещение потерь "
            "только по соглашению и только между сторонами, действующими при "
            "осуществлении предпринимательской деятельности.",
        ),
        "clear_nonbreach_trigger": (
            "indemnity_clear AND indemnity_trigger_unrelated_to_breach",
            "Сводка. Соглашение о возмещении потерь должно быть явным (пункт 1 "
            "статьи 406.1), а обстоятельство — не связанным с нарушением "
            "обязательства: иначе это убытки, а не возмещение потерь.",
        ),
    },
    "proper_performance": {
        "conforming_subject_quality_quantity_time_place_recipient": (
            "subject_conforms AND quality_quantity_conform AND performance_at_due_time "
            "AND performance_at_proper_place AND performance_to_proper_recipient",
            "Сводка пяти условий надлежащего исполнения в одно имя длиной в "
            "строку. Статьи 309, 311, 312, 314 и 316 ГК РФ отвечают за предмет, "
            "количество и качество, срок, место и надлежащего получателя. "
            "Объявление сцепляло их так, что нельзя было сказать, какое именно "
            "нарушено.",
        ),
    },
    "third_party_acceptance": {
        "statutory_acceptance_ground": (
            "(debtor_assigned_third_party_performance OR debtor_monetary_delay "
            "OR third_party_property_right_at_risk)",
            "Сводка трёх оснований статьи 313 ГК РФ: возложение исполнения "
            "должником (пункт 1), просрочка должника по денежному обязательству и "
            "опасность утраты третьим лицом права на имущество должника (пункт 2).",
        ),
    },
    "assignment_effective": {
        "transferable_claim": (
            "NOT claim_personal_to_creditor AND NOT assignment_prohibited_by_law",
            "Сводка двух запретов. Уступка невозможна, если требование неразрывно "
            "связано с личностью кредитора (статья 383 ГК РФ) или её запрещает "
            "закон. Объявление называло это положительным словом «передаваемое "
            "требование», и по нему нельзя было увидеть, что запретов два.",
        ),
    },
    "contract_transfer_effective": {
        "required_forms": (
            "assignment_form_observed AND debt_transfer_form_observed",
            "Сводка. Статья 392.3 ГК РФ применяет к передаче договора правила и "
            "об уступке требования, и о переводе долга, поэтому форм здесь две, а "
            "не одна. Множественное число в объявлении на это намекало, но "
            "проверить по нему было нечего.",
        ),
    },
    "debt_forgiveness_effective": {
        "commercial_gift_bar": (
            "forgiveness_gift_bar",
            "Переименование. Прощение долга с намерением одарить между "
            "коммерческими организациями упирается в запрет дарения (подпункт 4 "
            "пункта 1 статьи 575 ГК РФ); модель выводит этот запрет отдельным "
            "правилом из намерения и состава сторон.",
        ),
    },
    "notary_deposit_discharge": {
        "statutory_deposit_ground": (
            "deposit_ground_creditor_absent_or_evasive",
            "Переименование. Пункт 1 статьи 327 ГК РФ перечисляет основания "
            "внесения в депозит — отсутствие кредитора, его недееспособность, "
            "неопределённость и уклонение от принятия; модель сводит их к одному "
            "предикату, а объявление называло «законным основанием».",
        ),
    },
    "novation_effective": {
        "clear_replacement_intent": (
            "novation_intent_clear",
            "Переименование. Из соглашения должно определённо следовать намерение "
            "заменить первоначальное обязательство (статья 414 ГК РФ).",
        ),
    },
    "setoff_effective": {
        "declaration_delivered": (
            "set_off_declared AND set_off_notice_delivered",
            "Сводка. Зачёт производится заявлением, и заявление должно быть "
            "получено другой стороной (статья 410 ГК РФ): объявление и доставка — "
            "два факта.",
        ),
        "mutual_homogeneous_due_claims": (
            "counterclaims_mutual AND counterclaims_homogeneous AND active_claim_due "
            "AND passive_claim_due_or_early_allowed",
            "Сводка четырёх условий статьи 410 ГК РФ: встречность, однородность, "
            "наступление срока по активному требованию и наступление срока либо "
            "допустимость досрочного исполнения по пассивному. Объявление "
            "склеивало их в одно имя, и потерю любого из них было бы не заметить.",
        ),
        "bar": (
            "setoff_bar",
            "Переименование. Статья 411 ГК РФ перечисляет случаи недопустимости "
            "зачёта, и истечение давности по активному требованию — один из них; "
            "модель выводит запрет отдельным правилом.",
        ),
    },
    "accessory_security_displaced_by_main_invalidity": {
        "accessory_security_created": (
            "(penalty_agreed OR pledge_created OR suretyship_created "
            "OR payment_transferred_at_conclusion AND payment_identified_as_deposit_in_writing "
            "AND NOT deposit_nature_doubtful OR security_payment_agreed)",
            "Сводка всех акцессорных способов обеспечения. Пункт 3 статьи 329 ГК "
            "РФ связывает их судьбу с судьбой основного обязательства; исключение "
            "— независимая гарантия, и её в этом перечне намеренно нет.",
        ),
    },
    "guarantee_demand_payable": {
        "effective_independent_guarantee": (
            "guarantee_formally_effective",
            "Переименование. Модель выводит действительность гарантии отдельным "
            "правилом из выдачи, воспроизводимой формы, определимости условий "
            "(статьи 368 и 373 ГК РФ) и неистечения срока.",
        ),
        "timely_compliant_demand": (
            "creditor_demand_made AND guarantee_demand_timely AND guarantee_demand_complies",
            "Сводка трёх фактов. Требование должно быть предъявлено, предъявлено "
            "до окончания срока гарантии и соответствовать её условиям (статья "
            "374 ГК РФ). Объявление сцепляло срок и соответствие, теряя сам факт "
            "предъявления.",
        ),
    },
    "penalty_security_enforceable": {
        "valid_main_obligation": (
            "main_obligation_exists AND NOT main_obligation_invalid",
            "Сводка. Существование обязательства и его действительность — разные "
            "факты, и модель их разделяет: недействительность основного "
            "обязательства влечёт недействительность обеспечения (пункт 3 статьи "
            "329 ГК РФ), а несуществование делает обеспечение беспредметным.",
        ),
        "written_penalty": (
            "penalty_agreed AND penalty_writing_observed",
            "Сводка. Соглашение о неустойке и его письменная форма — два факта; "
            "несоблюдение формы влечёт недействительность соглашения (статья 331 "
            "ГК РФ), а не его отсутствие.",
        ),
        "trigger": (
            "penalty_trigger_occurred",
            "Переименование: наступление обстоятельства, с которым договор "
            "связывает начисление неустойки.",
        ),
    },
    "pledge_foreclosure_prerequisites": {
        "foreclosure_ground": (
            "foreclosure_ground_exists",
            "Переименование: неисполнение или ненадлежащее исполнение "
            "обеспеченного залогом обязательства (пункт 1 статьи 348 ГК РФ).",
        ),
        "amount_proven": (
            "secured_amount_proven",
            "Переименование. Размер обеспеченного залогом требования подлежит "
            "доказыванию при обращении взыскания; без него нельзя проверить "
            "несоразмерность по пункту 2 статьи 348 ГК РФ.",
        ),
        "bar": (
            "pledge_foreclosure_bar",
            "Переименование. Пункт 2 статьи 348 ГК РФ не допускает обращения "
            "взыскания при одновременном совпадении двух условий — незначительности "
            "нарушения и явной несоразмерности требований стоимости заложенного "
            "имущества; модель выводит запрет отдельным правилом именно как "
            "совпадение, а не как любое из двух.",
        ),
    },
    "pledge_valid_between_parties": {
        "valid_main_obligation": (
            "main_obligation_exists AND NOT main_obligation_invalid",
            "Сводка, та же что и в неустойке. Залог следует судьбе основного "
            "обязательства (пункт 3 статьи 329 ГК РФ), и модель разделяет его "
            "существование и действительность.",
        ),
        "authority": (
            "pledgor_owns_or_authorized",
            "Переименование. Залогодателем может быть собственник вещи либо лицо, "
            "имеющее иное право распоряжения ею (пункт 2 статьи 335 ГК РФ). "
            "Голое слово «полномочие» скрывало, что речь именно о праве "
            "распоряжения предметом залога, а не о полномочии подписать договор.",
        ),
        "asset": (
            "pledged_asset_identified",
            "Переименование: определённость предмета залога как существенного "
            "условия договора (пункт 1 статьи 339 ГК РФ).",
        ),
    },
    "security_payment_credit_available": {
        "active_security_payment": (
            "security_payment_active",
            "Переименование. Обеспечительный платёж должен быть внесён и не "
            "возвращён к моменту наступления обстоятельства (пункт 1 статьи 381.1 ГК "
            "РФ); модель называет это действующим платежом.",
        ),
        "secured_event": (
            "secured_circumstance_occurred",
            "Переименование. Пункт 1 статьи 381.1 ГК РФ говорит о наступлении "
            "обстоятельств, предусмотренных договором, при которых сумма платежа "
            "засчитывается в счёт исполнения.",
        ),
    },
    "surety_enforceable": {
        "valid_main_obligation": (
            "main_obligation_exists AND NOT main_obligation_invalid",
            "Сводка, та же что и в неустойке и залоге. Поручительство "
            "акцессорно (пункт 3 статьи 329 ГК РФ), и модель разделяет "
            "существование основного обязательства и его действительность.",
        ),
        "written_surety": (
            "suretyship_created AND suretyship_writing_observed",
            "Сводка. Договор поручительства и его письменная форма — два факта; "
            "несоблюдение формы влечёт недействительность (статья 362 ГК РФ).",
        ),
        "scope": (
            "surety_scope_proven",
            "Переименование: доказанность объёма ответственности поручителя (статья 363 ГК РФ).",
        ),
        "terminated": (
            "surety_terminated",
            "Переименование. Поручительство прекращается по основаниям статьи 367 ГК "
            "РФ — прекращением основного обязательства, истечением срока и другими; "
            "модель сводит их к одному факту прекращения.",
        ),
    },
    "judicial_termination_prerequisites": {
        "judicial_ground": (
            "(substantial_breach_ground_satisfied OR other_legal_or_contractual_ground_proven "
            "OR changed_circumstances_ground_satisfied)",
            "Сводка трёх оснований судебного расторжения: существенное нарушение "
            "(подпункт 1 пункта 2 статьи 450 ГК РФ), иной случай, предусмотренный "
            "законом или договором (подпункт 2), и существенное изменение "
            "обстоятельств (статья 451). Объявление называло их «судебным "
            "основанием» и не позволяло увидеть, что оснований три.",
        ),
    },
}


#: Сокращения существующих фактов: имена, которые сверка не сочла вопросами.
#:
#: Сверка исключила их из списка вопросов, потому что они не несут содержания —
#: `concluded` при `contract_concluded`, `form` при `assignment_form_observed`.
#: Для доказательства следования они всё равно нужны: без них объявленное
#: правило не с чем сравнивать. Обоснования здесь короткие: спорного в них нет.
ABBREVIATION_MEANINGS: dict[str, dict[str, str]] = {
    "installment_refusal": {"seller_refusal": "seller_chose_installment_refusal"},
    "notice_defense": {
        "proven_prejudice": "seller_proved_notice_prejudice",
        "seller_knowledge": "seller_knew_or_should_have_known_discrepancy",
    },
    "quality_remedy": {
        "defect": "quality_defect",
        "timely_claim": "defect_discovered_within_applicable_period",
    },
    "sale_contract": {
        "concluded": "contract_concluded",
        "transfer_ownership_duty": "seller_transfer_ownership_duty",
        "acceptance_duty": "buyer_acceptance_duty",
        "payment_duty": "buyer_payment_duty",
        "name": "goods_name_agreed",
        "quantity": "quantity_determinable",
    },
    "title_return": {"seller_return_demand": "seller_required_goods_return"},
    "transfer_duty": {
        "completed": "goods_transfer_completed",
        "delivery": "delivery_obligation AND goods_delivered_to_buyer",
        "carrier_handover": "shipment_contract AND goods_handed_to_carrier",
    },
    "article_520_cover": {"documented_expenses": "substitute_expenses_reasonable_documented"},
    "counterperformance_suspension": {
        "reciprocal_due": "reciprocal_obligations AND counterperformance_due",
        "delivered_notice": "suspension_notice_delivered",
    },
    "damages": {
        "breach": "breach_established",
        "claimed_loss": "loss_claimed",
        "causation": "causation_proven",
    },
    "indemnity": {
        "occurred_loss": "indemnity_loss_occurred",
        "amount_method": "indemnity_amount_or_method_agreed",
        "bad_faith": "indemnity_bad_faith_bar",
    },
    "proper_performance": {"tendered": "performance_tendered"},
    "third_party_acceptance": {
        "third_party_tendered": "third_party_performance_tendered",
        "personal_performance": "personal_performance_required",
    },
    "assignment_effective": {
        "assignment_agreement": "assignment_agreement_concluded",
        "form": "assignment_form_observed",
        "identifiable_claim": (
            "(assigned_claim_exists AND assigned_claim_identified OR future_claim_determinable)"
        ),
        "required_consent": "(NOT debtor_consent_required OR debtor_consent_obtained)",
    },
    "contract_transfer_effective": {
        "all_parties_consent": "all_parties_consented_contract_transfer"
    },
    "debt_forgiveness_effective": {
        "forgiveness_notice": "debt_forgiveness_declared AND debt_forgiveness_notice_delivered",
        "objection": "debtor_objected_forgiveness",
        "third_party_prejudice": "third_party_rights_prejudiced",
    },
    "notary_deposit_discharge": {"deposit_made": "notary_or_court_deposit_made"},
    "novation_effective": {
        "agreement": "novation_agreed",
        "new_terms": "new_obligation_terms_agreed",
        "form": "novation_form_observed",
    },
    "setoff_effective": {"amount_proven": "set_off_amount_proven"},
    "guarantee_demand_payable": {"abuse": "beneficiary_abuse_proven"},
    "penalty_security_enforceable": {"breach": "main_obligation_breached"},
    "pledge_foreclosure_prerequisites": {
        "breach": "main_obligation_breached",
        # Ссылка на другое объявленное правило: раскрывается его исполняемым
        # соответствием, а не отдельным предикатом.
        "pledge_valid_between_parties": "pledge_valid_between_parties",
    },
    "pledge_valid_between_parties": {"form": "pledge_form_observed"},
    "judicial_termination_prerequisites": {"pretrial_order_satisfied": "pretrial_order_satisfied"},
}


class ClosedCondition(BaseModel):
    """Одно объявленное имя и то, чем оно оказалось."""

    declared_rule: str
    declared_name: str
    model_expression: str
    was_open_question: bool
    reason_ru: str = ""


class RuleClosure(BaseModel):
    """Итог по одному объявленному правилу."""

    declared_rule: str
    executed_rule: str
    implication_proven: bool
    stricter_than_declared: bool
    counterexample: dict[str, bool] = Field(default_factory=dict)
    conditions: list[ClosedCondition] = Field(default_factory=list)


class ClosureReport(BaseModel):
    version: str = RULE_CLOSURE_VERSION
    rules: list[RuleClosure] = Field(default_factory=list)
    open_questions_closed: int = 0
    abbreviations_resolved: int = 0
    unproven: list[str] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


def _substitute(node: Node, table: dict[str, Node]) -> Node:
    """Заменить имена в разобранном выражении на выражения из таблицы."""
    kind = node[0]
    if kind == "var":
        return table.get(node[1], node)
    if kind == "not":
        return ("not", _substitute(node[1], table))
    return (kind, tuple(_substitute(part, table) for part in node[1]))


#: Институт, которому принадлежит объявленное правило.
#:
#: Ведётся явно, потому что имена правил в пакете не уникальны: 25 имён
#: повторяются в разных модулях, и `quality_remedies_available` есть и в
#: купле-продаже, и в поставке. Плоский поиск по всем модулям молча брал
#: последний найденный и доказывал следование не тому правилу — ровно та же
#: ошибка, о которой предупреждает сверка: инструмент, не различающий области
#: видимости, выдаёт не пустой результат, а ложное утверждение.
INSTITUTE_OF: dict[str, str] = {
    "eviction_remedy": "sale",
    "installment_refusal": "sale",
    "notice_defense": "sale",
    "quality_remedy": "sale",
    "sale_contract": "sale",
    "sale_refusal": "sale",
    "title_return": "sale",
    "transfer_duty": "sale",
    "article_520_cover": "supply",
    "article_520_withholding": "supply",
    "negotiation_response_breach": "supply",
    "counterperformance_suspension": "performance_remedies",
    "damages": "performance_remedies",
    "indemnity": "performance_remedies",
    "proper_performance": "performance_remedies",
    "third_party_acceptance": "performance_remedies",
    "assignment_effective": "obligation_dynamics",
    "contract_transfer_effective": "obligation_dynamics",
    "debt_forgiveness_effective": "obligation_dynamics",
    "notary_deposit_discharge": "obligation_dynamics",
    "novation_effective": "obligation_dynamics",
    "setoff_effective": "obligation_dynamics",
    "accessory_security_displaced_by_main_invalidity": "security",
    "guarantee_demand_payable": "security",
    "penalty_security_enforceable": "security",
    "pledge_foreclosure_prerequisites": "security",
    "pledge_valid_between_parties": "security",
    "security_payment_credit_available": "security",
    "surety_enforceable": "security",
    "judicial_termination_prerequisites": "termination",
}


def _executed_rules(institute: str) -> dict[str, Node]:
    """Исполняемые правила одного института.

    Читается ровно один модуль. Институты самодостаточны: правило ссылается на
    выводы своего института и на предикаты входа, но не на чужие выводы.
    """
    from causa.reasoning.rule_parity import collect_executed

    path = Path(__file__).resolve().parents[1] / "institutional" / "contracts" / f"{institute}.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    rules: dict[str, Node] = {}
    for _, (found, _problems) in collect_executed(tree).items():
        rules.update(found)
    return rules


def _inline(node: Node, rules: dict[str, Node], seen: frozenset[str] = frozenset()) -> Node:
    """Раскрыть промежуточные выводы до предикатов входа.

    Без раскрытия следование доказать нельзя: исполняемое правило ссылается на
    другие выводы (`setoff_prerequisites`, `pledge_foreclosure_bar`), а
    объявленное — на условия, которые внутри них и лежат.
    """
    kind = node[0]
    if kind == "var":
        name = node[1]
        if name in rules and name not in seen:
            return _inline(rules[name], rules, seen | {name})
        return node
    if kind == "not":
        return ("not", _inline(node[1], rules, seen))
    return (kind, tuple(_inline(part, rules, seen) for part in node[1]))


def close_rule(declared_rule: str) -> RuleClosure:
    """Доказать, что исполняемое правило влечёт объявленное.

    Направление выбрано не произвольно. Если исполняемое влечёт объявленное, то
    ни одно объявленное условие не потеряно: всякий набор фактов, на котором
    срабатывает модель, удовлетворяет и объявлению. Обратное следование не
    требуется — исполняемое правило почти всегда строже, и требовать равенства
    значило бы объявить дефектом каждое уточнение, добавленное после объявления.
    """
    declared_text = DECLARED_RULES[declared_rule]
    executed_name = EXECUTED_RULE_OF.get(declared_rule, declared_rule)
    rules = _executed_rules(INSTITUTE_OF[declared_rule])
    if executed_name not in rules:
        raise KeyError(f"Исполняемого правила {executed_name!r} в пакете нет.")

    table: dict[str, Node] = {}
    conditions: list[ClosedCondition] = []
    for name, (expression, reason) in OPEN_QUESTION_MEANINGS_RU.get(declared_rule, {}).items():
        table[name] = parse_expression(expression)
        conditions.append(
            ClosedCondition(
                declared_rule=declared_rule,
                declared_name=name,
                model_expression=expression,
                was_open_question=True,
                reason_ru=reason,
            )
        )
    for name, expression in ABBREVIATION_MEANINGS.get(declared_rule, {}).items():
        table[name] = parse_expression(expression)
        conditions.append(
            ClosedCondition(
                declared_rule=declared_rule,
                declared_name=name,
                model_expression=expression,
                was_open_question=False,
            )
        )

    declared = _inline(_substitute(parse_expression(declared_text), table), rules)
    executed = _inline(rules[executed_name], rules)

    symbols: dict[str, object] = {}
    solver = Solver()
    solver.add(compile_to_z3(executed, symbols))
    solver.add(Not(compile_to_z3(declared, symbols)))
    proven = solver.check() != sat
    counterexample: dict[str, bool] = {}
    if not proven:
        model = solver.model()
        counterexample = {
            name: bool(model.eval(symbol, model_completion=True))
            for name, symbol in sorted(symbols.items())
        }

    reverse = Solver()
    reverse_symbols: dict[str, object] = {}
    reverse.add(compile_to_z3(declared, reverse_symbols))
    reverse.add(Not(compile_to_z3(executed, reverse_symbols)))
    stricter = reverse.check() == sat

    return RuleClosure(
        declared_rule=declared_rule,
        executed_rule=executed_name,
        implication_proven=proven,
        stricter_than_declared=stricter,
        counterexample=counterexample,
        conditions=sorted(conditions, key=lambda entry: entry.declared_name),
    )


def audit_rule_closure() -> ClosureReport:
    """Закрыть все вопросы сверки разом и посчитать итог."""
    closures = [close_rule(name) for name in sorted(DECLARED_RULES)]
    open_closed = sum(
        entry.was_open_question for closure in closures for entry in closure.conditions
    )
    abbreviations = sum(
        not entry.was_open_question for closure in closures for entry in closure.conditions
    )
    unproven = [c.declared_rule for c in closures if not c.implication_proven]
    stricter = [c.declared_rule for c in closures if c.stricter_than_declared]
    notes = [
        f"Закрыто вопросов: {open_closed}. Ни одно объявленное имя не оказалось забытым "
        "условием: все они — переименования или сводки нескольких предикатов.",
        f"Разрешено сокращений: {abbreviations}. Они не были вопросами, но без них "
        "объявленное правило не с чем сравнивать.",
        f"Правил, где исполняемое строже объявленного: {len(stricter)} из {len(closures)}. "
        "Поэтому доказывается следование, а не равенство: равенство объявило бы дефектом "
        "каждое уточнение, добавленное к правилу после того, как объявление написали.",
        "Доказано соответствие объявленного и исполняемого, а не правильность "
        "исполняемого. Верно ли правило передаёт норму ГК РФ — вопрос к юристу, и ответ "
        "записан рядом с каждым условием по-русски, со ссылкой на статью.",
    ]
    if unproven:
        notes.append(
            "Следование не доказано для: "
            + ", ".join(unproven)
            + ". Это значит, что объявленное условие действительно потеряно, а не "
            "переименовано."
        )
    return ClosureReport(
        rules=closures,
        open_questions_closed=open_closed,
        abbreviations_resolved=abbreviations,
        unproven=unproven,
        notes_ru=notes,
    )


def render_closure_ru(report: ClosureReport) -> str:
    """Человекочитаемый отчёт о закрытии вопросов."""
    lines = ["# Закрытие вопросов сверки правил", ""]
    for note in report.notes_ru:
        lines.append(f"- {note}")
    lines.append("")
    for closure in report.rules:
        mark = "доказано" if closure.implication_proven else "НЕ ДОКАЗАНО"
        strict = ", исполняемое строже" if closure.stricter_than_declared else ""
        lines.append(f"## `{closure.declared_rule}` → `{closure.executed_rule}` — {mark}{strict}")
        lines.append("")
        for entry in closure.conditions:
            if not entry.was_open_question:
                continue
            lines.append(f"**`{entry.declared_name}`** → `{entry.model_expression}`")
            lines.append("")
            lines.append(entry.reason_ru)
            lines.append("")
    return "\n".join(lines)


def closure_payload(report: ClosureReport) -> dict:
    """Отчёт в виде данных для артефакта."""
    return report.model_dump(mode="json")
