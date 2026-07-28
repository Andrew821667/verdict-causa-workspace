from enum import Enum

from pydantic import BaseModel, Field

from causa import __version__ as CORE_VERSION
from causa.core.bootstrap import (
    DEFAULT_BOOTSTRAP_SCHEMA_VERSION,
    DEFAULT_TRANSLATOR_VERSION,
)
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.institutional.contracts.reviewed_analysis import (
    ANALYSIS_PIPELINE_VERSION,
    CASE_EVIDENCE_SCHEMA_VERSION,
)


class CompatibilityStatus(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"


class PackageCompatibilityEntry(BaseModel):
    package_version: str
    core_version: str
    bootstrap_schema_versions: list[str] = Field(default_factory=list)
    translator_versions: list[str] = Field(default_factory=list)
    case_evidence_schema_versions: list[str] = Field(default_factory=list)
    analysis_pipeline_versions: list[str] = Field(default_factory=list)
    status: CompatibilityStatus
    notes: list[str] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


class PackageCompatibilityCheck(BaseModel):
    package_id: str
    package_version: str
    core_version: str
    bootstrap_schema_version: str
    translator_version: str
    case_evidence_schema_version: str
    analysis_pipeline_version: str
    supported: bool
    reasons: list[str] = Field(default_factory=list)
    reasons_ru: list[str] = Field(default_factory=list)


CONTRACTS_PACKAGE_COMPATIBILITY = [
    PackageCompatibilityEntry(
        package_version="0.46.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed building-lease evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 650 through 655.",
            "Qualification, single-document form, registration for one-year terms, land rights, preserved land use, essential rent term, and transfer and return deeds remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные об аренде зданий и сооружений обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 650–655 ГК РФ.",
            "Квалификация, форма одного документа, регистрация при сроке не менее года, права на земельный участок, сохранение права пользования, существенное условие о плате и акты передачи и возврата разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.45.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed vehicle-lease evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 632 through 649.",
            "Qualification, written form, renewal unavailability, maintenance duty, crew service, operating costs, insurance, sublease freedom, and third-party liability remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные об аренде транспортных средств обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 632–649 ГК РФ.",
            "Квалификация, письменная форма, неприменение преимущественного права, содержание и ремонт, услуги экипажа, расходы по эксплуатации, страхование, субаренда и ответственность за вред третьим лицам разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.44.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed rental evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 626 through 631.",
            "Qualification, written form, term limit, renewal unavailability, defect cost allocation, defect remedy deadline, early-return refund, repair duty, and transfer restriction remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о прокате обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 626–631 ГК РФ.",
            "Квалификация, письменная форма, предельный срок, неприменение преимущественного права, распределение расходов на недостатки, срок устранения недостатков, возврат части платы, обязанность по ремонту и запрет распоряжения разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.43.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed lease evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 606 through 625.",
            "Qualification, object definiteness, form, defect liability, third-party rights, sublease consent, capital repair, termination, preferential renewal, and improvements remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные об аренде обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 606–625 ГК РФ.",
            "Квалификация, определённость объекта, форма, ответственность за недостатки, права третьих лиц, согласие на субаренду, капитальный ремонт, расторжение, преимущественное право и улучшения разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.42.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed annuity evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 583 through 605.",
            "Qualification, notarial form, security, overdue interest, permanent-rent redemption, life-annuity termination, and maintenance encumbrance remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о ренте обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 583–605 ГК РФ.",
            "Квалификация, нотариальная форма, обеспечение, проценты за просрочку, выкуп постоянной ренты, расторжение пожизненной ренты и обременение имущества разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.41.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed gift evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 572 through 582.",
            "Qualification, sham detection, form voidness, prohibition, restriction, donee refusal, revocation, and charitable donation remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о дарении обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 572–582 ГК РФ.",
            "Квалификация, притворность, ничтожность формы, запрещение, ограничение, отказ одаряемого, отмена и пожертвование разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.40.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed barter evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 567 through 571.",
            "Qualification, subsidiary sale rules, price difference, counter-performance, simultaneous ownership transfer, and eviction remedy remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о мене обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 567–571 ГК РФ.",
            "Квалификация, субсидиарные правила купли-продажи, разница в цене, встречное исполнение, одновременный переход права и средство защиты при изъятии разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.39.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed enterprise sale evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 559 through 566.",
            "Qualification, form and registration, composition certification, creditor protection, transfer, and price reduction remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о продаже предприятия обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 559–566 ГК РФ.",
            "Квалификация, форма и регистрация, удостоверение состава, права кредиторов, передача и уменьшение цены разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.38.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed real estate sale evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 549 through 558.",
            "Qualification, written form, essential terms, ownership registration, deed transfer, and quality remedies remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о продаже недвижимости обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 549–558 ГК РФ.",
            "Квалификация, письменная форма, существенные условия, регистрация перехода права, передача по акту и средства защиты по качеству разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.37.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed energy supply evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 539 through 548.",
            "Energy supply qualification, quantity and quality, network duties, metered payment, and interruption lawfulness remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные об энергоснабжении обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 539–548 ГК РФ.",
            "Квалификация энергоснабжения, количество и качество энергии, содержание сетей, оплата по учёту и правомерность перерыва подачи разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.36.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed contractation evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 535 through 538.",
            "Contractation qualification, procurer duties, and fault-based producer liability remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о контрактации обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 535–538 ГК РФ.",
            "Квалификация контрактации, обязанности заготовителя и виновная ответственность производителя разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.35.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed state supply evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 525 through 534.",
            "State contract conclusion, buyer attachment, payment, and loss compensation remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о поставке для государственных нужд обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 525–534 ГК РФ.",
            "Заключение контракта, прикрепление покупателя, оплата и возмещение убытков разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.34.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed retail sale evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 492 through 505.",
            "Retail contract nature, information duty, quality remedies, and exchange remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о розничной купле-продаже обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 492–505 ГК РФ.",
            "Публичность договора, информация, права по качеству и обмен разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.33.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed general obligations evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 307 through 308.3.",
            "Obligation concept, alternative and facultative obligations, and creditor protection remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные об общих положениях об обязательствах обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 307–308.3 ГК РФ.",
            "Понятие обязательства, альтернативные и факультативные обязательства и защита кредитора разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.32.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed procedure evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 445 through 449.",
            "Mandatory conclusion and auction paths remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о порядке заключения договора обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 445–449 ГК РФ.",
            "Обязательное заключение и заключение на торгах разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.31.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed freedom evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 421 through 424.",
            "Freedom of contract, conformity to law, onerousness, and price paths remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о свободе договора и цене обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 421–424 ГК РФ.",
            "Свобода договора, соответствие закону, возмездность и цена разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.30.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed framework evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 429.1 and 429.4.",
            "Framework agreement and subscription agreement paths remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о рамочном и абонентском договоре обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 429.1 и 429.4 ГК РФ.",
            "Рамочный договор и абонентский договор разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.29.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed option evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 429.2 and 429.3.",
            "Option offer, option contract, and payment paths remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные об опционных конструкциях обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 429.2 и 429.3 ГК РФ.",
            "Опцион на заключение договора, опционный договор и платёж разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.28.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed precontractual evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code article 434.1.",
            "Bad-faith negotiation, confidentiality breach, and void limitation remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о преддоговорной ответственности обязательны для пути Этапа 0.",
            "Формальные границы охватывают статью 434.1 ГК РФ.",
            "Недобросовестные переговоры, нарушение конфиденциальности и ничтожность ограничения разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.27.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed representations evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code article 431.2.",
            "Liability, rescission, and avoidance-for-deception paths remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о заверениях об обстоятельствах обязательны для пути Этапа 0.",
            "Формальные границы охватывают статью 431.2 ГК РФ.",
            "Ответственность, отказ от договора и оспаривание при обмане разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.26.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed adhesion-contract evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code article 428.",
            "Adhesion regime, grounds for relief, and the business-actor bar remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о договоре присоединения обязательны для пути Этапа 0.",
            "Формальные границы охватывают статью 428 ГК РФ.",
            "Режим присоединения, основания для изменения и ограничение для предпринимателя разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.25.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed public-contract evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code article 426.",
            "Duty to contract, non-preference, uniform terms, and void terms remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о публичном договоре обязательны для пути Этапа 0.",
            "Формальные границы охватывают статью 426 ГК РФ.",
            "Обязанность заключить, недопустимость предпочтения, единые условия и ничтожность разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.24.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed third-party-beneficiary evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code article 430.",
            "Right to demand, binding effect after intent, and creditor fallback remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о договоре в пользу третьего лица обязательны для пути Этапа 0.",
            "Формальные границы охватывают статью 430 ГК РФ.",
            "Право требования, связанность после намерения и переход права к кредитору разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.23.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed preliminary-contract evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code article 429 and article 445 paragraph 4.",
            "Conclusion, form, term, evasion, compulsion, and termination remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о предварительном договоре обязательны для пути Этапа 0.",
            "Формальные границы охватывают статью 429 и пункт 4 статьи 445 ГК РФ.",
            "Заключение, форма, срок, уклонение, понуждение и прекращение разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.22.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed form evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 158 through 165 and 434.",
            "Oral, written, and notarial form and their noncompliance effects remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о форме сделки обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 158–165 и 434 ГК РФ.",
            "Устная, письменная и нотариальная форма и последствия несоблюдения разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.21.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed interpretation evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code article 431.",
            "Literal reading, systematic reading, and common intent remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о толковании договора обязательны для пути Этапа 0.",
            "Формальные границы охватывают статью 431 ГК РФ.",
            "Буквальное значение, сопоставление с договором в целом и общая воля разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.20.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed limitation evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 195 through 208.",
            "Start of running, term elapse, suspension, interruption, and party plea remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные об исковой давности обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 195–208 ГК РФ.",
            "Начало течения, истечение срока, приостановление, перерыв и заявление стороны разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.19.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed temporal-effect evidence is mandatory for the Phase 0 analysis path.",
            "Formal boundaries cover Civil Code articles 425 and 433.",
            "Conclusion moment, entry into force, retroactive effect, and term end remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о действии договора во времени обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 425 и 433 ГК РФ.",
            "Момент заключения, вступление в силу, обратное действие и окончание срока разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.18.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Pilot observations require an approved v1 admission gate and replayable trace.",
            "Pilot artifacts contain only pseudonymous manifests and content hashes.",
            "External model access and cross-border transfer remain blocked in gate v1.",
        ],
        notes_ru=[
            "Пилотные наблюдения требуют одобренного gate v1 и воспроизводимой трассировки.",
            "Пилотные артефакты содержат только псевдонимные манифесты и hash содержимого.",
            "Внешняя модель и трансграничная передача остаются запрещены gate v1.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.17.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v9"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v9"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed general-sale evidence is mandatory before special-supply evaluation.",
            "Formal boundaries cover Civil Code articles 454 through 491.",
            "Transfer, risk, title, conformity, acceptance, payment, and remedies remain distinct.",
        ],
        notes_ru=[
            "Проверенные общие данные о купле-продаже обязательны до проверки специальных правил поставки.",
            "Формальные границы охватывают статьи 454–491 ГК РФ.",
            "Передача, риск, титул, соответствие, приемка, оплата и средства защиты разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.16.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v8"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v8"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed special-supply evidence is mandatory for the synthetic supply path.",
            "Formal boundaries cover Civil Code articles 506 through 524.",
            "Acceptance, short delivery, defects, refusal, and price damages remain distinct.",
        ],
        notes_ru=[
            "Проверенные специальные данные о поставке обязательны для синтетического пути поставки.",
            "Формальные границы охватывают статьи 506–524 ГК РФ.",
            "Приемка, недопоставка, недостатки, отказ и ценовые убытки разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.15.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v7"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v7"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed performance-remedies evidence is mandatory after obligation evaluation.",
            "Formal boundaries cover Civil Code articles 309 through 328 and 393 through 406.1.",
            "Performance, delay, damages, interest, specific relief, and indemnity remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные об исполнении и средствах защиты обязательны после проверки обязательства.",
            "Формальные границы охватывают статьи 309–328 и 393–406.1 ГК РФ.",
            "Исполнение, просрочка, убытки, проценты, исполнение в натуре и возмещение потерь разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.14.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v6"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v6"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed obligation-dynamics evidence is mandatory after obligation evaluation.",
            "Formal boundaries cover Civil Code articles 382 through 419.",
            "Party changes remain distinct from full and partial obligation discharge paths.",
        ],
        notes_ru=[
            "Проверенные данные о динамике обязательства обязательны после проверки исполнения.",
            "Формальные границы охватывают статьи 382–419 ГК РФ.",
            "Перемена лиц отделена от полного и частичного прекращения обязательства.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.13.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v5"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v5"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed performance-security evidence is mandatory after obligation evaluation.",
            "Formal boundaries cover Civil Code articles 329 through 381.2.",
            "Pledge, retention, suretyship, independent guarantee, deposit, and security payment remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные об обеспечении исполнения обязательны после проверки основного обязательства.",
            "Формальные границы охватывают статьи 329–381.2 ГК РФ.",
            "Залог, удержание, поручительство, независимая гарантия, задаток и обеспечительный платеж разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.12.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v4"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v4"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed transaction-invalidity evidence is mandatory before contractual effects.",
            "Formal boundaries cover Civil Code articles 166 through 181.",
            "Void and voidable grounds, standing, judgment, limitation, and effects remain distinct.",
        ],
        notes_ru=[
            "Проверенные данные о недействительности обязательны до договорных последствий.",
            "Формальные границы охватывают статьи 166–181 ГК РФ.",
            "Ничтожность, оспоримость, заявитель, решение, срок и последствия разделены.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.11.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v3"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v3"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed change-and-termination evidence is mandatory for the Phase 0 path.",
            "Formal boundaries cover Civil Code articles 450 through 453 and article 310.",
            "Judicial prerequisites remain distinct from an effective court judgment.",
        ],
        notes_ru=[
            "Проверенные данные об изменении и расторжении обязательны для пути Этапа 0.",
            "Формальные границы охватывают статьи 450–453 и статью 310 ГК РФ.",
            "Судебные предпосылки отделены от вступившего в силу решения суда.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.10.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v2"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v2"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed contract-formation evidence is mandatory before obligation analysis.",
            "Formal boundaries cover Civil Code articles 432, 435, 438, and 443.",
            "The model does not determine evidence weight or a court outcome.",
        ],
        notes_ru=[
            "Проверенные данные о заключении договора обязательны до анализа обязательства.",
            "Формальные границы охватывают статьи 432, 435, 438 и 443 ГК РФ.",
            "Модель не определяет вес доказательств и результат суда.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.9.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v1"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v1"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Reviewed liability evidence is mandatory for the synthetic Phase 0 path.",
            "Formal models cover narrow prerequisites under Civil Code articles 333 and 401.",
            "The model does not determine evidence weight, penalty amount, or a court outcome.",
        ],
        notes_ru=[
            "Проверенные данные об ответственности обязательны для синтетического пути Этапа 0.",
            "Формальная модель покрывает узкие предпосылки статей 333 и 401 ГК РФ.",
            "Модель не определяет вес доказательств, размер снижения или результат суда.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.8.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v0"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "A versioned legal-operator library provides bounded contractual counterfactuals.",
            "Counterfactual branches preserve baseline facts and enforce fact and scenario budgets.",
            "Dedicated benchmark and red-team suites cover operator behavior and bypass attempts.",
        ],
        notes_ru=[
            "Версионированная библиотека legal operators реализует ограниченные договорные контрфакты.",
            "Контрфактические ветви сохраняют исходные факты и соблюдают бюджеты изменений и сценариев.",
            "Отдельные benchmark и Red Team покрывают поведение операторов и попытки обхода ограничений.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.7.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v0"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Russian legal explanations are rendered at executive, professional, and forensic levels.",
            "Template and policy hashes support deterministic faithfulness checks.",
            "Human usability still requires a lawyer pilot.",
        ],
        notes_ru=[
            "Русские юридические объяснения формируются на кратком, профессиональном и forensic-уровнях.",
            "Hash шаблонов и политики обеспечивает детерминированную проверку верности.",
            "Практическая понятность по-прежнему требует пилотной проверки юристами.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.6.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v0"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Decision traces bind policy snapshot id and SHA-256 content hash.",
            "Management Plane policy registration, activation, diff, and rollback are auditable.",
            "No production or real-client-data compatibility claim is implied.",
        ],
        notes_ru=[
            "Трассировка связывает ID снимка политики и SHA-256 hash его содержимого.",
            "Регистрация, активация, semantic diff и откат политик Management Plane аудируемы.",
            "Совместимость с промышленной эксплуатацией и реальными клиентскими данными не заявляется.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.5.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v0"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Russian human-readable reasons are additive to stable machine contracts.",
            "Governance execution records are exported in ru-RU for the Russian-law package.",
            "No production or real-client-data compatibility claim is implied.",
        ],
        notes_ru=[
            "Русские человекочитаемые причины добавлены без изменения стабильных машинных контрактов.",
            "Governance-записи экспортируются с локалью ru-RU для российского правового пакета.",
            "Совместимость с промышленной эксплуатацией и реальными клиентскими данными не заявляется.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.4.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        case_evidence_schema_versions=["contracts.case-evidence.v0"],
        analysis_pipeline_versions=["contracts-reviewed-analysis-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Synthetic Phase 0 analysis requires reviewed case, temporal, and authority inputs.",
            "Every mapped formal fact retains assertion and source provenance.",
            "No production or real-client-data compatibility claim is implied.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.3.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Synthetic Phase 0 formal checks add damages remedy, causation, and limitation predicates.",
            "No production or real-client-data compatibility claim is implied.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.2.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Synthetic Phase 0 authority policy adds constitutional and regulatory levels.",
            "No production or real-client-data compatibility claim is implied.",
        ],
    ),
    PackageCompatibilityEntry(
        package_version="0.1.0",
        core_version="0.1.0",
        bootstrap_schema_versions=["contracts.norm.v0"],
        translator_versions=["contracts-json-to-formal-v0"],
        status=CompatibilityStatus.SUPPORTED,
        notes=[
            "Phase 0 synthetic contractual package only.",
            "No production or real-client-data compatibility claim is implied.",
        ],
    ),
]


def evaluate_contracts_package_compatibility(
    core_version: str = CORE_VERSION,
    bootstrap_schema_version: str = DEFAULT_BOOTSTRAP_SCHEMA_VERSION,
    translator_version: str = DEFAULT_TRANSLATOR_VERSION,
    case_evidence_schema_version: str = CASE_EVIDENCE_SCHEMA_VERSION,
    analysis_pipeline_version: str = ANALYSIS_PIPELINE_VERSION,
) -> PackageCompatibilityCheck:
    matching_entries = [
        entry
        for entry in CONTRACTS_PACKAGE_COMPATIBILITY
        if entry.package_version == CONTRACTS_PACKAGE_MANIFEST.version
        and entry.core_version == core_version
        and bootstrap_schema_version in entry.bootstrap_schema_versions
        and translator_version in entry.translator_versions
        and case_evidence_schema_version in entry.case_evidence_schema_versions
        and analysis_pipeline_version in entry.analysis_pipeline_versions
        and entry.status == CompatibilityStatus.SUPPORTED
    ]
    supported = bool(matching_entries)
    reasons = (
        ["Package, core, schemas, translator, and analysis pipeline coordinates are supported."]
        if supported
        else ["No supported compatibility entry matches the supplied coordinates."]
    )
    reasons_ru = (
        ["Координаты пакета, ядра, схем, транслятора и analysis pipeline поддерживаются."]
        if supported
        else ["Для переданных координат отсутствует поддерживаемая запись совместимости."]
    )

    return PackageCompatibilityCheck(
        package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        package_version=CONTRACTS_PACKAGE_MANIFEST.version,
        core_version=core_version,
        bootstrap_schema_version=bootstrap_schema_version,
        translator_version=translator_version,
        case_evidence_schema_version=case_evidence_schema_version,
        analysis_pipeline_version=analysis_pipeline_version,
        supported=supported,
        reasons=reasons,
        reasons_ru=reasons_ru,
    )
