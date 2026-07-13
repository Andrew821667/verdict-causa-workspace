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
