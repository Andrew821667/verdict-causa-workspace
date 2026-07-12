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
