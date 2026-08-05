from causa.core.models import LegalSource, SourceType


SYNTHETIC_CONTRACT_SOURCES = [
    LegalSource(
        id="synthetic-ru-constitutional-contract-guarantee",
        title="Синтетическая конституционная гарантия договорных отношений",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетический источник конституционного уровня: анализ договорных отношений "
            "должен осуществляться в пределах конституционно защищаемого правового порядка."
        ),
        valid_from="2020-01-01",
        metadata={
            "synthetic": True,
            "topic": "authority_framework",
            "authority_level": "constitutional",
            "specificity": "general",
        },
    ),
    LegalSource(
        id="synthetic-ru-contract-supply-delivery-duty",
        title="Синтетическая норма об обязанности поставить товар",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическая норма: в отношениях поставки поставщик обязан передать товар "
            "в согласованный срок, если отсутствует применимое основание освобождения."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "delivery_duty"},
    ),
    LegalSource(
        id="synthetic-ru-contract-general-performance-duty",
        title="Синтетическая общая норма о надлежащем исполнении обязательств",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическая общая норма: договорные обязательства должны исполняться "
            "надлежащим образом в соответствии с условиями обязательства."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "performance_duty", "specificity": "general"},
    ),
    LegalSource(
        id="synthetic-ru-contract-supply-specific-delivery-duty",
        title="Синтетическая специальная норма о сроке поставки",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическая специальная норма: срок исполнения договора поставки "
            "оценивается с учетом специальных правил о поставке."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "delivery_duty", "specificity": "special"},
    ),
    LegalSource(
        id="synthetic-ru-contract-supply-delivery-case-law",
        title="Синтетическое судебное толкование правил о поставке",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическая судебная позиция: актуальное судебное толкование может "
            "учитываться при анализе поставки в отсутствие применимой нормы закона."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "delivery_duty", "specificity": "special"},
    ),
    LegalSource(
        id="synthetic-ru-regulatory-supply-delivery-record",
        title="Синтетическое подзаконное правило об оформлении поставки",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетический подзаконный источник: документы о поставке оформляются "
            "по специальной форме учета."
        ),
        valid_from="2020-01-01",
        metadata={
            "synthetic": True,
            "topic": "delivery_duty",
            "authority_level": "regulatory",
            "specificity": "special",
        },
    ),
    LegalSource(
        id="synthetic-ru-contract-supply-delivery-term",
        title="Синтетическое договорное условие о графике поставки",
        source_type=SourceType.CONTRACT,
        text=(
            "Синтетическое условие договора: стороны согласовали специальный "
            "график поставки товара."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "delivery_duty", "specificity": "special"},
    ),
    LegalSource(
        id="synthetic-ru-contract-supplier-delivery-fact",
        title="Синтетический факт исполнения поставки",
        source_type=SourceType.FACT,
        text="Синтетический факт: поставщик зафиксировал событие передачи товара.",
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "delivery_duty"},
    ),
    LegalSource(
        id="synthetic-case-supply-1-reviewed-evidence",
        title="Синтетическая проверенная запись доказательств по делу о поставке",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая проверенная запись: даты поставки и узкий набор утверждений "
            "о фактах одобрены для демонстрационного анализа Этапа 0."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-contract-supply-delivery-duty-v1",
        title="Синтетическая норма о сроке поставки, редакция 1",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическая редакция 1: поставщик обязан передать товар в согласованный "
            "срок, если отсутствует применимое основание освобождения."
        ),
        valid_from="2020-01-01",
        valid_to="2025-12-31",
        metadata={"synthetic": True, "topic": "delivery_duty", "revision": "v1"},
    ),
    LegalSource(
        id="synthetic-ru-contract-supply-delivery-duty-v2",
        title="Синтетическая норма о сроке поставки, редакция 2",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическая редакция 2: для отношений, оцениваемых с 2026 года, необходимо "
            "проверить согласованный срок, фактическое исполнение и основание освобождения."
        ),
        valid_from="2026-01-01",
        metadata={"synthetic": True, "topic": "delivery_duty", "revision": "v2"},
    ),
    LegalSource(
        id="synthetic-ru-contract-delivery-term",
        title="Синтетическое правило о согласованном сроке поставки",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическая норма: если стороны согласовали дату поставки, исполнение "
            "оценивается применительно к этой дате."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "delivery_term"},
    ),
    LegalSource(
        id="synthetic-ru-contract-valid-excuse",
        title="Синтетическое правило об основании освобождения от ответственности",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическая норма: применимое договорное или законное основание "
            "освобождения может исключить вывод о нарушении при просрочке."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "valid_excuse"},
    ),
    LegalSource(
        id="synthetic-ru-contract-acceptance-defects",
        title="Синтетическое правило о приемке и недостатках товара",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическая норма: приемка и недостатки товара оцениваются отдельно "
            "от вопроса о соблюдении срока поставки."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "acceptance_defects"},
    ),
    LegalSource(
        id="synthetic-ru-contract-payment-duty",
        title="Синтетическая норма об обязанности покупателя оплатить товар",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическая норма: обязанность покупателя по оплате не прекращается "
            "из-за несвязанного довода о поставке без правового анализа оснований."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "payment_duty"},
    ),
    LegalSource(
        id="synthetic-ru-contract-penalty-reduction",
        title="Синтетическая граница применения снижения неустойки",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическая норма: снижение неустойки не должно автоматически "
            "устранять всю ответственность за нарушение обязательства."
        ),
        valid_from="2020-01-01",
        metadata={"synthetic": True, "topic": "penalty_reduction"},
    ),
    LegalSource(
        id="synthetic-ru-gk432-contract-formation-model-v1",
        title="Синтетическая проверенная модель заключения договора по статье 432 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: договорное основание проверяется через "
            "согласование предмета, обязательных и заявленных сторонами существенных условий."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "formation_article_432",
            "legal_reference": "ГК РФ, статья 432",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk435-offer-model-v1",
        title="Синтетическая проверенная модель оферты по статье 435 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: оферта должна быть адресована контрагенту, "
            "быть достаточно определенной и выражать намерение оферента быть связанным."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "formation_article_435",
            "legal_reference": "ГК РФ, статья 435",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk438-443-acceptance-model-v1",
        title="Синтетическая проверенная модель акцепта по статьям 438 и 443 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: полный безоговорочный ответ, своевременные "
            "действия по исполнению и ответ на иных условиях проверяются раздельно."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "formation_articles_438_443",
            "legal_reference": "ГК РФ, статьи 438 и 443",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum49-formation-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ о заключении договора",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: воля сторон может следовать из "
            "поведения, а принятое исполнение ограничивает недобросовестные возражения "
            "о незаключенности договора."
        ),
        valid_from="2018-12-25",
        metadata={
            "synthetic": True,
            "topic": "formation_plenum_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 25.12.2018 № 49",
            "basis_url": "https://vsrf.ru/documents/own/27540/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-formation-evidence",
        title="Синтетическая проверенная запись фактов о заключении договора поставки",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: согласование условий и своевременное начало "
            "исполнения адресатом оферты одобрены для демонстрационного анализа Этапа 0."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "formation_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk425-contract-effect-model-v1",
        title="Синтетическая проверенная модель действия договора во времени по статье 425 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: вступление договора в силу, распространение "
            "условий на предшествующие отношения, окончание срока действия и сохранение "
            "ответственности за нарушение проверяются раздельно."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "temporal_effect_article_425",
            "legal_reference": "ГК РФ, статья 425",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk433-conclusion-moment-model-v1",
        title="Синтетическая проверенная модель момента заключения договора по статье 433 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: момент заключения определяется получением "
            "акцепта, а для реального и подлежащего регистрации договора — передачей "
            "имущества и государственной регистрацией соответственно."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "temporal_effect_article_433",
            "legal_reference": "ГК РФ, статья 433",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-temporal-effect-evidence",
        title="Синтетическая проверенная запись фактов о действии договора во времени",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: консенсуальный договор поставки заключен получением "
            "акцепта и вступил в силу, срок действия определен и истек, а нарушение "
            "допущено в период действия договора."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "temporal_effect_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk195-200-limitation-framework-v1",
        title="Синтетическая проверенная модель исковой давности по статьям 195–200 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: понятие исковой давности, общий трехлетний "
            "и специальные сроки, предельный десятилетний срок и момент начала течения "
            "проверяются раздельно."
        ),
        valid_from="2013-09-01",
        metadata={
            "synthetic": True,
            "topic": "limitation_articles_195_200",
            "legal_reference": "ГК РФ, статьи 195–200",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk202-208-limitation-effects-v1",
        title="Синтетическая проверенная модель приостановления, перерыва и применения давности",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: приостановление и перерыв течения, период "
            "судебной защиты, заявление стороны, восстановление срока, дополнительные "
            "требования и исключения проверяются как самостоятельные вопросы."
        ),
        valid_from="2013-09-01",
        metadata={
            "synthetic": True,
            "topic": "limitation_articles_202_208",
            "legal_reference": "ГК РФ, статьи 199, 202–208",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-limitation-evidence",
        title="Синтетическая проверенная запись фактов об исковой давности",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: требование о нарушении поставки подпадает под исковую "
            "давность, нарушение и ответчик известны, но трехлетний срок в демонстрационном "
            "деле еще не истек."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "limitation_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk431-interpretation-model-v1",
        title="Синтетическая проверенная модель толкования договора по статье 431 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: сначала принимается во внимание буквальное "
            "значение слов и выражений, при неясности оно сопоставляется с другими "
            "условиями и смыслом договора в целом."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "interpretation_article_431_literal",
            "legal_reference": "ГК РФ, статья 431",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk431-common-intent-model-v1",
        title="Синтетическая проверенная модель установления общей воли сторон",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: если буквальное толкование не позволяет "
            "определить содержание, выясняется действительная общая воля с учетом цели "
            "договора, переговоров, практики, обычаев и последующего поведения сторон."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "interpretation_article_431_common_intent",
            "legal_reference": "ГК РФ, статья 431",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-interpretation-evidence",
        title="Синтетическая проверенная запись фактов о толковании условия договора",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: заявлен спор о толковании условия о сроке поставки; "
            "буквальное значение ясно и согласуется с другими условиями и смыслом "
            "договора в целом."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "interpretation_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk158-165-form-framework-v1",
        title="Синтетическая проверенная модель формы сделки по статьям 158–165 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: устная, простая письменная и нотариальная "
            "форма, требования к их совершению и последствия несоблюдения проверяются "
            "раздельно."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "form_articles_158_165",
            "legal_reference": "ГК РФ, статьи 158–165",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk160-434-written-form-model-v1",
        title="Синтетическая проверенная модель способов соблюдения письменной формы",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: подписанный сторонами документ, обмен "
            "документами и действительная электронная подпись рассматриваются как "
            "допустимые способы соблюдения письменной формы."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "form_articles_160_434",
            "legal_reference": "ГК РФ, статьи 160 и 434",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-form-evidence",
        title="Синтетическая проверенная запись фактов о форме сделки",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: для договора поставки требуется простая письменная "
            "форма; она соблюдена подписанным сторонами документом, нотариальная форма "
            "не требуется."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "form_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk429-preliminary-framework-v1",
        title="Синтетическая проверенная модель предварительного договора по статье 429 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: заключение и форма предварительного договора, "
            "определенность предмета основного договора и согласование спорных условий "
            "проверяются раздельно (пункты 1–3 статьи 429 ГК РФ)."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "preliminary_article_429_conclusion",
            "legal_reference": "ГК РФ, статья 429, пункты 1–3",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk429-445-preliminary-compulsion-v1",
        title="Синтетическая проверенная модель понуждения к заключению основного договора",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: срок заключения основного договора, уклонение "
            "стороны, понуждение к заключению и шестимесячный срок требования, а также "
            "прекращение обязательств проверяются раздельно (пункты 4–6 статьи 429, "
            "пункт 4 статьи 445 ГК РФ)."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "preliminary_articles_429_445",
            "legal_reference": "ГК РФ, статья 429, пункты 4–6; статья 445, пункт 4",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-preliminary-evidence",
        title="Синтетическая проверенная запись фактов о предварительном договоре",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: заключен предварительный договор поставки в надлежащей "
            "форме, предмет основного договора определен, спорные условия согласованы, "
            "срок заключения не истек, уклонения нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "preliminary_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk430-third-party-framework-v1",
        title="Синтетическая проверенная модель договора в пользу третьего лица по статье 430 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: заключение договора в пользу третьего лица, "
            "определённость третьего лица и предоставленное ему право требовать "
            "исполнения проверяются раздельно (пункт 1 статьи 430 ГК РФ)."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "third_party_article_430_right",
            "legal_reference": "ГК РФ, статья 430, пункт 1",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk430-third-party-change-v1",
        title="Синтетическая проверенная модель связанности сторон и отказа третьего лица",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: после выражения третьим лицом намерения "
            "воспользоваться правом изменение и расторжение договора требуют его "
            "согласия; при отказе третьего лица право может перейти к кредитору "
            "(пункты 2 и 4 статьи 430 ГК РФ)."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "third_party_article_430_change",
            "legal_reference": "ГК РФ, статья 430, пункты 2 и 4",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-third-party-evidence",
        title="Синтетическая проверенная запись фактов о договоре в пользу третьего лица",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: договор поставки заключён в пользу определённого "
            "грузополучателя, которому предоставлено право требовать исполнения; "
            "намерения воспользоваться правом ещё не выражено."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "third_party_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk426-public-contract-framework-v1",
        title="Синтетическая проверенная модель публичного договора по статье 426 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: публичный характер деятельности, обязанность "
            "заключить договор с каждым обратившимся при наличии возможности и "
            "недопустимость необоснованного отказа проверяются раздельно "
            "(пункты 1 и 3 статьи 426 ГК РФ)."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "public_contract_article_426_duty",
            "legal_reference": "ГК РФ, статья 426, пункты 1 и 3",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk426-public-contract-terms-v1",
        title="Синтетическая проверенная модель единых условий публичного договора",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: недопустимость предпочтения, единство цены и "
            "иных условий для потребителей соответствующей категории и ничтожность "
            "условий, не соответствующих публичному режиму, проверяются раздельно "
            "(пункты 2 и 5 статьи 426 ГК РФ)."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "public_contract_article_426_terms",
            "legal_reference": "ГК РФ, статья 426, пункты 2 и 5",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-public-contract-evidence",
        title="Синтетическая проверенная запись фактов о публичном договоре",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: поставщик действует в публичном режиме, контрагент "
            "обратился, исполнение возможно, условия едины для соответствующей "
            "категории, необоснованного отказа и предпочтения нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "public_contract_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk428-adhesion-framework-v1",
        title="Синтетическая проверенная модель договора присоединения по статье 428 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: определение условий одной стороной в "
            "стандартных формах и принятие их присоединением в целом, а также "
            "распространение режима при явном неравенстве переговорных возможностей "
            "проверяются раздельно (пункты 1 и 3 статьи 428 ГК РФ)."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "adhesion_article_428_regime",
            "legal_reference": "ГК РФ, статья 428, пункты 1 и 3",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk428-adhesion-relief-v1",
        title="Синтетическая проверенная модель изменения и расторжения договора присоединения",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: лишение обычных прав, исключение "
            "ответственности другой стороны, явно обременительные условия и "
            "ограничение для присоединившегося предпринимателя, знавшего условия, "
            "проверяются раздельно (пункт 2 статьи 428 ГК РФ)."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "adhesion_article_428_relief",
            "legal_reference": "ГК РФ, статья 428, пункт 2",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-adhesion-evidence",
        title="Синтетическая проверенная запись фактов о договоре присоединения",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: условия поставки определены поставщиком в стандартной "
            "форме и приняты присоединением; обременительных условий, лишения прав и "
            "исключения ответственности нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "adhesion_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk431-2-representations-framework-v1",
        title="Синтетическая проверенная модель заверений об обстоятельствах по статье 431.2 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: недостоверное заверение, имеющее значение "
            "для договора, доверие полагавшейся стороны и основание ответственности "
            "проверяются раздельно (пункт 1 статьи 431.2 ГК РФ)."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "representations_article_431_2_liability",
            "legal_reference": "ГК РФ, статья 431.2, пункт 1",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk431-2-representations-remedies-v1",
        title="Синтетическая проверенная модель последствий недостоверного заверения",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: возмещение убытков или неустойки независимо "
            "от действительности договора, отказ от договора при существенном значении "
            "заверения и оспаривание при обмане проверяются раздельно "
            "(пункты 2 и 3 статьи 431.2 ГК РФ)."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "representations_article_431_2_remedies",
            "legal_reference": "ГК РФ, статья 431.2, пункты 2 и 3",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-representations-evidence",
        title="Синтетическая проверенная запись фактов о заверениях об обстоятельствах",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: поставщик дал заверения о качестве и правовом "
            "положении товара, имеющие значение для покупателя; недостоверности "
            "заверений не установлено."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "representations_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk434-1-precontractual-framework-v1",
        title="Синтетическая проверенная модель преддоговорной ответственности по статье 434.1 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: свобода переговоров, обязанность действовать "
            "добросовестно, недобросовестное предоставление информации и внезапное "
            "неоправданное прекращение переговоров проверяются раздельно "
            "(пункты 1 и 2 статьи 434.1 ГК РФ)."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "precontractual_article_434_1_good_faith",
            "legal_reference": "ГК РФ, статья 434.1, пункты 1 и 2",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk434-1-precontractual-remedies-v1",
        title="Синтетическая проверенная модель последствий недобросовестных переговоров",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: нарушение конфиденциальности, возмещение "
            "убытков независимо от заключения договора и ничтожность соглашения об "
            "ограничении ответственности за недобросовестные действия проверяются "
            "раздельно (пункты 3–5 и 7 статьи 434.1 ГК РФ)."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "precontractual_article_434_1_remedies",
            "legal_reference": "ГК РФ, статья 434.1, пункты 3–5 и 7",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-precontractual-evidence",
        title="Синтетическая проверенная запись фактов о преддоговорной ответственности",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: стороны вели переговоры о поставке добросовестно; "
            "недостоверной информации, внезапного прекращения и нарушения "
            "конфиденциальности не установлено."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "precontractual_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk429-2-option-framework-v1",
        title="Синтетическая проверенная модель опциона на заключение договора по статье 429.2 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: предоставление безотзывной оферты, "
            "определённость существенных условий, возмездность опциона, акцепт в срок "
            "и передаваемость права проверяются раздельно (статья 429.2 ГК РФ)."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "option_article_429_2_offer",
            "legal_reference": "ГК РФ, статья 429.2",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk429-3-option-contract-v1",
        title="Синтетическая проверенная модель опционного договора по статье 429.3 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: право требовать совершения действий в срок, "
            "прекращение договора при незаявлении требования и невозвратность платежа "
            "проверяются раздельно (статья 429.3 ГК РФ)."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "option_article_429_3_contract",
            "legal_reference": "ГК РФ, статья 429.3",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-option-evidence",
        title="Синтетическая проверенная запись фактов об опционных конструкциях",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: покупателю предоставлен возмездный опцион на "
            "заключение договора поставки с определёнными условиями; акцепт совершён "
            "в установленный срок."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "option_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk429-1-framework-agreement-v1",
        title="Синтетическая проверенная модель рамочного договора по статье 429.1 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: определение общих условий обязательственных "
            "взаимоотношений, их конкретизация отдельными договорами или заявками и "
            "применение общих условий к неурегулированным отношениям проверяются "
            "раздельно (статья 429.1 ГК РФ)."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "framework_article_429_1_agreement",
            "legal_reference": "ГК РФ, статья 429.1",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk429-4-subscription-agreement-v1",
        title="Синтетическая проверенная модель абонентского договора по статье 429.4 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: право требовать исполнение по требованию "
            "абонента за согласованные платежи и обязанность вносить плату независимо "
            "от затребования исполнения проверяются раздельно (статья 429.4 ГК РФ)."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "framework_article_429_4_subscription",
            "legal_reference": "ГК РФ, статья 429.4",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-framework-evidence",
        title="Синтетическая проверенная запись фактов о рамочном и абонентском договоре",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: стороны заключили рамочный договор поставки с "
            "определёнными общими условиями, конкретизированный отдельными заявками; "
            "абонентское обслуживание не согласовано."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "framework_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk421-422-freedom-of-contract-v1",
        title="Синтетическая проверенная модель свободы договора по статьям 421 и 422 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: свобода заключения договора, непоименованный и "
            "смешанный договор, определение условий по усмотрению сторон и соответствие "
            "договора императивным нормам проверяются раздельно (статьи 421 и 422 ГК РФ)."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "freedom_articles_421_422",
            "legal_reference": "ГК РФ, статьи 421 и 422",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk423-424-onerousness-and-price-v1",
        title="Синтетическая проверенная модель возмездности и цены по статьям 423 и 424 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: презумпция возмездности договора, цена по "
            "соглашению, применение регулируемых цен и определение цены за сопоставимые "
            "товары, работы или услуги проверяются раздельно (статьи 423 и 424 ГК РФ)."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "onerousness_and_price_articles_423_424",
            "legal_reference": "ГК РФ, статьи 423 и 424",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-freedom-evidence",
        title="Синтетическая проверенная запись фактов о свободе договора и цене",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: договор поставки заключён свободно, является "
            "поименованным и возмездным, цена согласована сторонами; понуждение к "
            "заключению отсутствует."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "freedom_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk445-446-mandatory-conclusion-v1",
        title="Синтетическая проверенная модель обязательного заключения по статьям 445 и 446 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: обязанность заключить договор, направление "
            "оферты или проекта, уклонение обязанной стороны, понуждение к заключению, "
            "возмещение убытков и определение спорных условий судом проверяются "
            "раздельно (статьи 445 и 446 ГК РФ)."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "mandatory_conclusion_articles_445_446",
            "legal_reference": "ГК РФ, статьи 445 и 446",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk447-449-auction-v1",
        title="Синтетическая проверенная модель заключения договора на торгах по статьям 447–449 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: заключение договора на торгах, определение "
            "победителя, подписание протокола о результатах, уклонение победителя и "
            "недействительность торгов, проведённых с нарушением правил, проверяются "
            "раздельно (статьи 447–449 ГК РФ)."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "auction_articles_447_449",
            "legal_reference": "ГК РФ, статьи 447–449",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-procedure-evidence",
        title="Синтетическая проверенная запись фактов о порядке заключения договора",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: договор поставки заключён в обычном порядке без "
            "обязательного заключения и без проведения торгов; понуждение и оспаривание "
            "торгов отсутствуют."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "procedure_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk307-308-obligation-concept-v1",
        title="Синтетическая проверенная модель понятия и сторон обязательства по статьям 307 и 308 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: понятие обязательства и право кредитора "
            "требовать исполнения, добросовестность сторон и правило о том, что "
            "обязательство не создаёт обязанностей для не участвующих в нём лиц, "
            "проверяются раздельно (статьи 307 и 308 ГК РФ)."
        ),
        valid_from="1995-01-01",
        metadata={
            "synthetic": True,
            "topic": "obligation_concept_articles_307_308",
            "legal_reference": "ГК РФ, статьи 307 и 308",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk3081-3083-obligation-types-and-protection-v1",
        title="Синтетическая проверенная модель альтернативных, факультативных обязательств и защиты кредитора по статьям 308.1–308.3 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: альтернативное обязательство и выбор предмета, "
            "факультативное обязательство и право замены, а также защита прав кредитора — "
            "исполнение в натуре и судебная неустойка — проверяются раздельно "
            "(статьи 308.1, 308.2 и 308.3 ГК РФ)."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "obligation_types_and_protection_articles_3081_3083",
            "legal_reference": "ГК РФ, статьи 308.1–308.3",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-general-obligations-evidence",
        title="Синтетическая проверенная запись фактов об общих положениях об обязательствах",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: обязательство поставки установлено и исполняется "
            "добросовестно; покупатель требует исполнения в натуре; обязательство не "
            "является альтернативным или факультативным."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "general_obligations_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk492-495-retail-sale-concept-v1",
        title="Синтетическая проверенная модель понятия и информации в розничной купле-продаже по статьям 492–495 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: розничная купля-продажа как публичный договор, "
            "заключение договора выдачей чека, публичная оферта и обязанность продавца "
            "предоставить информацию о товаре проверяются раздельно (статьи 492–495 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "retail_sale_concept_articles_492_495",
            "legal_reference": "ГК РФ, статьи 492–495",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk502-504-retail-exchange-and-quality-v1",
        title="Синтетическая проверенная модель обмена и качества в розничной купле-продаже по статьям 502–504 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: обмен товара надлежащего качества, права "
            "покупателя при продаже товара ненадлежащего качества и возмещение разницы в "
            "цене при замене или возврате проверяются раздельно (статьи 502–504 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "retail_exchange_and_quality_articles_502_504",
            "legal_reference": "ГК РФ, статьи 502–504",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-retail-sale-evidence",
        title="Синтетическая проверенная запись фактов о розничной купле-продаже",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является оптовой поставкой между "
            "предпринимателями и не является розничной куплей-продажей; требований об "
            "обмене или по качеству в розничном режиме не заявлено."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "retail_sale_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk525-528-state-contract-v1",
        title="Синтетическая проверенная модель государственного контракта по статьям 525–528 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: поставка для государственных и муниципальных "
            "нужд на основе государственного контракта, размещение заказа, обязательность "
            "заключения для поставщика и понуждение к заключению проверяются раздельно "
            "(статьи 525–528 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "state_contract_articles_525_528",
            "legal_reference": "ГК РФ, статьи 525–528",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk529-534-state-supply-performance-v1",
        title="Синтетическая проверенная модель исполнения поставки для госнужд по статьям 529–534 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: прикрепление покупателя, отказ покупателя от "
            "товаров, оплата по ценам контракта, поручительство заказчика и возмещение "
            "убытков поставщику проверяются раздельно (статьи 529–534 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "state_supply_performance_articles_529_534",
            "legal_reference": "ГК РФ, статьи 529–534",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-state-supply-evidence",
        title="Синтетическая проверенная запись фактов о поставке для государственных нужд",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является обычной коммерческой поставкой "
            "между предпринимателями и не связан с государственным или муниципальным "
            "контрактом; прикрепление покупателя и отказы заказчика отсутствуют."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "state_supply_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk535-536-contractation-concept-v1",
        title="Синтетическая проверенная модель понятия контрактации и обязанностей заготовителя по статьям 535 и 536 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: контрактация как передача производителем "
            "выращенной им сельскохозяйственной продукции заготовителю, приёмка по месту "
            "нахождения производителя, недопустимость отказа от соответствующей продукции "
            "и возврат отходов переработки проверяются раздельно (статьи 535 и 536 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "contractation_concept_articles_535_536",
            "legal_reference": "ГК РФ, статьи 535 и 536",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk537-538-contractation-duties-and-liability-v1",
        title="Синтетическая проверенная модель обязанностей и ответственности производителя по статьям 537 и 538 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: обязанность производителя передать продукцию в "
            "количестве и ассортименте и его ответственность за нарушение только при "
            "наличии вины проверяются раздельно (статьи 537 и 538 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "contractation_duties_and_liability_articles_537_538",
            "legal_reference": "ГК РФ, статьи 537 и 538",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-contractation-evidence",
        title="Синтетическая проверенная запись фактов о контрактации",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является обычной поставкой готовых "
            "товаров и не является контрактацией сельскохозяйственной продукции; отказ "
            "заготовителя и нарушения производителя отсутствуют."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "contractation_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk539-542-energy-supply-concept-v1",
        title="Синтетическая проверенная модель понятия энергоснабжения, количества и качества энергии по статьям 539–542 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: подача энергии через присоединённую сеть при "
            "наличии у абонента отвечающего требованиям энергопринимающего устройства и "
            "учёта, соответствие энергии договору по количеству и качеству и право абонента "
            "отказаться от оплаты некачественной энергии проверяются раздельно "
            "(статьи 539–542 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "energy_supply_concept_articles_539_542",
            "legal_reference": "ГК РФ, статьи 539–542",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk543-547-energy-supply-duties-and-interruption-v1",
        title="Синтетическая проверенная модель содержания сетей, оплаты, перерыва подачи и ответственности по статьям 543–547 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: обязанности по содержанию сетей и режиму "
            "потребления (для бытового потребителя — на организации), оплата по данным "
            "учёта, правомерность перерыва подачи только по соглашению или как неотложная "
            "мера при аварии с уведомлением и возмещение реального ущерба проверяются "
            "раздельно (статьи 543–547 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "energy_supply_duties_and_interruption_articles_543_547",
            "legal_reference": "ГК РФ, статьи 543–547",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-energy-supply-evidence",
        title="Синтетическая проверенная запись фактов об энергоснабжении",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой готовых товаров и не "
            "является договором энергоснабжения через присоединённую сеть; перерывов подачи "
            "и претензий к качеству энергии нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "energy_supply_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk549-552-real-estate-sale-concept-v1",
        title="Синтетическая проверенная модель понятия, формы и регистрации продажи недвижимости по статьям 549–552 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: продажа недвижимости как передача недвижимого "
            "имущества в собственность, письменная форма одним документом, подписанным "
            "сторонами, и государственная регистрация перехода права проверяются раздельно "
            "(статьи 549–552 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "real_estate_sale_concept_articles_549_552",
            "legal_reference": "ГК РФ, статьи 549–552",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk554-558-real-estate-sale-terms-and-transfer-v1",
        title="Синтетическая проверенная модель предмета, цены, передачи, качества и продажи жилых помещений по статьям 554–558 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: определённость предмета и согласованная цена как "
            "условия заключённости, передача по передаточному акту и уклонение как отказ, "
            "последствия ненадлежащего качества и перечень лиц при продаже жилого помещения "
            "проверяются раздельно (статьи 554–558 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "real_estate_sale_terms_and_transfer_articles_554_558",
            "legal_reference": "ГК РФ, статьи 554–558",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-real-estate-sale-evidence",
        title="Синтетическая проверенная запись фактов о продаже недвижимости",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой движимых товаров и не "
            "является продажей недвижимого имущества; передаточный акт, регистрация перехода "
            "права и претензии к качеству недвижимости отсутствуют."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "real_estate_sale_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk559-561-enterprise-sale-concept-v1",
        title="Синтетическая проверенная модель понятия, формы и удостоверения состава продажи предприятия по статьям 559–561 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: продажа предприятия как передача имущественного "
            "комплекса в целом, письменная форма одним документом с обязательными "
            "приложениями, государственная регистрация договора и удостоверение состава "
            "предприятия проверяются раздельно (статьи 559–561 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "enterprise_sale_concept_articles_559_561",
            "legal_reference": "ГК РФ, статьи 559–561",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk562-566-enterprise-sale-creditors-and-transfer-v1",
        title="Синтетическая проверенная модель прав кредиторов, передачи, недостатков и публичных интересов при продаже предприятия по статьям 562–566 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: письменное уведомление кредиторов и солидарная "
            "ответственность за перевод долга без согласия, передача по передаточному акту "
            "и регистрация перехода права, уменьшение цены при неуказанных долгах и "
            "ограничение последствий недействительности публичными интересами проверяются "
            "раздельно (статьи 562–566 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "enterprise_sale_creditors_and_transfer_articles_562_566",
            "legal_reference": "ГК РФ, статьи 562–566",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-enterprise-sale-evidence",
        title="Синтетическая проверенная запись фактов о продаже предприятия",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой отдельных товаров и не "
            "является продажей предприятия как имущественного комплекса; передаточного акта, "
            "уведомления кредиторов и регистрации перехода права нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "enterprise_sale_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk567-568-barter-concept-and-price-v1",
        title="Синтетическая проверенная модель понятия мены, применения правил о купле-продаже и разницы в цене по статьям 567 и 568 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: мена как обмен товара на товар в собственность, "
            "субсидиарное применение правил о купле-продаже, признание сторон продавцом и "
            "покупателем, презумпция равноценности и оплата разницы в цене при "
            "неравноценности проверяются раздельно (статьи 567 и 568 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "barter_concept_and_price_articles_567_568",
            "legal_reference": "ГК РФ, статьи 567 и 568",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk569-571-barter-performance-and-eviction-v1",
        title="Синтетическая проверенная модель встречного исполнения, перехода права и ответственности за изъятие по статьям 569–571 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: встречное исполнение обязанности передать товар при "
            "несовпадении сроков, одновременный переход права собственности после исполнения "
            "обеими сторонами и право требовать возврата товара и убытков при изъятии его "
            "третьим лицом проверяются раздельно (статьи 569–571 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "barter_performance_and_eviction_articles_569_571",
            "legal_reference": "ГК РФ, статьи 569–571",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-barter-evidence",
        title="Синтетическая проверенная запись фактов о мене",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является возмездной поставкой товаров за "
            "денежную оплату и не является меной товара на товар; разницы в цене, встречного "
            "исполнения и изъятия товара третьим лицом нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "barter_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk572-576-gift-concept-and-form-v1",
        title="Синтетическая проверенная модель понятия, формы, запрещения и ограничений дарения по статьям 572–576 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: дарение как безвозмездная передача вещи или права "
            "либо освобождение от обязанности, притворность при встречном предоставлении, "
            "требуемая письменная форма, запрещение дарения и ограничения, требующие согласия, "
            "проверяются раздельно (статьи 572–576 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "gift_concept_and_form_articles_572_576",
            "legal_reference": "ГК РФ, статьи 572–576",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk573-582-gift-refusal-revocation-and-donation-v1",
        title="Синтетическая проверенная модель отказа одаряемого, отмены дарения и пожертвования по статьям 573 и 577–582 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: отказ одаряемого от дара до передачи, основания "
            "отказа дарителя от исполнения и отмены дарения, неприменение отмены к обычным "
            "подаркам небольшой стоимости и отмена пожертвования при нарушении назначения "
            "проверяются раздельно (статьи 573, 577–582 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "gift_refusal_revocation_and_donation_articles_573_582",
            "legal_reference": "ГК РФ, статьи 573 и 577–582",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-gift-evidence",
        title="Синтетическая проверенная запись фактов о дарении",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является возмездной поставкой товаров за "
            "оплату и не является безвозмездным дарением; встречного предоставления по нему "
            "нет только в смысле дарения, оснований отмены и пожертвования не заявлено."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "gift_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk583-593-annuity-general-and-permanent-v1",
        title="Синтетическая проверенная модель общих положений о ренте, формы, обеспечения и постоянной ренты по статьям 583–593 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: рента как передача имущества под периодические "
            "платежи, нотариальная форма и регистрация, обеспечение выплаты и проценты за "
            "просрочку, а также ничтожность отказа от выкупа и выкуп постоянной ренты по "
            "требованию получателя проверяются раздельно (статьи 583–593 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "annuity_general_and_permanent_articles_583_593",
            "legal_reference": "ГК РФ, статьи 583–593",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk596-605-annuity-life-and-maintenance-v1",
        title="Синтетическая проверенная модель пожизненной ренты и пожизненного содержания с иждивением по статьям 596–605 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: пожизненная рента и пожизненное содержание с "
            "иждивением, расторжение при существенном нарушении плательщиком и недопустимость "
            "обременения имущества без согласия получателя проверяются раздельно "
            "(статьи 596–605 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "annuity_life_and_maintenance_articles_596_605",
            "legal_reference": "ГК РФ, статьи 596–605",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-annuity-evidence",
        title="Синтетическая проверенная запись фактов о ренте",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является рентой или пожизненным содержанием с иждивением; передачи "
            "имущества под периодические рентные платежи нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "annuity_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk606-614-lease-concept-object-and-rent-v1",
        title="Синтетическая проверенная модель понятия, объектов, формы и предоставления имущества по договору аренды по статьям 606–614 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: аренда как предоставление имущества за плату во "
            "временное владение и пользование, определённость объекта, форма и регистрация, "
            "предоставление имущества со всеми принадлежностями, ответственность за недостатки "
            "и предупреждение о правах третьих лиц проверяются раздельно (статьи 606–614 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "lease_concept_object_and_rent_articles_606_614",
            "legal_reference": "ГК РФ, статьи 606–614",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk615-625-lease-use-repair-and-renewal-v1",
        title="Синтетическая проверенная модель пользования, содержания, расторжения, преимущественного права и улучшений по статьям 615–625 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: пользование имуществом по назначению и субаренда с "
            "согласия арендодателя, капитальный и текущий ремонт, досрочное расторжение, "
            "преимущественное право на новый срок и возмещение неотделимых улучшений "
            "проверяются раздельно (статьи 615–625 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "lease_use_repair_and_renewal_articles_615_625",
            "legal_reference": "ГК РФ, статьи 615–625",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-lease-evidence",
        title="Синтетическая проверенная запись фактов об аренде",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является арендой; предоставления имущества за плату во временное "
            "владение и пользование нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "lease_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk626-628-rental-concept-form-and-term-v1",
        title="Синтетическая проверенная модель понятия, формы, срока проката и обязанностей арендодателя по статьям 626–628 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: прокат как предоставление профессиональным "
            "арендодателем движимого имущества за плату во временное владение и пользование, "
            "письменная форма, предельный срок до одного года, неприменение правил о "
            "преимущественном праве и обязанность проверить исправность имущества проверяются "
            "раздельно (статьи 626–628 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "rental_concept_form_and_term_articles_626_628",
            "legal_reference": "ГК РФ, статьи 626–628",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk629-631-rental-defects-payment-and-repair-v1",
        title="Синтетическая проверенная модель недостатков, арендной платы, ремонта и распоряжения по статьям 629–631 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: устранение недостатков арендодателем в десятидневный "
            "срок, отнесение расходов на арендатора при нарушении им правил эксплуатации, "
            "возврат части платы при досрочном возврате, обязанность арендодателя по капитальному "
            "и текущему ремонту и запрет субаренды и передачи прав проверяются раздельно "
            "(статьи 629–631 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "rental_defects_payment_and_repair_articles_629_631",
            "legal_reference": "ГК РФ, статьи 629–631",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-rental-evidence",
        title="Синтетическая проверенная запись фактов о прокате",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является прокатом; предоставления движимого имущества профессиональным "
            "арендодателем во временное владение и пользование нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "rental_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk632-641-vehicle-lease-with-crew-v1",
        title="Синтетическая проверенная модель аренды транспортного средства с экипажем по статьям 632–641 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: аренда транспортного средства с предоставлением услуг "
            "по управлению и технической эксплуатации, письменная форма независимо от срока, "
            "неприменение правил о преимущественном праве, обязанности арендодателя по "
            "содержанию, экипажу и страхованию, распределение расходов и ответственность за вред "
            "третьим лицам проверяются раздельно (статьи 632–641 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "vehicle_lease_with_crew_articles_632_641",
            "legal_reference": "ГК РФ, статьи 632–641",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk642-649-vehicle-lease-without-crew-v1",
        title="Синтетическая проверенная модель аренды транспортного средства без экипажа по статьям 642–649 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: аренда транспортного средства без предоставления услуг "
            "по управлению и технической эксплуатации, письменная форма независимо от срока, "
            "обязанности арендатора по содержанию, страхованию и расходам, право сдавать "
            "транспортное средство в субаренду и ответственность арендатора за вред третьим "
            "лицам проверяются раздельно (статьи 642–649 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "vehicle_lease_without_crew_articles_642_649",
            "legal_reference": "ГК РФ, статьи 642–649",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-vehicle-lease-evidence",
        title="Синтетическая проверенная запись фактов об аренде транспортного средства",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является арендой транспортного средства; предоставления транспортного "
            "средства во временное владение и пользование нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "vehicle_lease_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk650-651-building-lease-concept-form-and-registration-v1",
        title="Синтетическая проверенная модель понятия, формы и государственной регистрации аренды зданий и сооружений по статьям 650 и 651 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: аренда здания или сооружения как передача во временное "
            "владение и пользование, письменная форма путём составления одного документа и "
            "недействительность при её несоблюдении, государственная регистрация договора со "
            "сроком не менее года проверяются раздельно (статьи 650 и 651 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "building_lease_concept_form_and_registration_articles_650_651",
            "legal_reference": "ГК РФ, статьи 650 и 651",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk652-655-building-lease-land-rent-and-transfer-v1",
        title="Синтетическая проверенная модель прав на земельный участок, арендной платы и передачи здания по статьям 652–655 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: передача прав на часть земельного участка, занятую "
            "недвижимостью, сохранение права пользования участком при смене его собственника, "
            "существенное условие о размере арендной платы и оформление передачи и возврата "
            "здания передаточным актом проверяются раздельно (статьи 652–655 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "building_lease_land_rent_and_transfer_articles_652_655",
            "legal_reference": "ГК РФ, статьи 652–655",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-building-lease-evidence",
        title="Синтетическая проверенная запись фактов об аренде здания или сооружения",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является арендой здания или сооружения; передачи здания во временное "
            "владение и пользование нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "building_lease_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk656-659-enterprise-lease-concept-form-and-creditors-v1",
        title="Синтетическая проверенная модель понятия, формы, регистрации и прав кредиторов при аренде предприятия по статьям 656–659 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: аренда предприятия как имущественного комплекса, "
            "письменная форма путём составления одного документа и недействительность при её "
            "несоблюдении, государственная регистрация договора, письменное уведомление "
            "кредиторов, согласие кредитора на перевод долгов и передача предприятия по "
            "передаточному акту проверяются раздельно (статьи 656–659 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "enterprise_lease_concept_form_and_creditors_articles_656_659",
            "legal_reference": "ГК РФ, статьи 656–659",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk660-664-enterprise-lease-use-maintenance-and-return-v1",
        title="Синтетическая проверенная модель пользования, содержания и возврата арендованного предприятия по статьям 660–664 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: право арендатора распоряжаться материальными "
            "ценностями в составе предприятия без согласия арендодателя, обязанность арендатора "
            "поддерживать предприятие в надлежащем техническом состоянии, включая текущий и "
            "капитальный ремонт, и возврат предприятия по передаточному акту за счёт арендатора "
            "проверяются раздельно (статьи 660–664 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "enterprise_lease_use_maintenance_and_return_articles_660_664",
            "legal_reference": "ГК РФ, статьи 660–664",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-enterprise-lease-evidence",
        title="Синтетическая проверенная запись фактов об аренде предприятия",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является арендой предприятия; передачи предприятия как имущественного "
            "комплекса во временное владение и пользование нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "enterprise_lease_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk665-667-leasing-concept-object-and-notice-v1",
        title="Синтетическая проверенная модель понятия, предмета финансовой аренды и уведомления продавца по статьям 665–667 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: финансовая аренда как приобретение арендодателем "
            "указанного арендатором имущества у определённого продавца и передача его "
            "арендатору, допустимость только непотребляемых вещей кроме земельных участков и "
            "иных природных объектов и обязанность уведомить продавца о лизинговом назначении "
            "проверяются раздельно (статьи 665–667 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "leasing_concept_object_and_notice_articles_665_667",
            "legal_reference": "ГК РФ, статьи 665–667",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk668-670-leasing-delivery-risk-and-seller-claims-v1",
        title="Синтетическая проверенная модель передачи предмета лизинга, перехода риска и требований к продавцу по статьям 668–670 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: передача предмета лизинга в установленный срок и "
            "последствия просрочки по обстоятельствам, за которые отвечает арендодатель, "
            "переход риска случайной гибели в момент передачи, прямые требования арендатора к "
            "продавцу и солидарная ответственность арендодателя при выборе им продавца "
            "проверяются раздельно (статьи 668–670 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "leasing_delivery_risk_and_seller_claims_articles_668_670",
            "legal_reference": "ГК РФ, статьи 668–670",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-leasing-evidence",
        title="Синтетическая проверенная запись фактов о финансовой аренде",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является финансовой арендой; приобретения имущества у определённого "
            "продавца для передачи арендатору нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "leasing_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk671-678-residential-lease-concept-form-and-duties-v1",
        title="Синтетическая проверенная модель понятия, объекта, формы найма жилого помещения и обязанностей сторон по статьям 671–678 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: наём жилого помещения как предоставление его за плату "
            "во владение и пользование для проживания, требование изолированного и пригодного "
            "для постоянного проживания помещения, письменная форма договора и обязанности "
            "наймодателя по эксплуатации и нанимателя по пользованию проверяются раздельно "
            "(статьи 671–678 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "residential_lease_concept_form_and_duties_articles_671_678",
            "legal_reference": "ГК РФ, статьи 671–678",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk682-688-residential-lease-rent-renewal-and-termination-v1",
        title="Синтетическая проверенная модель платы, преимущественного права и расторжения найма жилого помещения по статьям 682–688 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: недопустимость одностороннего изменения платы, "
            "обязанность наймодателя предложить продление не позднее чем за три месяца до "
            "истечения срока, неприменение этого правила к краткосрочному найму, судебный "
            "порядок расторжения по требованию наймодателя и предоставление нанимателю срока "
            "для устранения нарушения проверяются раздельно (статьи 682–688 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "residential_lease_rent_renewal_and_termination_articles_682_688",
            "legal_reference": "ГК РФ, статьи 682–688",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-residential-lease-evidence",
        title="Синтетическая проверенная запись фактов о найме жилого помещения",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является наймом жилого помещения; предоставления жилого помещения для "
            "проживания за плату нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "residential_lease_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk689-694-gratuitous-use-concept-limits-and-defects-v1",
        title="Синтетическая проверенная модель понятия ссуды, ограничений субъектного состава и недостатков вещи по статьям 689–694 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: безвозмездное пользование как передача вещи во "
            "временное пользование с обязанностью вернуть её с учётом нормального износа, запрет "
            "коммерческой организации передавать имущество своему учредителю и руководителю, "
            "предоставление вещи с принадлежностями, ответственность за умышленно скрытые "
            "недостатки и сохранение прав третьих лиц проверяются раздельно (статьи 689–694 "
            "ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "gratuitous_use_concept_limits_and_defects_articles_689_694",
            "legal_reference": "ГК РФ, статьи 689–694",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk695-701-gratuitous-use-maintenance-risk-and-termination-v1",
        title="Синтетическая проверенная модель содержания вещи, риска, расторжения и отказа от договора ссуды по статьям 695–701 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: обязанность ссудополучателя поддерживать вещь в "
            "исправном состоянии и нести расходы на её содержание, распределение риска случайной "
            "гибели, основания досрочного расторжения, месячный срок извещения при отказе от "
            "договора и сохранение прав ссудополучателя при отчуждении вещи проверяются "
            "раздельно (статьи 695–701 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "gratuitous_use_maintenance_risk_and_termination_articles_695_701",
            "legal_reference": "ГК РФ, статьи 695–701",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-gratuitous-use-evidence",
        title="Синтетическая проверенная запись фактов о безвозмездном пользовании",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является договором безвозмездного пользования; передачи вещи в "
            "безвозмездное временное пользование нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "gratuitous_use_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk702-716-work-contract-concept-terms-and-materials-v1",
        title="Синтетическая проверенная модель понятия подряда, сроков, сметы и материалов по статьям 702–716 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: подряд как выполнение работы по заданию заказчика и "
            "сдача её результата за плату, обязанность выполнить работу лично при её прямом "
            "закреплении, согласование начального и конечного сроков, предупреждение заказчика "
            "о существенном превышении твёрдой сметы, ответственность за непригодность "
            "предоставленного заказчиком материала и обязанность подрядчика предупредить об "
            "обстоятельствах, угрожающих годности работы, проверяются раздельно (статьи 702–716 "
            "ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "work_contract_concept_terms_and_materials_articles_702_716",
            "legal_reference": "ГК РФ, статьи 702–716",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk717-729-work-contract-quality-acceptance-and-withdrawal-v1",
        title="Синтетическая проверенная модель качества работы, приёмки, сроков обнаружения недостатков и отказа заказчика по статьям 717–729 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: право заказчика отказаться от договора до сдачи "
            "результата с оплатой выполненной части, обязанность заказчика осмотреть и принять "
            "результат работы, ответственность подрядчика за ненадлежащее качество и сроки "
            "обнаружения недостатков результата работы проверяются раздельно (статьи 717–729 "
            "ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "work_contract_quality_acceptance_and_withdrawal_articles_717_729",
            "legal_reference": "ГК РФ, статьи 717–729",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-work-contract-evidence",
        title="Синтетическая проверенная запись фактов о подряде",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является договором подряда; выполнения работы по заданию заказчика и "
            "сдачи её результата за плату нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "work_contract_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk730-736-consumer-work-concept-information-and-payment-v1",
        title="Синтетическая проверенная модель понятия бытового подряда, прав заказчика, информации о работе и порядка оплаты по статьям 730–736 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: бытовой подряд как выполнение подрядчиком-"
            "предпринимателем работы по заданию гражданина для удовлетворения его бытовых или "
            "других личных потребностей, запрет навязывать заказчику дополнительную работу, "
            "право заказчика в любое время до сдачи работы прекратить договор с оплатой "
            "выполненной части, обязанность сообщить необходимую и достоверную информацию о "
            "работе, последствия использования недоброкачественного материала подрядчика, "
            "оплата после окончательной сдачи работы и обязанность сообщить требования к "
            "использованию результата проверяются раздельно (статьи 730–736 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "consumer_work_concept_information_and_payment_articles_730_736",
            "legal_reference": "ГК РФ, статьи 730–736",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk737-739-consumer-work-defects-and-uncollected-result-v1",
        title="Синтетическая проверенная модель последствий недостатков результата работы и неявки заказчика по статьям 737–739 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: требования заказчика при обнаружении недостатков "
            "результата работы, право требовать безвозмездного устранения существенного "
            "недостатка, обнаруженного по истечении гарантийного срока в пределах десяти лет с "
            "момента принятия результата, и право подрядчика продать невостребованный результат "
            "не ранее чем через два месяца после письменного предупреждения заказчика "
            "проверяются раздельно (статьи 737–739 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "consumer_work_defects_and_uncollected_result_articles_737_739",
            "legal_reference": "ГК РФ, статьи 737–739",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-consumer-work-evidence",
        title="Синтетическая проверенная запись фактов о бытовом подряде",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является договором бытового подряда; работа по заданию гражданина для "
            "удовлетворения его личных потребностей не выполнялась."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "consumer_work_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk740-749-construction-contract-concept-documentation-and-duties-v1",
        title="Синтетическая проверенная модель понятия строительного подряда, страхования риска, технической документации и обязанностей заказчика по статьям 740–749 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: строительный подряд как обязанность подрядчика в "
            "установленный срок построить по заданию заказчика объект либо выполнить иные "
            "строительные работы и обязанность заказчика создать необходимые условия, принять "
            "результат и уплатить цену, страхование риска случайной гибели объекта, согласование "
            "технической документации и сметы, сообщение заказчику о не учтённых в документации "
            "работах, предоставление земельного участка и услуг и контроль заказчика за ходом и "
            "качеством работ проверяются раздельно (статьи 740–749 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "construction_contract_concept_documentation_and_duties_articles_740_749",
            "legal_reference": "ГК РФ, статьи 740–749",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk752-757-construction-contract-conservation-acceptance-and-quality-v1",
        title="Синтетическая проверенная модель консервации строительства, сдачи и приёмки работ, качества и предельного срока обнаружения недостатков по статьям 752–757 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: последствия приостановления строительства и "
            "консервации объекта, порядок сдачи и приёмки результата работ и односторонний акт "
            "при необоснованном отказе от его подписания, ответственность подрядчика за "
            "отступления от технической документации и обязательных строительных норм и "
            "предельный пятилетний срок обнаружения недостатков проверяются раздельно "
            "(статьи 752–757 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "construction_contract_conservation_acceptance_and_quality_articles_752_757",
            "legal_reference": "ГК РФ, статьи 752–757",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-construction-contract-evidence",
        title="Синтетическая проверенная запись фактов о строительном подряде",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является договором строительного подряда; строительство объекта и иные "
            "строительные работы по заданию заказчика не выполнялись."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "construction_contract_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk758-760-design-work-concept-initial-data-and-approval-v1",
        title="Синтетическая проверенная модель понятия подряда на проектные и изыскательские работы, исходных данных и согласования документации по статьям 758–760 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: подряд на выполнение проектных и изыскательских работ "
            "как обязанность подрядчика по заданию заказчика разработать техническую "
            "документацию или выполнить изыскательские работы и обязанность заказчика принять и "
            "оплатить их результат, передача задания и иных исходных данных, запрет отступать от "
            "требований задания без согласия заказчика, согласование готовой документации с "
            "заказчиком и компетентными органами, запрет передавать документацию третьим лицам "
            "без согласия заказчика и гарантия отсутствия у третьих лиц права воспрепятствовать "
            "работам проверяются раздельно (статьи 758–760 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "design_work_concept_initial_data_and_approval_articles_758_760",
            "legal_reference": "ГК РФ, статьи 758–760",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk761-762-design-work-liability-and-customer-duties-v1",
        title="Синтетическая проверенная модель ответственности подрядчика за недостатки документации и обязанностей заказчика по статьям 761–762 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: ответственность подрядчика за ненадлежащее составление "
            "технической документации и выполнение изыскательских работ, включая недостатки, "
            "выявленные впоследствии в ходе строительства или эксплуатации объекта, обязанность "
            "заказчика уплатить установленную цену и оказывать содействие, включая участие в "
            "согласовании документации, и возмещение дополнительных расходов, вызванных "
            "изменением исходных данных, проверяются раздельно (статьи 761–762 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "design_work_liability_and_customer_duties_articles_761_762",
            "legal_reference": "ГК РФ, статьи 761–762",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-design-work-evidence",
        title="Синтетическая проверенная запись фактов о проектных и изыскательских работах",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является договором подряда на выполнение проектных и изыскательских "
            "работ; разработка технической документации и изыскательские работы по заданию "
            "заказчика не выполнялись."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "design_work_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk763-766-state-work-contract-basis-parties-and-terms-v1",
        title="Синтетическая проверенная модель оснований выполнения подрядных работ для государственных нужд, сторон контракта и его содержания по статьям 763–766 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: выполнение подрядных строительных, проектных и "
            "изыскательских работ для государственных или муниципальных нужд на основе "
            "государственного или муниципального контракта, статус заказчика как "
            "государственного органа, казённого учреждения или иного получателя бюджетных "
            "средств, порядок заключения контракта по правилам о поставке для государственных "
            "нужд и обязательные условия контракта об объёме и стоимости работ, сроках их начала "
            "и окончания, размере и порядке финансирования и оплаты и способах обеспечения "
            "исполнения обязательств проверяются раздельно (статьи 763–766 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "state_work_contract_basis_parties_and_terms_articles_763_766",
            "legal_reference": "ГК РФ, статьи 763–766",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk767-768-state-work-budget-changes-and-special-law-v1",
        title="Синтетическая проверенная модель изменения государственного контракта при уменьшении бюджетных средств и применения специального закона по статьям 767–768 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: обязанность сторон согласовать новые сроки и при "
            "необходимости другие условия выполнения работ при уменьшении выделенных бюджетных "
            "средств, право подрядчика требовать возмещения убытков, причинённых изменением "
            "сроков, и применение закона о подрядах для государственных или муниципальных нужд в "
            "части, не урегулированной Кодексом, проверяются раздельно (статьи 767–768 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "state_work_budget_changes_and_special_law_articles_767_768",
            "legal_reference": "ГК РФ, статьи 767–768",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-state-work-evidence",
        title="Синтетическая проверенная запись фактов о подрядных работах для государственных нужд",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату между коммерческими организациями и не относится к подрядным работам для "
            "государственных или муниципальных нужд; бюджетное финансирование работ отсутствует."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "state_work_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk769-774-research-work-concept-confidentiality-and-duties-v1",
        title="Синтетическая проверенная модель понятия договоров на научно-исследовательские и опытно-конструкторские работы, конфиденциальности, прав на результаты и обязанностей сторон по статьям 769–774 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: договор на выполнение научно-исследовательских работ "
            "как обязанность исполнителя провести обусловленные техническим заданием научные "
            "исследования и договор на выполнение опытно-конструкторских и технологических работ "
            "как обязанность разработать образец нового изделия, конструкторскую документацию на "
            "него или новую технологию, обязанность провести научные исследования лично и "
            "привлекать третьих лиц только с согласия заказчика, конфиденциальность сведений и "
            "согласование публикаций, определение пределов и условий использования результатов, "
            "гарантия ненарушения исключительных прав других лиц, незамедлительное сообщение о "
            "невозможности получить результат и обязанности заказчика передать информацию, "
            "принять и оплатить результаты проверяются раздельно (статьи 769–774 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "research_work_concept_confidentiality_and_duties_articles_769_774",
            "legal_reference": "ГК РФ, статьи 769–774",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk775-778-research-work-impossibility-and-liability-v1",
        title="Синтетическая проверенная модель последствий невозможности достижения результата и ответственности исполнителя по статьям 775–778 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: последствия невозможности достижения результатов "
            "научно-исследовательских работ и невозможности продолжения опытно-конструкторских и "
            "технологических работ по не зависящим от исполнителя обстоятельствам, обязанность "
            "заказчика оплатить стоимость работ и понесённые затраты до выявления невозможности, "
            "ответственность исполнителя при недоказанности отсутствия его вины и применение к "
            "этим договорам правил о сроках, цене работ и последствиях неявки заказчика за "
            "результатом проверяются раздельно (статьи 775–778 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "research_work_impossibility_and_liability_articles_775_778",
            "legal_reference": "ГК РФ, статьи 775–778",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-research-work-evidence",
        title="Синтетическая проверенная запись фактов о научно-исследовательских и опытно-конструкторских работах",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является договором на выполнение научно-исследовательских, "
            "опытно-конструкторских и технологических работ; научные исследования и разработка "
            "образца нового изделия по техническому заданию заказчика не проводились."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "research_work_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk779-781-paid-services-concept-personal-performance-and-payment-v1",
        title="Синтетическая проверенная модель понятия возмездного оказания услуг, личного исполнения и оплаты услуг по статьям 779–781 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: возмездное оказание услуг как обязанность исполнителя "
            "по заданию заказчика совершить определённые действия или осуществить определённую "
            "деятельность и обязанность заказчика оплатить эти услуги, исключение услуг, "
            "оказываемых по договорам, предусмотренным отдельными главами Кодекса, обязанность "
            "оказать услуги лично, если иное не предусмотрено договором, оплата услуг в сроки и "
            "порядке договора, полная оплата при невозможности исполнения по вине заказчика и "
            "возмещение фактически понесённых расходов при невозможности по обстоятельствам, за "
            "которые ни одна из сторон не отвечает, проверяются раздельно "
            "(статьи 779–781 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "paid_services_concept_personal_performance_and_payment_articles_779_781",
            "legal_reference": "ГК РФ, статьи 779–781",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk782-783-1-paid-services-withdrawal-and-communication-v1",
        title="Синтетическая проверенная модель одностороннего отказа от договора возмездного оказания услуг и особенностей услуг связи по статьям 782–783.1 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: право заказчика отказаться от исполнения договора при "
            "условии оплаты исполнителю фактически понесённых расходов, право исполнителя "
            "отказаться лишь при полном возмещении заказчику убытков, применение к договору "
            "общих положений о подряде и бытовом подряде и допустимость приостановления или "
            "ограничения оказания услуг связи только в установленных законом и договором случаях "
            "проверяются раздельно (статьи 782–783.1 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "paid_services_withdrawal_and_communication_articles_782_783_1",
            "legal_reference": "ГК РФ, статьи 782–783.1",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-paid-services-evidence",
        title="Синтетическая проверенная запись фактов о возмездном оказании услуг",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является договором возмездного оказания услуг; совершения действий или "
            "осуществления деятельности по заданию заказчика за плату нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "paid_services_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk784-792-carriage-concept-documents-and-obligations-v1",
        title="Синтетическая проверенная модель понятия перевозки, транспортных документов, провозной платы и обязанностей сторон по статьям 784–792 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: перевозка грузов, пассажиров и багажа на основании "
            "договора перевозки, обязанность перевозчика доставить вверенный груз в пункт "
            "назначения и выдать его получателю либо перевезти пассажира и багаж, подтверждение "
            "договора транспортной накладной, билетом и багажной квитанцией, публичный характер "
            "перевозки транспортом общего пользования, правила о провозной плате и удержании "
            "груза, подача исправных транспортных средств и их использование отправителем и "
            "сроки доставки проверяются раздельно (статьи 784–792 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "carriage_concept_documents_and_obligations_articles_784_792",
            "legal_reference": "ГК РФ, статьи 784–792",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk793-800-carriage-liability-and-claims-v1",
        title="Синтетическая проверенная модель ответственности перевозчика, сохранности груза и порядка предъявления требований по статьям 793–800 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: ответственность сторон за нарушение обязательств по "
            "перевозке и недействительность соглашений об ограничении или устранении "
            "установленной законом ответственности перевозчика, ответственность за неподачу "
            "транспортных средств и их неиспользование, штраф за задержку отправления пассажира, "
            "ответственность за утрату, недостачу и повреждение груза или багажа при "
            "недоказанности отсутствия вины перевозчика, обязательный претензионный порядок и "
            "ответственность за вред жизни и здоровью пассажира проверяются раздельно "
            "(статьи 793–800 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "carriage_liability_and_claims_articles_793_800",
            "legal_reference": "ГК РФ, статьи 793–800",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-carriage-evidence",
        title="Синтетическая проверенная запись фактов о перевозке",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является договором перевозки; доставка вверенного отправителем груза "
            "перевозчиком в пункт назначения за плату не осуществлялась."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "carriage_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk801-804-forwarding-concept-form-and-information-v1",
        title="Синтетическая проверенная модель понятия транспортной экспедиции, формы договора, ответственности экспедитора и информации о грузе по статьям 801–804 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: транспортная экспедиция как обязанность экспедитора за "
            "вознаграждение и за счёт клиента выполнить или организовать выполнение определённых "
            "договором услуг, связанных с перевозкой груза, письменная форма договора и выдача "
            "доверенности, ответственность экспедитора по общим правилам об обязательствах и по "
            "правилам ответственности перевозчика, когда нарушение вызвано ненадлежащим "
            "исполнением договора перевозки, обязанность клиента предоставить документы и "
            "информацию о свойствах груза и обязанность экспедитора сообщить о неполноте "
            "полученных сведений проверяются раздельно (статьи 801–804 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "forwarding_concept_form_and_information_articles_801_804",
            "legal_reference": "ГК РФ, статьи 801–804",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk805-806-forwarding-third-parties-and-withdrawal-v1",
        title="Синтетическая проверенная модель привлечения третьих лиц и одностороннего отказа от договора транспортной экспедиции по статьям 805–806 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: право экспедитора привлечь к исполнению своих "
            "обязанностей других лиц, если из договора не следует обязанность исполнить их "
            "лично, сохранение ответственности экспедитора при возложении исполнения на третье "
            "лицо, право любой стороны отказаться от исполнения договора с предупреждением в "
            "разумный срок, возмещение убытков, вызванных расторжением, и уплата штрафа в "
            "размере десяти процентов суммы понесённых затрат проверяются раздельно "
            "(статьи 805–806 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "forwarding_third_parties_and_withdrawal_articles_805_806",
            "legal_reference": "ГК РФ, статьи 805–806",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-forwarding-evidence",
        title="Синтетическая проверенная запись фактов о транспортной экспедиции",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является договором транспортной экспедиции; выполнения или организации "
            "услуг, связанных с перевозкой груза, за вознаграждение и за счёт клиента нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "forwarding_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk807-811-loan-concept-form-interest-and-repayment-v1",
        title="Синтетическая проверенная модель понятия займа, формы договора, процентов и возврата суммы займа по статьям 807–811 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: заём как передача займодавцем в собственность заёмщику "
            "денег или вещей, определённых родовыми признаками, с обязанностью возвратить такую "
            "же сумму или равное количество вещей того же рода и качества, письменная форма "
            "договора при превышении установленной суммы и при участии юридического лица, "
            "правила о размере и уплате процентов и о беспроцентном займе, уменьшение судом "
            "чрезмерно обременительных ростовщических процентов, обязанность возвратить сумму "
            "займа в срок и начисление процентов за просрочку проверяются раздельно "
            "(статьи 807–811 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "loan_concept_form_interest_and_repayment_articles_807_811",
            "legal_reference": "ГК РФ, статьи 807–811",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk812-818-loan-challenge-security-purpose-and-novation-v1",
        title="Синтетическая проверенная модель оспаривания займа по безденежности, утраты обеспечения, целевого займа и новации долга по статьям 812–818 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: право заёмщика оспаривать договор займа по "
            "безденежности, право займодавца потребовать досрочного возврата при утрате "
            "обеспечения по обстоятельствам, за которые он не отвечает, использование целевого "
            "займа по назначению и обеспечение контроля займодавца и замена долга, возникшего из "
            "иного основания, заёмным обязательством с соблюдением требований о новации "
            "проверяются раздельно (статьи 812–818 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "loan_challenge_security_purpose_and_novation_articles_812_818",
            "legal_reference": "ГК РФ, статьи 812–818",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-loan-evidence",
        title="Синтетическая проверенная запись фактов о займе",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является договором займа; передачи денег или вещей, определённых "
            "родовыми признаками, с обязанностью возврата нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "loan_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk819-820-credit-concept-parties-and-form-v1",
        title="Синтетическая проверенная модель понятия кредитного договора, его сторон, процентов и письменной формы по статьям 819–820 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: кредитный договор как обязанность банка или иной "
            "кредитной организации предоставить денежные средства заёмщику в размере и на "
            "условиях договора и обязанность заёмщика возвратить полученную сумму, уплатить "
            "проценты и предусмотренные договором иные платежи, применение правил о "
            "потребительском кредите к заёмщику-гражданину и обязательная письменная форма "
            "договора под страхом ничтожности проверяются раздельно (статьи 819–820 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "credit_concept_parties_and_form_articles_819_820",
            "legal_reference": "ГК РФ, статьи 819–820",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk821-821-1-credit-refusal-and-early-repayment-v1",
        title="Синтетическая проверенная модель отказа от предоставления и получения кредита и требования досрочного возврата по статьям 821–821.1 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: право кредитора отказаться от предоставления кредита "
            "при обстоятельствах, очевидно свидетельствующих о невозврате суммы в срок, право "
            "заёмщика отказаться от получения кредита с уведомлением до установленного срока, "
            "право кредитора отказаться от дальнейшего кредитования при нецелевом использовании "
            "и допустимость требования досрочного возврата только в предусмотренных законом или "
            "договором случаях, а от заёмщика-гражданина — только в установленных законом "
            "случаях, проверяются раздельно (статьи 821–821.1 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "credit_refusal_and_early_repayment_articles_821_821_1",
            "legal_reference": "ГК РФ, статьи 821–821.1",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-credit-evidence",
        title="Синтетическая проверенная запись фактов о кредите",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является кредитным договором; предоставления денежных средств кредитной "
            "организацией с обязанностью возврата и уплаты процентов нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "credit_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk822-goods-credit-concept-and-sale-rules-v1",
        title="Синтетическая проверенная модель товарного кредита и применения к нему правил о купле-продаже по статье 822 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: договор товарного кредита как обязанность стороны "
            "предоставить другой стороне вещи, определённые родовыми признаками, применение к "
            "нему правил о займе, если иное не предусмотрено договором и не вытекает из существа "
            "обязательства, и исполнение условий о количестве, ассортименте, комплектности, "
            "качестве, таре и упаковке предоставляемых вещей по правилам о купле-продаже товаров "
            "проверяются раздельно (статья 822 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "goods_credit_concept_and_sale_rules_article_822",
            "legal_reference": "ГК РФ, статья 822",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk823-commercial-credit-forms-and-applicable-rules-v1",
        title="Синтетическая проверенная модель коммерческого кредита, его форм и применимых правил по статье 823 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: предоставление коммерческого кредита договорами, "
            "исполнение которых связано с передачей в собственность денежных сумм или вещей, "
            "определяемых родовыми признаками, в том числе в виде аванса, предварительной "
            "оплаты, отсрочки и рассрочки оплаты товаров, работ или услуг, допустимость такого "
            "условия, если иное не установлено законом, и применение правил главы о займе и "
            "кредите постольку, поскольку это не противоречит правилам о договоре, из которого "
            "возникло обязательство, и существу такого обязательства, проверяются раздельно "
            "(статья 823 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "commercial_credit_forms_and_applicable_rules_article_823",
            "legal_reference": "ГК РФ, статья 823",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-commercial-credit-evidence",
        title="Синтетическая проверенная запись фактов о товарном и коммерческом кредите",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату; обязанности предоставить вещи в кредит и условия о коммерческом кредите в "
            "виде аванса, предварительной оплаты, отсрочки или рассрочки в нём нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "commercial_credit_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk824-829-factoring-concept-parties-and-assignment-v1",
        title="Синтетическая проверенная модель понятия факторинга, его сторон, предмета уступки и последующей уступки по статьям 824–829 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: финансирование под уступку денежного требования как "
            "уступка клиентом финансовому агенту денежного требования к должнику против передачи "
            "денежных средств или совершения иных предусмотренных договором действий, требования "
            "к финансовому агенту, определение уступаемого требования способом, позволяющим его "
            "идентифицировать, ответственность клиента за действительность требования, "
            "действительность уступки вопреки договорному запрету и допустимость последующей "
            "уступки только при прямом указании договора проверяются раздельно "
            "(статьи 824–829 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "factoring_concept_parties_and_assignment_articles_824_829",
            "legal_reference": "ГК РФ, статьи 824–829",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk830-833-factoring-debtor-performance-and-settlements-v1",
        title="Синтетическая проверенная модель исполнения должником, зачёта, расчётов сторон и возврата полученного по статьям 830–833 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: обязанность должника произвести платёж финансовому "
            "агенту при письменном уведомлении об уступке с определением требования и указанием "
            "агента, право должника предъявить к зачёту требования к клиенту, имевшиеся ко "
            "времени получения уведомления, правила расчётов сторон при покупке требования и при "
            "его уступке в целях обеспечения и направление требования должника о возврате "
            "полученных сумм проверяются раздельно (статьи 830–833 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "factoring_debtor_performance_and_settlements_articles_830_833",
            "legal_reference": "ГК РФ, статьи 830–833",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-factoring-evidence",
        title="Синтетическая проверенная запись фактов о финансировании под уступку денежного требования",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату и не является договором факторинга; уступки денежного требования финансовому "
            "агенту против предоставления финансирования нет."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "factoring_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk834-839-bank-deposit-concept-form-and-interest-v1",
        title="Синтетическая проверенная модель понятия банковского вклада, права привлекать вклады, формы договора, возврата вклада и процентов по статьям 834–839 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: договор банковского вклада как обязанность банка, "
            "принявшего поступившую от вкладчика или для него денежную сумму, возвратить сумму "
            "вклада и выплатить проценты, право на привлечение денежных средств во вклады, "
            "обязательная письменная форма договора под страхом ничтожности, выдача вклада по "
            "первому требованию вкладчика с выплатой процентов по ставке вкладов до "
            "востребования при досрочном возврате, размер процентов и порядок их начисления "
            "проверяются раздельно (статьи 834–839 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "bank_deposit_concept_form_and_interest_articles_834_839",
            "legal_reference": "ГК РФ, статьи 834–839",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk840-844-bank-deposit-security-third-parties-and-documents-v1",
        title="Синтетическая проверенная модель обеспечения возврата вклада, вкладов третьих лиц и в пользу третьих лиц, сберегательной книжки и сертификата по статьям 840–844 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: обеспечение возврата вкладов граждан обязательным "
            "страхованием и определение способов обеспечения возврата вкладов юридических лиц "
            "договором, зачисление на счёт вкладчика денежных средств, поступивших от третьих "
            "лиц, приобретение прав вкладчика третьим лицом, в пользу которого внесён вклад, а "
            "также удостоверение вклада сберегательной книжкой и сберегательным сертификатом "
            "проверяются раздельно (статьи 840–844 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "bank_deposit_security_third_parties_and_documents_articles_840_844",
            "legal_reference": "ГК РФ, статьи 840–844",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-bank-deposit-evidence",
        title="Синтетическая проверенная запись фактов о банковском вкладе",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату; денежная сумма во вклад с обязанностью возвратить её и выплатить проценты "
            "банком не принималась."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "bank_deposit_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk845-853-bank-account-concept-operations-and-payment-v1",
        title="Синтетическая проверенная модель понятия банковского счёта, заключения договора, распоряжения счётом, сроков операций, кредитования счёта и оплаты услуг банка по статьям 845–853 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: договор банковского счёта как обязанность банка "
            "принимать и зачислять поступающие на счёт клиента денежные средства, выполнять "
            "распоряжения о перечислении и выдаче сумм и проводить другие операции по счёту, "
            "заключение договора на объявленных банком условиях, удостоверение прав распоряжения "
            "счётом, совершение операций для клиента, сроки операций по счёту, кредитование "
            "счёта при отсутствии средств, оплата услуг банка, проценты за пользование "
            "средствами и зачёт встречных требований банка и клиента проверяются раздельно "
            "(статьи 845–853 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "bank_account_concept_operations_and_payment_articles_845_853",
            "legal_reference": "ГК РФ, статьи 845–853",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk854-860-bank-account-debiting-secrecy-and-termination-v1",
        title="Синтетическая проверенная модель списания средств со счёта, ответственности банка, банковской тайны, ограничения распоряжения и расторжения договора по статьям 854–860 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: списание денежных средств со счёта по распоряжению "
            "клиента и без такого распоряжения в предусмотренных законом случаях, очерёдность "
            "списания при недостаточности средств, ответственность банка за ненадлежащее "
            "совершение операций по счёту, гарантия тайны банковского счёта и сведений о "
            "клиенте, пределы ограничения распоряжения счётом, расторжение договора и возврат "
            "остатка денежных средств проверяются раздельно (статьи 854–860 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "bank_account_debiting_secrecy_and_termination_articles_854_860",
            "legal_reference": "ГК РФ, статьи 854–860",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-bank-account-evidence",
        title="Синтетическая проверенная запись фактов о банковском счёте",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров за единовременную "
            "оплату; банковский счёт для приёма и зачисления денежных средств клиента по этому "
            "договору банком не открывался."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "bank_account_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk861-876-settlements-forms-orders-credit-and-collection-v1",
        title="Синтетическая проверенная модель наличных и безналичных расчётов, их форм, расчётов платёжными поручениями, по аккредитиву и по инкассо по статьям 861–876 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: осуществление расчётов наличными деньгами и в "
            "безналичном порядке, формы безналичных расчётов, предусмотренные законом, "
            "банковскими правилами и применяемыми в банковской практике обычаями, обязанность "
            "банка перевести денежные средства по платёжному поручению в установленный срок и "
            "ответственность за её нарушение, обязательства банка-эмитента и исполняющего банка "
            "по аккредитиву, порядок его исполнения и закрытия, а также исполнение инкассового "
            "поручения и извещение о его неисполнении проверяются раздельно "
            "(статьи 861–876 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "settlements_forms_orders_credit_and_collection_articles_861_876",
            "legal_reference": "ГК РФ, статьи 861–876",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk877-885-settlements-cheque-rules-v1",
        title="Синтетическая проверенная модель расчётов чеками, реквизитов чека, его оплаты, передачи прав, аваля и последствий неоплаты по статьям 877–885 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: чек как ценная бумага, содержащая ничем не "
            "обусловленное распоряжение чекодателя банку произвести платёж указанной в нём "
            "суммы, обязательные реквизиты чека и последствия их отсутствия, оплата чека за счёт "
            "средств чекодателя при предъявлении в установленный срок, передача прав по чеку, "
            "гарантия платежа авалем, удостоверение отказа от оплаты, извещение о неоплате и её "
            "последствия проверяются раздельно (статьи 877–885 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "settlements_cheque_rules_articles_877_885",
            "legal_reference": "ГК РФ, статьи 877–885",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-settlements-evidence",
        title="Синтетическая проверенная запись фактов о расчётах",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: оплата по спорному договору поставки произведена "
            "единовременно; безналичные расчёты платёжными поручениями, по аккредитиву, по "
            "инкассо или чеками по этому обязательству не осуществлялись."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "settlements_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk886-895-storage-concept-form-period-and-safekeeping-v1",
        title="Синтетическая проверенная модель понятия хранения, формы договора, принятия вещи, срока хранения, обеспечения сохранности и пользования вещью по статьям 886–895 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: договор хранения как обязанность хранителя хранить "
            "переданную поклажедателем вещь и возвратить её в сохранности, письменная форма "
            "договора и способы её соблюдения, обязанность принять вещь на хранение по "
            "консенсуальному договору, срок хранения и хранение до востребования, принятие мер по "
            "обеспечению сохранности вещи, запрет пользоваться вещью без согласия поклажедателя, "
            "уведомление об изменении условий хранения и передача вещи третьему лицу проверяются "
            "раздельно (статьи 886–895 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "storage_concept_form_period_and_safekeeping_articles_886_895",
            "legal_reference": "ГК РФ, статьи 886–895",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk896-906-storage-remuneration-return-and-liability-v1",
        title="Синтетическая проверенная модель вознаграждения и расходов на хранение, возврата вещи и ответственности хранителя по статьям 896–906 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: выплата вознаграждения за хранение и его размер, "
            "возмещение расходов на хранение и чрезвычайных расходов, обязанность поклажедателя "
            "взять вещь обратно по истечении срока хранения, обязанность хранителя возвратить ту "
            "самую вещь в том состоянии, в каком она была принята, с учётом естественного "
            "ухудшения и естественной убыли, а также основания и размер ответственности "
            "хранителя, в том числе профессионального, проверяются раздельно "
            "(статьи 896–906 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "storage_remuneration_return_and_liability_articles_896_906",
            "legal_reference": "ГК РФ, статьи 896–906",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-storage-evidence",
        title="Синтетическая проверенная запись фактов о хранении",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: спорный договор является поставкой товаров; вещь на хранение с "
            "обязанностью хранителя возвратить её в сохранности по этому договору не "
            "передавалась."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "storage_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk907-911-warehouse-storage-concept-and-inspection-v1",
        title="Синтетическая проверенная модель договора складского хранения, склада общего пользования, проверки товаров при приёме, осмотра товаров и изменения условий хранения по статьям 907–911 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: договор складского хранения как обязанность товарного "
            "склада за вознаграждение хранить переданные товаровладельцем товары и возвратить их "
            "в сохранности, публичный характер договора склада общего пользования, осмотр товаров "
            "и определение их количества и внешнего состояния при приёме, право товаровладельца "
            "осматривать товары и брать пробы, изменение условий хранения с уведомлением "
            "товаровладельца и проверка товаров при их возвращении проверяются раздельно "
            "(статьи 907–911 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "warehouse_storage_concept_and_inspection_articles_907_911",
            "legal_reference": "ГК РФ, статьи 907–911",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk912-918-warehouse-documents-and-goods-release-v1",
        title="Синтетическая проверенная модель складских документов, двойного складского свидетельства, выдачи товара и хранения вещей с обезличением по статьям 912–918 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: выдача складом двойного складского свидетельства, "
            "простого складского свидетельства или складской квитанции, обязательные реквизиты "
            "двойного складского свидетельства, права держателей складского и залогового "
            "свидетельств и их передача, выдача товара по двойному складскому свидетельству и "
            "хранение вещей с обезличением проверяются раздельно (статьи 912–918 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "warehouse_documents_and_goods_release_articles_912_918",
            "legal_reference": "ГК РФ, статьи 912–918",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-warehouse-storage-evidence",
        title="Синтетическая проверенная запись фактов о хранении на товарном складе",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: товары по спорному договору поставки передавались "
            "непосредственно покупателю; на хранение товарному складу за вознаграждение они не "
            "передавались."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "warehouse_storage_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk919-923-special-storage-pawnshop-bank-and-lockers-v1",
        title="Синтетическая проверенная модель хранения в ломбарде, хранения ценностей в банке и в индивидуальном сейфе, хранения в камерах хранения транспортных организаций по статьям 919–923 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: удостоверение договора хранения вещи в ломбарде именной "
            "сохранной квитанцией, оценка вещи и её страхование за счёт ломбарда, судьба "
            "невостребованной вещи, приём банком на хранение ценных бумаг, драгоценных металлов и "
            "иных ценностей с выдачей именного сохранного документа, хранение ценностей в "
            "индивидуальном банковском сейфе и ответственность банка, а также публичный характер "
            "хранения в камерах хранения транспортных организаций и судьба невостребованных вещей "
            "проверяются раздельно (статьи 919–923 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "special_storage_pawnshop_bank_and_lockers_articles_919_923",
            "legal_reference": "ГК РФ, статьи 919–923",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk924-926-special-storage-cloakroom-hotel-and-sequestration-v1",
        title="Синтетическая проверенная модель хранения в гардеробах организаций, хранения в гостинице и секвестра по статьям 924–926 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: безвозмездность хранения в гардеробах организаций и "
            "обязанность принять все необходимые меры для сохранности вещи, ответственность "
            "гостиницы как хранителя за утрату, недостачу или повреждение внесённых постояльцем "
            "вещей и особый режим денег и драгоценностей, а также передача спорной вещи на "
            "хранение третьему лицу по договору о секвестре и её возврат управомоченному лицу "
            "проверяются раздельно (статьи 924–926 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "special_storage_cloakroom_hotel_and_sequestration_articles_924_926",
            "legal_reference": "ГК РФ, статьи 924–926",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-special-storage-evidence",
        title="Синтетическая проверенная запись фактов о специальных видах хранения",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: по спорному договору поставки вещи не передавались на хранение "
            "ломбарду, банку, в камеру хранения, гардероб организации или гостиницу и не "
            "передавались на хранение в порядке секвестра."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "special_storage_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk927-938-insurance-forms-interests-and-parties-v1",
        title="Синтетическая проверенная модель добровольного и обязательного страхования, страховых интересов, имущественного и личного страхования и требований к страховщику по статьям 927–938 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: осуществление страхования на основании договоров "
            "имущественного или личного страхования, недопустимость страхования противоправных "
            "интересов, требование интереса в сохранении застрахованного имущества, страхование "
            "риска утраты имущества, риска ответственности и предпринимательского риска, "
            "страхование жизни и здоровья, обязанность страховать, возложенная законом, и её "
            "последствия, а также требования к страховщику проверяются раздельно "
            "(статьи 927–938 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "insurance_forms_interests_and_parties_articles_927_938",
            "legal_reference": "ГК РФ, статьи 927–938",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk939-943-insurance-contract-form-and-terms-v1",
        title="Синтетическая проверенная модель прав выгодоприобретателя, формы договора страхования, его существенных условий и правил страхования по статьям 939–943 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: права и обязанности выгодоприобретателя по договору "
            "страхования, обязательная письменная форма договора под страхом недействительности, "
            "соглашение сторон об объекте страхования или застрахованном лице, о характере "
            "страхового случая, о размере страховой суммы и о сроке действия договора, а также "
            "определение условий договора в правилах страхования и условия их обязательности для "
            "страхователя проверяются раздельно (статьи 939–943 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "insurance_contract_form_and_terms_articles_939_943",
            "legal_reference": "ГК РФ, статьи 939–943",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-insurance-evidence",
        title="Синтетическая проверенная запись фактов о страховании",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: по спорному договору поставки договор страхования "
            "имущественных или личных интересов сторонами не заключался."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "insurance_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk944-959-insurance-settlement-disclosure-sum-and-premium-v1",
        title="Синтетическая проверенная модель сведений при заключении договора страхования, страховой суммы и стоимости, страховой премии, увеличения страхового риска и досрочного прекращения по статьям 944–959 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: обязанность страхователя сообщить страховщику известные "
            "ему обстоятельства, имеющие существенное значение для оценки страхового риска, "
            "определение страховой суммы и страховой стоимости, последствия страхования сверх "
            "страховой стоимости и неполного имущественного страхования, порядок и сроки уплаты "
            "страховой премии, вступление договора в силу, сообщение об увеличении страхового "
            "риска и досрочное прекращение договора проверяются раздельно "
            "(статьи 944–959 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "insurance_settlement_disclosure_sum_and_premium_articles_944_959",
            "legal_reference": "ГК РФ, статьи 944–959",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk960-970-insurance-settlement-notice-release-and-subrogation-v1",
        title="Синтетическая проверенная модель уведомления о страховом случае, уменьшения убытков, освобождения страховщика, суброгации и исковой давности по статьям 960–970 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: обязанность страхователя уведомить страховщика о "
            "наступлении страхового случая и последствия её неисполнения, обязанность принять "
            "разумные и доступные меры для уменьшения убытков и возмещение соответствующих "
            "расходов, основания освобождения страховщика от выплаты, переход к страховщику прав "
            "страхователя на возмещение ущерба и срок исковой давности по требованиям из договора "
            "страхования проверяются раздельно (статьи 960–970 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "insurance_settlement_notice_release_and_subrogation_articles_960_970",
            "legal_reference": "ГК РФ, статьи 960–970",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-insurance-settlement-evidence",
        title="Синтетическая проверенная запись фактов об исполнении страхового обязательства",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: по спорному договору поставки страховой случай не наступал и "
            "исполнение страхового обязательства сторонами не производилось."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "insurance_settlement_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk971-976-mandate-concept-instructions-and-duties-v1",
        title="Синтетическая проверенная модель договора поручения, вознаграждения поверенного, исполнения поручения по указаниям доверителя, обязанностей сторон и передоверия по статьям 971–976 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: договор поручения как обязанность поверенного совершить "
            "от имени и за счёт доверителя определённые юридические действия, возмездность "
            "поручения, исполнение поручения в соответствии с правомерными, осуществимыми и "
            "конкретными указаниями доверителя, право отступить от указаний в интересах "
            "доверителя с последующим уведомлением, личное исполнение поручения и передоверие, "
            "обязанности поверенного сообщать сведения, передавать полученное и представить "
            "отчёт, а также обязанности доверителя выдать доверенность, возмещать издержки и "
            "принять исполненное проверяются раздельно (статьи 971–976 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "mandate_concept_instructions_and_duties_articles_971_976",
            "legal_reference": "ГК РФ, статьи 971–976",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk977-979-mandate-termination-and-consequences-v1",
        title="Синтетическая проверенная модель прекращения договора поручения, его последствий и обязанностей правопреемников поверенного по статьям 977–979 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: прекращение договора поручения вследствие отмены "
            "поручения доверителем, отказа поверенного, смерти или признания недееспособным одной "
            "из сторон, ничтожность соглашения об отказе от этих прав, возмещение издержек и "
            "уплата вознаграждения соразмерно выполненной работе при прекращении договора до его "
            "полного исполнения, а также обязанности наследников поверенного и ликвидатора "
            "известить доверителя и принять меры для охраны его имущества проверяются раздельно "
            "(статьи 977–979 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "mandate_termination_and_consequences_articles_977_979",
            "legal_reference": "ГК РФ, статьи 977–979",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-mandate-evidence",
        title="Синтетическая проверенная запись фактов о поручении",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: по спорному договору поставки поручение совершить от имени и "
            "за счёт другой стороны юридические действия не давалось; договор поручения между "
            "сторонами не заключался."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "mandate_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk980-983-gestio-conditions-notice-and-approval-v1",
        title="Синтетическая проверенная модель условий действий в чужом интересе, уведомления заинтересованного лица, одобрения и неодобрения действий по статьям 980–983 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: совершение действий без поручения, иного указания или "
            "заранее обещанного согласия заинтересованного лица в целях предотвращения вреда его "
            "личности или имуществу исходя из очевидной выгоды или пользы и действительных или "
            "вероятных намерений этого лица с необходимой заботливостью и осмотрительностью, "
            "обязанность сообщить заинтересованному лицу и выждать его решение, применение правил "
            "о договоре поручения при одобрении действий и отсутствие обязанностей "
            "заинтересованного лица при их неодобрении проверяются раздельно "
            "(статьи 980–983 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "gestio_conditions_notice_and_approval_articles_980_983",
            "legal_reference": "ГК РФ, статьи 980–983",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk984-989-gestio-expenses-remuneration-and-reporting-v1",
        title="Синтетическая проверенная модель возмещения расходов, вознаграждения, последствий сделки в чужом интересе и отчёта по статьям 984–989 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: возмещение необходимых расходов и иного реального "
            "ущерба лицу, действовавшему в чужом интересе, право на вознаграждение при "
            "положительном для заинтересованного лица результате, переход обязанностей по сделке, "
            "заключённой в чужом интересе, при её одобрении, применение правил о неосновательном "
            "обогащении и возмещении вреда, а также обязанность представить отчёт с указанием "
            "полученных доходов и понесённых расходов проверяются раздельно "
            "(статьи 984–989 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "gestio_expenses_remuneration_and_reporting_articles_984_989",
            "legal_reference": "ГК РФ, статьи 984–989",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-negotiorum-gestio-evidence",
        title="Синтетическая проверенная запись фактов о действиях в чужом интересе без поручения",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: стороны спорного договора поставки действовали по договору; "
            "действий без поручения в интересе другой стороны в целях предотвращения вреда её "
            "личности или имуществу не совершалось."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "negotiorum_gestio_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk990-998-commission-concept-execution-and-property-v1",
        title="Синтетическая проверенная модель договора комиссии, комиссионного вознаграждения, исполнения поручения, субкомиссии и прав на вещи по статьям 990–998 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: договор комиссии как обязанность комиссионера по "
            "поручению комитента за вознаграждение совершить сделки от своего имени, но за счёт "
            "комитента, уплата комиссионного вознаграждения и вознаграждения за делькредере, "
            "исполнение поручения на наиболее выгодных для комитента условиях и допустимость "
            "отступления от указаний с уведомлением, ответственность за неисполнение сделки "
            "третьим лицом, субкомиссия, право собственности комитента на вещи и удовлетворение "
            "требований комиссионера проверяются раздельно (статьи 990–998 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "commission_concept_execution_and_property_articles_990_998",
            "legal_reference": "ГК РФ, статьи 990–998",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk999-1004-commission-report-duties-and-termination-v1",
        title="Синтетическая проверенная модель отчёта комиссионера, обязанностей комитента и прекращения договора комиссии по статьям 999–1004 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: обязанность комиссионера представить отчёт и передать "
            "комитенту всё полученное по договору комиссии, обязанности комитента принять "
            "исполненное, осмотреть имущество и известить о недостатках, освободить комиссионера "
            "от обязательств перед третьим лицом и возместить израсходованные суммы, а также "
            "основания прекращения договора комиссии, отмена поручения комитентом и отказ "
            "комиссионера от исполнения проверяются раздельно (статьи 999–1004 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "commission_report_duties_and_termination_articles_999_1004",
            "legal_reference": "ГК РФ, статьи 999–1004",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-commission-evidence",
        title="Синтетическая проверенная запись фактов о комиссии",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: по спорному договору поставки сделки от своего имени за счёт "
            "другой стороны не совершались; договор комиссии между сторонами не заключался."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "commission_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk1005-1008-agency-concept-remuneration-and-reports-v1",
        title="Синтетическая проверенная модель агентского договора, правового положения агента, агентского вознаграждения, ограничений прав сторон и отчётов агента по статьям 1005–1008 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: агентский договор как обязанность агента за "
            "вознаграждение совершать по поручению принципала юридические и иные действия от "
            "своего имени, но за счёт принципала либо от имени и за счёт принципала, определение "
            "стороны сделки в зависимости от того, от чьего имени действует агент, уплата "
            "агентского вознаграждения, допустимые ограничения прав принципала и агента, "
            "ничтожность условий об исключительном круге покупателей и представление агентом "
            "отчётов с возражениями принципала проверяются раздельно (статьи 1005–1008 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "agency_concept_remuneration_and_reports_articles_1005_1008",
            "legal_reference": "ГК РФ, статьи 1005–1008",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk1009-1011-agency-subagency-termination-and-rules-v1",
        title="Синтетическая проверенная модель субагентского договора, прекращения агентского договора и применения правил о поручении и комиссии по статьям 1009–1011 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: право агента заключить субагентский договор с "
            "сохранением ответственности перед принципалом, прекращение агентского договора "
            "вследствие отказа стороны от исполнения бессрочного договора, смерти агента, "
            "признания его недееспособным или банкротства, а также применение правил о поручении "
            "или о комиссии в зависимости от того, действует агент от имени принципала или от "
            "своего имени, проверяются раздельно (статьи 1009–1011 ГК РФ)."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "agency_subagency_termination_and_rules_articles_1009_1011",
            "legal_reference": "ГК РФ, статьи 1009–1011",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-agency-evidence",
        title="Синтетическая проверенная запись фактов об агентировании",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: по спорному договору поставки поручение совершать юридические "
            "и иные действия за счёт другой стороны не давалось; агентский договор между "
            "сторонами не заключался."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "agency_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk166-168-invalidity-framework-v1",
        title="Синтетическая проверенная модель ничтожности и оспоримости по статьям 166–168 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: ничтожность, оспоримость, надлежащий заявитель, "
            "законный интерес, недобросовестная ссылка и нарушение закона проверяются раздельно."
        ),
        valid_from="2013-09-01",
        metadata={
            "synthetic": True,
            "topic": "invalidity_articles_166_168",
            "legal_reference": "ГК РФ, статьи 166–168",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk169-172-void-transactions-v1",
        title="Синтетическая проверенная модель ничтожных сделок по статьям 169–172 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: антисоциальная цель, мнимость, притворность, "
            "сделки недееспособных и малолетних образуют самостоятельные основания."
        ),
        valid_from="2013-09-01",
        metadata={
            "synthetic": True,
            "topic": "invalidity_articles_169_172",
            "legal_reference": "ГК РФ, статьи 169–172",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk173-179-voidable-transactions-v1",
        title="Синтетическая проверенная модель оспоримых сделок по статьям 173–179 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: согласие, полномочия, цели юридического лица, "
            "дееспособность, заблуждение, обман, угроза и кабальность проверяются отдельно."
        ),
        valid_from="2013-09-01",
        metadata={
            "synthetic": True,
            "topic": "invalidity_articles_173_179",
            "legal_reference": "ГК РФ, статьи 173–179",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk180-181-invalidity-effects-v1",
        title="Синтетическая проверенная модель частичной недействительности и сроков",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: отделимость части сделки, сохранение остатка, "
            "исполнение, реституция и сроки требований не смешиваются с основанием."
        ),
        valid_from="2013-09-01",
        metadata={
            "synthetic": True,
            "topic": "invalidity_articles_180_181",
            "legal_reference": "ГК РФ, статьи 180–181",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum25-invalidity-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ о недействительности сделок",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: обычное нарушение закона не всегда "
            "влечет ничтожность, оспоримость требует надлежащего требования, а противоречивое "
            "недобросовестное поведение может блокировать ссылку на недействительность."
        ),
        valid_from="2015-06-23",
        metadata={
            "synthetic": True,
            "topic": "invalidity_plenum_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 23.06.2015 № 25",
            "basis_url": "https://vsrf.ru/documents/own/8435/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-invalidity-evidence",
        title="Синтетическая проверенная запись фактов о действительности сделки поставки",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: договор заключен, но основания ничтожности, оспоримости "
            "и требования о применении последствий в демонстрационном деле отсутствуют."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "invalidity_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk450-453-termination-model-v1",
        title="Синтетическая проверенная модель изменения и расторжения договора по статьям 450–453 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: соглашение сторон, судебные основания, "
            "существенное изменение обстоятельств, форма, досудебный порядок и "
            "последствия прекращения проверяются раздельно."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "change_termination_articles_450_453",
            "legal_reference": "ГК РФ, статьи 450–453",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk310-4501-unilateral-model-v1",
        title="Синтетическая проверенная модель одностороннего изменения и отказа",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: наличие права, направленность действия, "
            "доставка уведомления, соблюдение требований и отказ от ранее подтвержденного "
            "основания проверяются до признания юридического эффекта."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "unilateral_articles_310_450_1",
            "legal_reference": "ГК РФ, статьи 310 и 450.1",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum54-unilateral-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ об одностороннем отказе",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: неправомерный отказ не создает "
            "заявленного эффекта, уведомление должно быть доставлено, а право должно "
            "осуществляться разумно и добросовестно."
        ),
        valid_from="2016-11-22",
        metadata={
            "synthetic": True,
            "topic": "unilateral_plenum_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 22.11.2016 № 54",
            "basis_url": "https://vsrf.ru/documents/own/8524/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum18-pretrial-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ о досудебном порядке",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: предложение об изменении или "
            "расторжении договора является обязательным досудебным этапом судебного пути."
        ),
        valid_from="2021-06-22",
        metadata={
            "synthetic": True,
            "topic": "termination_pretrial_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 22.06.2021 № 18",
            "basis_url": "https://vsrf.ru/documents/own/30139/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-termination-evidence",
        title="Синтетическая проверенная запись фактов об изменении и расторжении договора",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: договор заключен, но соглашение об изменении, судебное "
            "требование и односторонний отказ в демонстрационном деле отсутствуют."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "termination_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk329-333-security-framework-v1",
        title="Синтетическая проверенная модель общих правил обеспечения и неустойки",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: действительность основного обязательства, "
            "акцессорность обеспечения и письменная форма неустойки проверяются раздельно."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "security_articles_329_333",
            "legal_reference": "ГК РФ, статьи 329–333",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk334-360-pledge-retention-v1",
        title="Синтетическая проверенная модель залога и удержания",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: возникновение и противопоставимость залога, "
            "основания и порядок обращения взыскания, а также удержание вещи разделены."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "security_articles_334_360",
            "legal_reference": "ГК РФ, статьи 334–360",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk361-367-suretyship-v1",
        title="Синтетическая проверенная модель поручительства",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: форма, объем, характер ответственности, "
            "изменение основного обязательства, перевод долга и прекращение поручительства "
            "проверяются независимо."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "security_articles_361_367",
            "legal_reference": "ГК РФ, статьи 361–367",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk368-379-independent-guarantee-v1",
        title="Синтетическая проверенная модель независимой гарантии",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: независимость гарантии, допустимый гарант, "
            "форма, содержание, срок и соответствие требования проверяются отдельно."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "security_articles_368_379",
            "legal_reference": "ГК РФ, статьи 368–379",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk380-3812-deposit-security-payment-v1",
        title="Синтетическая проверенная модель задатка и обеспечительного платежа",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: квалификация задатка, последствия "
            "ответственности сторон, зачет и возврат обеспечительного платежа разделены."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "security_articles_380_3812",
            "legal_reference": "ГК РФ, статьи 380–381.2",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum54-security-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ об обязательствах",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: способы обеспечения применяются "
            "в составе проверяемой структуры обязательства и не подменяют основной долг."
        ),
        valid_from="2016-11-22",
        metadata={
            "synthetic": True,
            "topic": "security_general_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 22.11.2016 № 54",
            "basis_url": "https://vsrf.ru/documents/own/8524/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum23-pledge-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ о залоге вещей",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: основания взыскания, запрет при "
            "незначительном нарушении, судебный и внесудебный маршруты проверяются раздельно."
        ),
        valid_from="2023-06-27",
        metadata={
            "synthetic": True,
            "topic": "security_pledge_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 27.06.2023 № 23",
            "basis_url": "https://www.vsrf.ru/documents/own/32601/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum45-suretyship-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ о поручительстве",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: поручитель исполняет собственную "
            "обязанность, а объем, срок, возражения и переход прав требуют отдельной проверки."
        ),
        valid_from="2020-12-24",
        metadata={
            "synthetic": True,
            "topic": "security_suretyship_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 24.12.2020 № 45",
            "basis_url": "https://www.vsrf.ru/documents/own/29544/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-security-evidence",
        title="Синтетическая проверенная запись фактов об обеспечении исполнения",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: основное обязательство и нарушение подтверждены, "
            "но отдельный способ обеспечения в демонстрационном деле не установлен."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "security_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk382-390-assignment-v1",
        title="Синтетическая проверенная модель уступки требования",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: существование и определимость требования, "
            "запреты, форма, согласие, уведомление, возражения должника и ответственность "
            "цедента проверяются раздельно."
        ),
        valid_from="2014-07-01",
        metadata={
            "synthetic": True,
            "topic": "obligation_dynamics_articles_382_390",
            "legal_reference": "ГК РФ, статьи 382–390",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk391-3923-debt-transfer-v1",
        title="Синтетическая проверенная модель перевода долга и передачи договора",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: согласие кредитора, форма, освобождение "
            "первоначального должника, кумулятивное принятие долга и передача договора "
            "не смешиваются."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "obligation_dynamics_articles_391_3923",
            "legal_reference": "ГК РФ, статьи 391–392.3",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk407-413-discharge-v1",
        title="Синтетическая проверенная модель исполнения, отступного и зачета",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: надлежащее исполнение, депозит нотариуса, "
            "предоставление отступного и условия зачета являются самостоятельными "
            "основаниями прекращения."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "obligation_dynamics_articles_407_413",
            "legal_reference": "ГК РФ, статьи 407–413",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk414-419-discharge-v1",
        title="Синтетическая проверенная модель иных оснований прекращения",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: новация, прощение долга, совпадение сторон, "
            "невозможность исполнения, акт органа власти, смерть и ликвидация проверяются "
            "по разным формальным путям."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "obligation_dynamics_articles_414_419",
            "legal_reference": "ГК РФ, статьи 414–419",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum54-party-change-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ о перемене лиц",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: распорядительный эффект уступки, "
            "положение должника, договорные ограничения и процессуальное правопреемство "
            "требуют самостоятельной проверки."
        ),
        valid_from="2017-12-21",
        metadata={
            "synthetic": True,
            "topic": "obligation_dynamics_party_change_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 21.12.2017 № 54",
            "basis_url": "https://vsrf.ru/documents/own/26276/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum6-discharge-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ о прекращении обязательств",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: соглашение об отступном и его "
            "предоставление, заявление о зачете, ясная воля на новацию и объективная "
            "невозможность исполнения не подменяют друг друга."
        ),
        valid_from="2020-06-11",
        metadata={
            "synthetic": True,
            "topic": "obligation_dynamics_discharge_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 11.06.2020 № 6",
            "basis_url": "https://www.vsrf.ru/documents/own/29023/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-obligation-dynamics-evidence",
        title="Синтетическая проверенная запись перемены лиц и прекращения обязательства",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: состав сторон не изменялся, поставка исполнена после "
            "просрочки, основная обязанность исполнена, а ранее возникший вопрос "
            "ответственности сохраняется."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "obligation_dynamics_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk309-328-performance-v1",
        title="Синтетическая проверенная модель исполнения обязательств",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: надлежащий предмет, срок, место и получатель, "
            "частичное, досрочное и третьелицевое исполнение, множественность лиц и "
            "встречное исполнение проверяются раздельно."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "performance_articles_309_328",
            "legal_reference": "ГК РФ, статьи 309–328",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk393-4061-remedies-v1",
        title="Синтетическая проверенная модель последствий нарушения обязательств",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: убытки, замещающая сделка, проценты, "
            "исполнение в натуре, субсидиарная ответственность, просрочка сторон и "
            "возмещение потерь имеют самостоятельные предпосылки."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "remedies_articles_393_406_1",
            "legal_reference": "ГК РФ, статьи 393–406.1",
            "basis_url": "https://government.ru/docs/all/95825/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum54-performance-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ об исполнении обязательств",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: принятие частичного и "
            "третьелицевого исполнения, полномочия получателя, срок, платеж и встречное "
            "исполнение требуют самостоятельной проверки."
        ),
        valid_from="2016-11-22",
        metadata={
            "synthetic": True,
            "topic": "performance_plenum_54_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 22.11.2016 № 54",
            "basis_url": "https://vsrf.ru/documents/own/8524/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum7-remedies-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ о средствах защиты",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: реальный ущерб, упущенная выгода, "
            "разумная достоверность, проценты, исполнение в натуре и возмещение потерь "
            "не подменяют друг друга."
        ),
        valid_from="2016-03-24",
        metadata={
            "synthetic": True,
            "topic": "remedies_plenum_7_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 24.03.2016 № 7",
            "basis_url": "https://www.vsrf.ru/documents/own/8478/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-performance-remedies-evidence",
        title="Синтетическая проверенная запись исполнения и средств защиты",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: поставка произведена с просрочкой надлежащему "
            "получателю, денежное требование и убытки в демонстрационном деле не заявлены."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "performance_remedies_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk454-464-sale-transfer-v1",
        title="Синтетическая проверенная модель предмета и передачи товара",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: квалификация купли-продажи, предмет, количество, "
            "передача товара, принадлежностей и документов, срок, момент исполнения, риск, "
            "права третьих лиц и эвикция проверяются раздельно."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "sale_articles_454_464",
            "legal_reference": "ГК РФ, статьи 454–464",
            "basis_url": "https://government.ru/docs/all/96096/?page=3",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk465-477-sale-conformity-v1",
        title="Синтетическая проверенная модель соответствия товара",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: количество, ассортимент, качество, гарантия, "
            "срок годности, проверка качества, недостатки и сроки их обнаружения имеют "
            "самостоятельные предпосылки и распределение бремени доказывания."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "sale_articles_465_477",
            "legal_reference": "ГК РФ, статьи 465–477",
            "basis_url": "https://government.ru/docs/all/96096/?page=3",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk478-491-sale-payment-v1",
        title="Синтетическая проверенная модель комплектности, приемки и оплаты",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: комплектность, комплект, тара, извещение, "
            "принятие, цена, оплата, предоплата, кредит, рассрочка, страхование и сохранение "
            "права собственности проверяются отдельными юридическими путями."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "sale_articles_478_491",
            "legal_reference": "ГК РФ, статьи 478–491",
            "basis_url": "https://government.ru/docs/all/96096/?page=3",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-vs-review2024-sale-quality-v1",
        title="Синтетическая модель актуальных позиций ВС РФ о недостатках товара",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление судебных позиций: гарантийный срок влияет на "
            "распределение бремени доказывания, а безрезультатный гарантийный ремонт не "
            "прекращает предусмотренные законом требования покупателя."
        ),
        valid_from="2024-10-09",
        metadata={
            "synthetic": True,
            "topic": "sale_quality_supreme_court_review_2024",
            "legal_reference": (
                "Обзор судебной практики ВС РФ № 2, 3 (2024), определение № 301-ЭС23-10631"
            ),
            "basis_url": "https://www.vsrf.ru/documents/reviews/34051/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-general-sale-evidence",
        title="Синтетическая проверенная запись общих фактов купли-продажи",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: товар передан покупателю с просрочкой; предмет и цена "
            "согласованы, количество, качество, комплектность и упаковка соответствуют "
            "договору, требования об оплате и прекращении не заявлены."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "general_sale_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk506-512-supply-framework-v1",
        title="Синтетическая проверенная модель заключения и исполнения поставки",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: признаки поставки, согласование разногласий, "
            "периоды, отгрузочная разнарядка, транспорт, восполнение недопоставки и "
            "ассортимент проверяются как самостоятельные юридические вопросы."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "supply_articles_506_512",
            "legal_reference": "ГК РФ, статьи 506–512",
            "basis_url": "https://government.ru/docs/all/96096/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk513-517-supply-acceptance-v1",
        title="Синтетическая проверенная модель приемки товара по договору поставки",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: приемка, письменное извещение, ответственное "
            "хранение, выборка, оплата получателем и возврат тары проверяются раздельно."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "supply_articles_513_517",
            "legal_reference": "ГК РФ, статьи 513–517",
            "basis_url": "https://government.ru/docs/all/96096/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk518-524-supply-remedies-v1",
        title="Синтетическая проверенная модель специальных средств защиты по поставке",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: последствия недостатков и некомплектности, "
            "заменяющая закупка, удержание оплаты, неустойка, распределение исполнения, "
            "односторонний отказ и ценовые убытки проверяются отдельными путями."
        ),
        valid_from="1996-03-01",
        metadata={
            "synthetic": True,
            "topic": "supply_articles_518_524",
            "legal_reference": "ГК РФ, статьи 518–524",
            "basis_url": "https://government.ru/docs/all/96096/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum18-supply-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВАС РФ о договоре поставки",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: квалификация определяется "
            "признаками статьи 506 ГК РФ с учетом розничного контекста, неуказанный срок "
            "определяется по общим правилам, а инструкции П-6 и П-7 применяются к приемке "
            "только при договорной отсылке."
        ),
        valid_from="1997-10-22",
        metadata={
            "synthetic": True,
            "topic": "supply_plenum_guidance",
            "legal_reference": "Постановление Пленума ВАС РФ от 22.10.1997 № 18",
            "basis_url": "https://www.consultant.ru/document/cons_doc_LAW_17621/",
            "official_practice_confirmation_url": (
                "https://vsrf.ru/lk/practice/stor_pdf_ec/1655326"
            ),
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-special-supply-evidence",
        title="Синтетическая проверенная запись специальных фактов поставки",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: предпринимательская поставка завершена с просрочкой; "
            "количество, качество и комплектность соответствуют договору, специальные "
            "требования из недопоставки и прекращения не заявлены."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "special_supply_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
    LegalSource(
        id="synthetic-ru-gk401-liability-model-v1",
        title="Синтетическая проверенная модель оснований ответственности по статье 401 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: для ответственности и освобождения отдельно "
            "проверяются вина, характер деятельности должника, непреодолимая сила и "
            "исключенные обычные коммерческие риски."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "liability_article_401",
            "legal_reference": "ГК РФ, статья 401",
            "basis_url": "https://minjust.gov.ru/ru/pages/grazhdanskij-kodeks/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-gk333-penalty-model-v1",
        title="Синтетическая проверенная модель снижения неустойки по статье 333 ГК РФ",
        source_type=SourceType.STATUTE,
        text=(
            "Синтетическое представление: модель проверяет заявление предпринимателя, "
            "явную несоразмерность и риск необоснованной выгоды, но не определяет размер "
            "снижения и не подменяет судебную оценку."
        ),
        valid_from="2015-06-01",
        metadata={
            "synthetic": True,
            "topic": "penalty_article_333",
            "legal_reference": "ГК РФ, статья 333",
            "basis_url": "https://minjust.gov.ru/ru/pages/grazhdanskij-kodeks/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-ru-plenum7-liability-guidance-v1",
        title="Синтетическая модель разъяснений Пленума ВС РФ об ответственности",
        source_type=SourceType.CASE_LAW,
        text=(
            "Синтетическое представление разъяснений: бремя доказывания, признаки "
            "непреодолимой силы, исключенные коммерческие риски и предпосылки снижения "
            "неустойки проверяются раздельно."
        ),
        valid_from="2017-02-07",
        metadata={
            "synthetic": True,
            "topic": "liability_plenum_guidance",
            "legal_reference": "Постановление Пленума ВС РФ от 24.03.2016 № 7",
            "basis_url": "https://www.vsrf.ru/documents/own/8478/",
            "review_required": True,
        },
    ),
    LegalSource(
        id="synthetic-case-supply-1-liability-evidence",
        title="Синтетическая проверенная запись фактов об ответственности и неустойке",
        source_type=SourceType.FACT,
        text=(
            "Синтетическая запись: факты, относящиеся к вине, освобождению от "
            "ответственности и заявлению о снижении неустойки, одобрены для Этапа 0."
        ),
        valid_from="2026-01-01",
        metadata={
            "synthetic": True,
            "non_authoritative": True,
            "topic": "liability_case_evidence",
            "case_id": "case-supply-1",
        },
    ),
]


def get_synthetic_contract_source(source_id: str) -> LegalSource:
    for source in SYNTHETIC_CONTRACT_SOURCES:
        if source.id == source_id:
            return source
    msg = f"Unknown synthetic contract source: {source_id}"
    raise KeyError(msg)
