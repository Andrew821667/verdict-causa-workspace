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
