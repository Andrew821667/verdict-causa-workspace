"""Формальная модель освобождения гражданина от обязательств.

Статья 213.28 закона 127-ФЗ: завершение расчётов с кредиторами и освобождение
гражданина от обязательств. Последняя из трёх статей главы X, названных долгом
в выпуске 1.25.0, и самая спорная: именно вокруг освобождения от обязательств и
его исключений идут реальные дела.

## Два разных механизма, которые легко смешать

Статья не даёт одного ответа «освобождён или нет». Она даёт два, и они работают
на разных уровнях:

* **пункт 4 — освобождение не допускается вовсе.** Уровень должника: гражданин
  не освобождается ни от одного требования. Три основания, и все три о его
  собственном поведении.
* **пункты 5 и 6 — требование сохраняет силу.** Уровень требования:
  освобождение состоялось, но этого требования не достигает. Перечень
  требований, а не поведение должника.

Плюс абзац второй пункта 3 добавляет ещё два изъятия уровня требования:
требования, о которых кредиторы не знали и не должны были знать, и требования, в
счёт которых заключено отдельное мировое соглашение по статье 213.10-1.

Смешение двух уровней дало бы ровно ту ошибку, которая в споре дороже всего:
из сохранения силы одного требования вывести, что гражданин не освобождён ни от
чего. Поэтому модель выводит их раздельно, а вывод «требование погашено»
собирает из обоих.

## Пункт 4: три основания недопустимости

1. **Привлечение к ответственности за банкротные правонарушения** — уголовной
   или административной, за неправомерные действия при банкротстве,
   преднамеренное или фиктивное банкротство, **при условии, что правонарушения
   совершены в данном деле**. Оговорка о «данном деле» существенна: прошлое
   банкротное правонарушение гражданина основанием не является.
2. **Непредоставление или искажение сведений** управляющему или суду, **и это
   установлено судебным актом, принятым при рассмотрении данного дела**.
3. **Незаконное поведение при возникновении или исполнении обязательства**, на
   котором кредитор основал требование: мошенничество, злостное уклонение от
   погашения задолженности, уклонение от уплаты налогов, заведомо ложные
   сведения при получении кредита, сокрытие или умышленное уничтожение
   имущества. Условие — «доказано», и доказывание здесь оценивает суд, поэтому
   это основание всегда поднимает флаг юриста.

## Пункты 5 и 6: что сохраняет силу

Пункт 5 называет требования, неразрывно связанные с личностью кредитора:
текущие платежи, вред жизни или здоровью, заработная плата и выходное пособие,
моральный вред, алименты — **и иные требования, неразрывно связанные с
личностью кредитора**. Последнее — открытая оценочная категория, и она выведена
отдельным предикатом: названное требование модель квалифицирует сама, а
«иное неразрывно связанное» оставляет суду и поднимает флаг.

Пункт 6 распространяет правило пункта 5 ещё на пять требований, и **оговорка о
вине относится не ко всем**:

| Требование | «умышленно или по грубой неосторожности» |
|---|---|
| субсидиарная ответственность контролирующего лица (глава III.2) | **нет** |
| убытки юридическому лицу как участником или членом коллегиальных органов (статьи 53 и 53.1 ГК РФ) | да |
| убытки как арбитражным управляющим | да |
| вред имуществу | да |
| последствия недействительности сделки (статьи 61.2, 61.3) | **нет** |

Распространить оговорку о вине на субсидиарную ответственность или на
последствия недействительности сделки значило бы освободить гражданина от них
при недоказанной форме вины, чего пункт 6 не говорит. Это прочтение закреплено
отдельными случаями red-team.

## Стык со статьёй 53.1 ГК РФ, которого нет

Пункт 6 называет статьи 53 и 53.1 ГК РФ, и модель ответственности управляющих
лиц в пакете есть. Связи между институтами тем не менее **нет, и это решение, а
не упущение**: институт статьи 53.1 отвечает, возникла ли ответственность, а
этот — достигает ли освобождение требования о ней. Требование сохраняет силу
независимо от того, будет ли оно в итоге удовлетворено, а формы вины у двух
статей разные: статья 53.1 говорит о недобросовестности и неразумности, пункт 6
статьи 213.28 — об умысле и грубой неосторожности. Сверять их означало бы
приравнять то, что закон различает.

## Пункт 5 абзац 2: исполнительные листы

На неудовлетворённые сохранившие силу требования, **включённые в реестр**, суд
выдаёт исполнительные листы. Правило относится к требованиям пункта 5, а через
отсылку пункта 6 — и к его пяти категориям.

## Чего модель не делает

* **Не разбирает процедуру** представления и рассмотрения отчёта финансового
  управляющего (пункты 1 и 2): определение о завершении реализации имущества
  принимается как проверенный факт.
* **Не оценивает размер непогашенной части** требования: статья говорит о
  предъявлении требования в непогашенной части, а не о её исчислении.
* **Не разбирает субсидиарную ответственность** (глава III.2), ответственность
  арбитражного управляющего и оспаривание сделок по статьям 61.2 и 61.3 — все
  они названы как категории требований, а не смоделированы.
* **Не моделирует мировое соглашение** по статье 213.10-1: факт его утверждения
  принимается от рецензента.
* **Отвечает об одном требовании** одного гражданина: контракт данных даёт один
  блок доказательств на институт.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

CITIZEN_RELEASE_EVIDENCE_SCHEMA_VERSION = "contracts.citizen-release-evidence.v0"
CITIZEN_RELEASE_MAPPING_VERSION = "contracts-reviewed-citizen-release-to-facts-v0"
CITIZEN_RELEASE_MODEL_VERSION = "contracts-citizen-release-article-213-28-127fz-v0"

# Дословный текст статьи 213.28 закона 127-ФЗ — synthetic_sources.py,
# synthetic-ru-127fz-213.28-citizen-release-from-obligations-v1. Статья 213.27 —
# та очерёдность, к пункту 6 которой («за исключением случаев, предусмотренных
# настоящим Федеральным законом») эта статья и является исключением; статья
# 213.1 отвечает, к какому должнику глава X применяется; статья 53.1 ГК РФ
# названа пунктом 6 как основание одного из сохраняющихся требований.
CITIZEN_RELEASE_LEGAL_SOURCE_REFS = (
    "synthetic-ru-127fz-213.28-citizen-release-from-obligations-v1",
    "synthetic-ru-127fz-213.27-citizen-creditor-ranking-v1",
    "synthetic-ru-127fz-213.1-citizen-bankruptcy-regulation-v1",
    "synthetic-ru-gk53-1-management-liability-v1",
)


class CitizenReleaseEvidencePredicate(str, Enum):
    # --- Предпосылки: пункты 2 и 3 ---
    # Гражданин признан банкротом.
    CITIZEN_DECLARED_BANKRUPT = "citizen_declared_bankrupt"
    # Вынесено определение о завершении реализации имущества гражданина
    # (пункт 2). До него вопроса об освобождении нет.
    PROPERTY_REALISATION_COMPLETED_BY_COURT_RULING = (
        "property_realisation_completed_by_court_ruling"
    )

    # --- Пункт 4: три основания недопустимости освобождения ---
    # Привлечён к уголовной или административной ответственности за неправомерные
    # действия при банкротстве, преднамеренное или фиктивное банкротство, и
    # правонарушения совершены в данном деле о банкротстве.
    HELD_LIABLE_FOR_BANKRUPTCY_OFFENCE_IN_THIS_CASE = (
        "held_liable_for_bankruptcy_offence_in_this_case"
    )
    # Не предоставил необходимые сведения либо предоставил заведомо
    # недостоверные управляющему или суду, и это установлено судебным актом,
    # принятым при рассмотрении данного дела.
    WITHHELD_OR_FALSIFIED_INFORMATION_ESTABLISHED_BY_COURT = (
        "withheld_or_falsified_information_established_by_court"
    )
    # Доказано незаконное поведение при возникновении или исполнении
    # обязательства, на котором кредитор основал требование.
    ACTED_UNLAWFULLY_IN_THE_OBLIGATION_RELIED_ON = "acted_unlawfully_in_the_obligation_relied_on"

    # --- Требование ---
    # Включено в реестр требований кредиторов: условие выдачи исполнительного
    # листа по абзацу второму пункта 5.
    CLAIM_FILED_IN_BANKRUPTCY_REGISTER = "claim_filed_in_bankruptcy_register"
    # Требование по текущим платежам: пункт 5 называет их первыми.
    IS_CURRENT_PAYMENT_CLAIM = "is_current_payment_claim"
    # Требование прямо названо пунктом 5: вред жизни или здоровью, заработная
    # плата, выходное пособие, моральный вред, алименты.
    IS_CLAIM_NAMED_IN_PARAGRAPH_FIVE = "is_claim_named_in_paragraph_five"
    # Иное требование, неразрывно связанное с личностью кредитора. Открытая
    # оценочная категория пункта 5: её устанавливает суд.
    IS_OTHER_CLAIM_INSEPARABLE_FROM_THE_CREDITORS_PERSON = (
        "is_other_claim_inseparable_from_the_creditors_person"
    )

    # --- Пункт 6: пять категорий, и оговорка о вине не ко всем ---
    # Привлечение гражданина как контролирующего лица к субсидиарной
    # ответственности (глава III.2). Формы вины пункт 6 здесь не требует.
    IS_SUBSIDIARY_LIABILITY_CLAIM = "is_subsidiary_liability_claim"
    # Возмещение убытков юридическому лицу, участником или членом коллегиальных
    # органов которого был гражданин (статьи 53 и 53.1 ГК РФ). Требует умысла
    # или грубой неосторожности.
    IS_DAMAGES_CLAIM_UNDER_ARTICLES_53_AND_53_1 = "is_damages_claim_under_articles_53_and_53_1"
    # Возмещение убытков, причинённых гражданином как арбитражным управляющим.
    # Требует умысла или грубой неосторожности.
    IS_MANAGER_DAMAGES_CLAIM = "is_manager_damages_claim"
    # Возмещение вреда имуществу. Требует умысла или грубой неосторожности.
    IS_PROPERTY_DAMAGE_CLAIM = "is_property_damage_claim"
    # Применение последствий недействительности сделки, признанной
    # недействительной по статье 61.2 или 61.3. Формы вины пункт 6 здесь не
    # требует.
    IS_AVOIDED_TRANSACTION_CONSEQUENCES_CLAIM = "is_avoided_transaction_consequences_claim"
    # Умысел или грубая неосторожность — условие трёх категорий пункта 6 из пяти.
    CAUSED_INTENTIONALLY_OR_BY_GROSS_NEGLIGENCE = "caused_intentionally_or_by_gross_negligence"

    # --- Абзац второй пункта 3: ещё два изъятия ---
    # О требовании кредиторы не знали и не должны были знать к моменту принятия
    # определения о завершении реализации имущества.
    CREDITORS_DID_NOT_KNOW_AND_SHOULD_NOT_HAVE_KNOWN = (
        "creditors_did_not_know_and_should_not_have_known"
    )
    # В счёт удовлетворения требования заключено утверждённое судом отдельное
    # мировое соглашение по статье 213.10-1.
    SEPARATE_SETTLEMENT_UNDER_ARTICLE_213_10_1_APPROVED = (
        "separate_settlement_under_article_213_10_1_approved"
    )


REQUIRED_CITIZEN_RELEASE_PREDICATES = frozenset(CitizenReleaseEvidencePredicate)

#: Категории требования, исключающие друг друга: одно требование не может быть
#: одновременно алиментным и о субсидиарной ответственности.
_EXCLUSIVE_CLAIM_CATEGORIES = (
    "is_claim_named_in_paragraph_five",
    "is_other_claim_inseparable_from_the_creditors_person",
    "is_subsidiary_liability_claim",
    "is_damages_claim_under_articles_53_and_53_1",
    "is_manager_damages_claim",
    "is_property_damage_claim",
    "is_avoided_transaction_consequences_claim",
)

#: Три категории пункта 6, для которых оговорка о форме вины обязательна.
_FAULT_REQUIRING_CATEGORIES = (
    "is_damages_claim_under_articles_53_and_53_1",
    "is_manager_damages_claim",
    "is_property_damage_claim",
)


class CitizenReleaseEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: CitizenReleaseEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedCitizenReleaseEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CITIZEN_RELEASE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[CitizenReleaseEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedCitizenReleaseEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Citizen-release evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Citizen-release evidence contains duplicate legal source refs.")
        return self


class CitizenReleaseFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    citizen_declared_bankrupt: bool
    property_realisation_completed_by_court_ruling: bool
    held_liable_for_bankruptcy_offence_in_this_case: bool
    withheld_or_falsified_information_established_by_court: bool
    acted_unlawfully_in_the_obligation_relied_on: bool
    claim_filed_in_bankruptcy_register: bool
    is_current_payment_claim: bool
    is_claim_named_in_paragraph_five: bool
    is_other_claim_inseparable_from_the_creditors_person: bool
    is_subsidiary_liability_claim: bool
    is_damages_claim_under_articles_53_and_53_1: bool
    is_manager_damages_claim: bool
    is_property_damage_claim: bool
    is_avoided_transaction_consequences_claim: bool
    caused_intentionally_or_by_gross_negligence: bool
    creditors_did_not_know_and_should_not_have_known: bool
    separate_settlement_under_article_213_10_1_approved: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "CitizenReleaseFactSet":
        bankruptcy_bound = {
            "property_realisation_completed_by_court_ruling": (
                "определение о завершении реализации имущества"
            ),
            "held_liable_for_bankruptcy_offence_in_this_case": (
                "привлечение к ответственности за банкротные правонарушения"
            ),
            "withheld_or_falsified_information_established_by_court": (
                "непредоставление или искажение сведений"
            ),
            "separate_settlement_under_article_213_10_1_approved": (
                "отдельное мировое соглашение по статье 213.10-1"
            ),
        }
        for field_name, label in bankruptcy_bound.items():
            if getattr(self, field_name) and not self.citizen_declared_bankrupt:
                raise ValueError(
                    f"Признак «{label}» относится к делу о банкротстве гражданина, а "
                    "признание банкротом по делу не заявлено: пункты 2–4 статьи 213.28 "
                    "говорят о гражданине, признанном банкротом."
                )
        if self.claim_filed_in_bankruptcy_register and self.is_current_payment_claim:
            raise ValueError(
                "Требование не может быть одновременно реестровым и текущим: требования "
                "по текущим платежам в реестр не включаются (пункт 2 статьи 5 127-ФЗ)."
            )
        if sum(getattr(self, name) for name in _EXCLUSIVE_CLAIM_CATEGORIES) > 1:
            raise ValueError(
                "Требование не может одновременно относиться к нескольким категориям "
                "пунктов 5 и 6 статьи 213.28: они перечислены как разные требования."
            )
        if self.caused_intentionally_or_by_gross_negligence and not any(
            getattr(self, name) for name in _FAULT_REQUIRING_CATEGORIES
        ):
            raise ValueError(
                "Умысел или грубая неосторожность заявлены, а требования, для которого "
                "пункт 6 статьи 213.28 эту форму вины требует, нет: оговорка относится к "
                "убыткам юридическому лицу, убыткам арбитражного управляющего и вреду "
                "имуществу, но не к субсидиарной ответственности и не к последствиям "
                "недействительности сделки."
            )
        if (
            self.creditors_did_not_know_and_should_not_have_known
            and self.claim_filed_in_bankruptcy_register
        ):
            raise ValueError(
                "Требование включено в реестр требований кредиторов, значит кредитор о "
                "нём знал: изъятие абзаца второго пункта 3 статьи 213.28 касается "
                "требований, о которых кредиторы не знали и не должны были знать."
            )
        return self


class CitizenReleaseFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class CitizenReleaseEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: CitizenReleaseFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[CitizenReleaseFactProvenance] = Field(default_factory=list)


class CitizenReleaseConstraintSet(BaseModel):
    id: str
    model_version: str = CITIZEN_RELEASE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class CitizenReleaseEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    #: Гражданин освобождён от дальнейшего исполнения требований (пункт 3).
    citizen_released_from_obligations: bool
    #: Освобождение не допускается: банкротное правонарушение в данном деле (пункт 4).
    release_barred_by_bankruptcy_offence: bool
    #: Освобождение не допускается: сведения не предоставлены либо искажены (пункт 4).
    release_barred_by_withheld_information: bool
    #: Освобождение не допускается: незаконное поведение в обязательстве (пункт 4).
    release_barred_by_unlawful_conduct_in_the_obligation: bool
    #: Правило об освобождении не применяется вовсе — уровень должника (пункт 4).
    release_not_applied_at_all: bool
    #: Требование сохраняет силу как неразрывно связанное с личностью кредитора
    #: либо как текущий платёж (пункт 5).
    claim_survives_as_personally_bound: bool
    #: Требование сохраняет силу по пункту 6.
    claim_survives_under_paragraph_six: bool
    #: Требование сохраняет силу: кредиторы о нём не знали (абзац 2 пункта 3).
    claim_survives_as_unknown_to_creditors: bool
    #: Требование сохраняет силу: заключено отдельное мировое соглашение
    #: по статье 213.10-1 (абзац 2 пункта 3).
    claim_survives_under_separate_settlement: bool
    #: Требование погашено освобождением: оно состоялось и этого требования достигло.
    claim_discharged: bool
    #: На сохранившее силу реестровое требование выдаётся исполнительный лист
    #: (абзац 2 пункта 5).
    writ_of_execution_issued_for_the_surviving_registered_claim: bool
    #: Случай, предусмотренный законом, при котором требование погашенным не
    #: считается, — то исключение, о котором говорит пункт 6 статьи 213.27.
    discharge_exception_applies_to_this_claim: bool
    requires_human_citizen_release_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_citizen_release_evidence(
    evidence: ReviewedCitizenReleaseEvidence,
) -> CitizenReleaseEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Citizen-release evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Citizen-release evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_CITIZEN_RELEASE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed citizen-release evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_CITIZEN_RELEASE_PREDICATES
    }
    return CitizenReleaseEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CITIZEN_RELEASE_MAPPING_VERSION,
        facts=CitizenReleaseFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            CitizenReleaseFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_CITIZEN_RELEASE_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_citizen_release_constraint_set(
    mapping: CitizenReleaseEvidenceMappingResult,
) -> CitizenReleaseConstraintSet:
    return CitizenReleaseConstraintSet(
        id=f"citizen-release-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            (
                "release_barred_by_bankruptcy_offence == citizen_declared_bankrupt AND "
                "property_realisation_completed_by_court_ruling AND "
                "held_liable_for_bankruptcy_offence_in_this_case"
            ),
            (
                "release_barred_by_withheld_information == citizen_declared_bankrupt AND "
                "property_realisation_completed_by_court_ruling AND "
                "withheld_or_falsified_information_established_by_court"
            ),
            (
                "release_barred_by_unlawful_conduct_in_the_obligation == "
                "citizen_declared_bankrupt AND "
                "property_realisation_completed_by_court_ruling AND "
                "acted_unlawfully_in_the_obligation_relied_on"
            ),
            (
                "release_not_applied_at_all == release_barred_by_bankruptcy_offence OR "
                "release_barred_by_withheld_information OR "
                "release_barred_by_unlawful_conduct_in_the_obligation"
            ),
            (
                "citizen_released_from_obligations == citizen_declared_bankrupt AND "
                "property_realisation_completed_by_court_ruling AND "
                "NOT release_not_applied_at_all"
            ),
            (
                "claim_survives_as_personally_bound == citizen_declared_bankrupt AND "
                "property_realisation_completed_by_court_ruling AND "
                "(is_current_payment_claim OR is_claim_named_in_paragraph_five OR "
                "is_other_claim_inseparable_from_the_creditors_person)"
            ),
            (
                "claim_survives_under_paragraph_six == citizen_declared_bankrupt AND "
                "property_realisation_completed_by_court_ruling AND "
                "(is_subsidiary_liability_claim OR "
                "is_avoided_transaction_consequences_claim OR "
                "((is_damages_claim_under_articles_53_and_53_1 OR is_manager_damages_claim "
                "OR is_property_damage_claim) AND "
                "caused_intentionally_or_by_gross_negligence))"
            ),
            (
                "claim_survives_as_unknown_to_creditors == citizen_declared_bankrupt AND "
                "property_realisation_completed_by_court_ruling AND "
                "creditors_did_not_know_and_should_not_have_known"
            ),
            (
                "claim_survives_under_separate_settlement == citizen_declared_bankrupt AND "
                "property_realisation_completed_by_court_ruling AND "
                "separate_settlement_under_article_213_10_1_approved"
            ),
            (
                "claim_discharged == citizen_released_from_obligations AND "
                "NOT claim_survives_as_personally_bound AND "
                "NOT claim_survives_under_paragraph_six AND "
                "NOT claim_survives_as_unknown_to_creditors AND "
                "NOT claim_survives_under_separate_settlement"
            ),
            (
                "writ_of_execution_issued_for_the_surviving_registered_claim == "
                "claim_filed_in_bankruptcy_register AND "
                "(claim_survives_as_personally_bound OR claim_survives_under_paragraph_six)"
            ),
            (
                "discharge_exception_applies_to_this_claim == release_not_applied_at_all OR "
                "claim_survives_as_personally_bound OR claim_survives_under_paragraph_six OR "
                "claim_survives_as_unknown_to_creditors OR "
                "claim_survives_under_separate_settlement"
            ),
            (
                "requires_human_citizen_release_assessment == "
                "release_barred_by_unlawful_conduct_in_the_obligation OR "
                "(claim_survives_as_personally_bound AND "
                "is_other_claim_inseparable_from_the_creditors_person) OR "
                "claim_survives_as_unknown_to_creditors OR "
                "(claim_survives_under_paragraph_six AND "
                "caused_intentionally_or_by_gross_negligence)"
            ),
        ],
    )


def evaluate_citizen_release_constraints(
    constraint_set: CitizenReleaseConstraintSet,
    facts: CitizenReleaseFactSet,
) -> CitizenReleaseEvaluation:
    variables = {field_name: Bool(field_name) for field_name in CitizenReleaseFactSet.model_fields}
    citizen_released_from_obligations = Bool("citizen_released_from_obligations")
    release_barred_by_bankruptcy_offence = Bool("release_barred_by_bankruptcy_offence")
    release_barred_by_withheld_information = Bool("release_barred_by_withheld_information")
    release_barred_by_unlawful_conduct_in_the_obligation = Bool(
        "release_barred_by_unlawful_conduct_in_the_obligation"
    )
    release_not_applied_at_all = Bool("release_not_applied_at_all")
    claim_survives_as_personally_bound = Bool("claim_survives_as_personally_bound")
    claim_survives_under_paragraph_six = Bool("claim_survives_under_paragraph_six")
    claim_survives_as_unknown_to_creditors = Bool("claim_survives_as_unknown_to_creditors")
    claim_survives_under_separate_settlement = Bool("claim_survives_under_separate_settlement")
    claim_discharged = Bool("claim_discharged")
    writ_of_execution_issued_for_the_surviving_registered_claim = Bool(
        "writ_of_execution_issued_for_the_surviving_registered_claim"
    )
    discharge_exception_applies_to_this_claim = Bool("discharge_exception_applies_to_this_claim")
    requires_human_citizen_release_assessment = Bool("requires_human_citizen_release_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    # Вопрос об освобождении возникает только после определения о завершении
    # реализации имущества (пункт 2): до него освобождать не от чего.
    release_question = And(
        variables["citizen_declared_bankrupt"],
        variables["property_realisation_completed_by_court_ruling"],
    )

    # Пункт 4 — уровень должника: три основания недопустимости освобождения.
    solver.add(
        release_barred_by_bankruptcy_offence
        == And(release_question, variables["held_liable_for_bankruptcy_offence_in_this_case"])
    )
    solver.add(
        release_barred_by_withheld_information
        == And(
            release_question,
            variables["withheld_or_falsified_information_established_by_court"],
        )
    )
    solver.add(
        release_barred_by_unlawful_conduct_in_the_obligation
        == And(release_question, variables["acted_unlawfully_in_the_obligation_relied_on"])
    )
    solver.add(
        release_not_applied_at_all
        == Or(
            release_barred_by_bankruptcy_offence,
            release_barred_by_withheld_information,
            release_barred_by_unlawful_conduct_in_the_obligation,
        )
    )
    solver.add(
        citizen_released_from_obligations == And(release_question, Not(release_not_applied_at_all))
    )

    # Пункты 5 и 6 — уровень требования: освобождение состоялось, но этого
    # требования не достигает. Поэтому они не зависят от оснований пункта 4.
    solver.add(
        claim_survives_as_personally_bound
        == And(
            release_question,
            Or(
                variables["is_current_payment_claim"],
                variables["is_claim_named_in_paragraph_five"],
                variables["is_other_claim_inseparable_from_the_creditors_person"],
            ),
        )
    )
    # Оговорка «умышленно или по грубой неосторожности» относится к трём
    # категориям пункта 6 из пяти. Распространить её на субсидиарную
    # ответственность или на последствия недействительности сделки значило бы
    # освободить гражданина от них при недоказанной форме вины.
    solver.add(
        claim_survives_under_paragraph_six
        == And(
            release_question,
            Or(
                variables["is_subsidiary_liability_claim"],
                variables["is_avoided_transaction_consequences_claim"],
                And(
                    Or(
                        variables["is_damages_claim_under_articles_53_and_53_1"],
                        variables["is_manager_damages_claim"],
                        variables["is_property_damage_claim"],
                    ),
                    variables["caused_intentionally_or_by_gross_negligence"],
                ),
            ),
        )
    )
    # Абзац второй пункта 3: ещё два изъятия того же уровня.
    solver.add(
        claim_survives_as_unknown_to_creditors
        == And(release_question, variables["creditors_did_not_know_and_should_not_have_known"])
    )
    solver.add(
        claim_survives_under_separate_settlement
        == And(
            release_question,
            variables["separate_settlement_under_article_213_10_1_approved"],
        )
    )
    survives = Or(
        claim_survives_as_personally_bound,
        claim_survives_under_paragraph_six,
        claim_survives_as_unknown_to_creditors,
        claim_survives_under_separate_settlement,
    )
    solver.add(claim_discharged == And(citizen_released_from_obligations, Not(survives)))
    # Абзац второй пункта 5: исполнительные листы — на реестровые требования,
    # сохранившие силу. Через отсылку пункта 6 правило достаёт и его категории.
    solver.add(
        writ_of_execution_issued_for_the_surviving_registered_claim
        == And(
            variables["claim_filed_in_bankruptcy_register"],
            Or(claim_survives_as_personally_bound, claim_survives_under_paragraph_six),
        )
    )
    # Тот самый случай, о котором говорит пункт 6 статьи 213.27: требование не
    # считается погашенным, потому что так предусмотрено этим законом.
    solver.add(
        discharge_exception_applies_to_this_claim == Or(release_not_applied_at_all, survives)
    )
    solver.add(
        requires_human_citizen_release_assessment
        == Or(
            release_barred_by_unlawful_conduct_in_the_obligation,
            And(
                claim_survives_as_personally_bound,
                variables["is_other_claim_inseparable_from_the_creditors_person"],
            ),
            claim_survives_as_unknown_to_creditors,
            And(
                claim_survives_under_paragraph_six,
                variables["caused_intentionally_or_by_gross_negligence"],
            ),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return CitizenReleaseEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            citizen_released_from_obligations=False,
            release_barred_by_bankruptcy_offence=False,
            release_barred_by_withheld_information=False,
            release_barred_by_unlawful_conduct_in_the_obligation=False,
            release_not_applied_at_all=False,
            claim_survives_as_personally_bound=False,
            claim_survives_under_paragraph_six=False,
            claim_survives_as_unknown_to_creditors=False,
            claim_survives_under_separate_settlement=False,
            claim_discharged=False,
            writ_of_execution_issued_for_the_surviving_registered_claim=False,
            discharge_exception_applies_to_this_claim=False,
            requires_human_citizen_release_assessment=True,
            reasons_ru=["Набор фактов об освобождении гражданина от обязательств противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru: list[str] = []
    if truth(citizen_released_from_obligations):
        reasons_ru.append(
            "После завершения расчётов с кредиторами гражданин, признанный банкротом, "
            "освобождается от дальнейшего исполнения требований кредиторов, в том числе "
            "не заявленных при введении реструктуризации долгов или реализации "
            "имущества (пункт 3 статьи 213.28 закона 127-ФЗ)."
        )
    if truth(release_barred_by_bankruptcy_offence):
        reasons_ru.append(
            "Освобождение от обязательств не допускается: вступившим в законную силу "
            "судебным актом гражданин привлечён к ответственности за неправомерные "
            "действия при банкротстве, преднамеренное или фиктивное банкротство, и "
            "правонарушения совершены в данном деле (пункт 4 статьи 213.28 закона). "
            "Оговорка о «данном деле» существенна: прошлое банкротное правонарушение "
            "основанием не является."
        )
    if truth(release_barred_by_withheld_information):
        reasons_ru.append(
            "Освобождение от обязательств не допускается: гражданин не предоставил "
            "необходимые сведения либо предоставил заведомо недостоверные финансовому "
            "управляющему или суду, и это установлено судебным актом по данному делу "
            "(пункт 4 статьи 213.28 закона)."
        )
    if truth(release_barred_by_unlawful_conduct_in_the_obligation):
        reasons_ru.append(
            "Освобождение от обязательств не допускается: доказано, что при "
            "возникновении или исполнении обязательства, на котором кредитор основал "
            "требование, гражданин действовал незаконно — мошенничество, злостное "
            "уклонение от погашения задолженности, уклонение от уплаты налогов, "
            "заведомо ложные сведения при получении кредита, сокрытие или умышленное "
            "уничтожение имущества (пункт 4 статьи 213.28 закона). Доказанность "
            "незаконного поведения устанавливает суд, а не модель."
        )
    if truth(release_not_applied_at_all):
        reasons_ru.append(
            "Правило об освобождении от исполнения обязательств не применяется к "
            "гражданину вовсе: он не освобождается ни от одного требования. Суд "
            "указывает на это в определении о завершении реализации имущества либо "
            "выносит отдельное определение, если основание выявлено позже (пункт 4 "
            "статьи 213.28 закона)."
        )
    if truth(claim_survives_as_personally_bound):
        if truth(variables["is_current_payment_claim"]):
            ground = "требование по текущим платежам"
        elif truth(variables["is_claim_named_in_paragraph_five"]):
            ground = (
                "требование о возмещении вреда жизни или здоровью, о выплате заработной "
                "платы или выходного пособия, о возмещении морального вреда либо о "
                "взыскании алиментов"
            )
        else:
            ground = "иное требование, неразрывно связанное с личностью кредитора"
        reasons_ru.append(
            f"Требование сохраняет силу и может быть предъявлено после окончания "
            f"производства по делу в непогашенной части: {ground} (пункт 5 статьи "
            "213.28 закона). Освобождение гражданина от обязательств его не достигает."
        )
    if truth(claim_survives_under_paragraph_six):
        if truth(variables["is_subsidiary_liability_claim"]):
            ground = (
                "привлечение гражданина как контролирующего лица к субсидиарной "
                "ответственности (глава III.2 закона); формы вины пункт 6 здесь не "
                "требует"
            )
        elif truth(variables["is_avoided_transaction_consequences_claim"]):
            ground = (
                "применение последствий недействительности сделки, признанной "
                "недействительной по статье 61.2 или 61.3 закона; формы вины пункт 6 "
                "здесь не требует"
            )
        elif truth(variables["is_damages_claim_under_articles_53_and_53_1"]):
            ground = (
                "возмещение убытков, причинённых юридическому лицу, участником или "
                "членом коллегиальных органов которого был гражданин (статьи 53 и 53.1 "
                "ГК РФ), умышленно или по грубой неосторожности"
            )
        elif truth(variables["is_manager_damages_claim"]):
            ground = (
                "возмещение убытков, причинённых гражданином как арбитражным "
                "управляющим умышленно или по грубой неосторожности"
            )
        else:
            ground = (
                "возмещение вреда имуществу, причинённого умышленно или по грубой неосторожности"
            )
        reasons_ru.append(
            f"Требование сохраняет силу по правилу пункта 5, распространённому пунктом "
            f"6 статьи 213.28 закона: {ground}."
        )
    if truth(claim_survives_as_unknown_to_creditors):
        reasons_ru.append(
            "Требование сохраняет силу: кредиторы о нём не знали и не должны были знать "
            "к моменту принятия определения о завершении реализации имущества (абзац "
            "второй пункта 3 статьи 213.28 закона). Что кредитор не должен был знать, "
            "устанавливает суд."
        )
    if truth(claim_survives_under_separate_settlement):
        reasons_ru.append(
            "Требование сохраняет силу: в целях его удовлетворения гражданином "
            "заключено утверждённое арбитражным судом отдельное мировое соглашение по "
            "статье 213.10-1 закона (абзац второй пункта 3 статьи 213.28)."
        )
    if truth(claim_discharged):
        reasons_ru.append(
            "Требование погашено освобождением гражданина от обязательств: ни одно из "
            "изъятий пунктов 3–6 статьи 213.28 закона к нему не относится."
        )
    if truth(writ_of_execution_issued_for_the_surviving_registered_claim):
        reasons_ru.append(
            "На сохранившее силу требование, включённое в реестр требований кредиторов, "
            "арбитражный суд выдаёт исполнительный лист в непогашенной части (абзац "
            "второй пункта 5 статьи 213.28 закона)."
        )
    if truth(requires_human_citizen_release_assessment):
        reasons_ru.append(
            "Требуется оценка юриста. Доказанность незаконного поведения гражданина "
            "(пункт 4), неразрывную связь требования с личностью кредитора (пункт 5), "
            "незнание кредитора о требовании (абзац второй пункта 3) и форму вины — "
            "умысел либо грубую неосторожность (пункт 6) — устанавливает суд, а не "
            "модель."
        )
    return CitizenReleaseEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        citizen_released_from_obligations=truth(citizen_released_from_obligations),
        release_barred_by_bankruptcy_offence=truth(release_barred_by_bankruptcy_offence),
        release_barred_by_withheld_information=truth(release_barred_by_withheld_information),
        release_barred_by_unlawful_conduct_in_the_obligation=truth(
            release_barred_by_unlawful_conduct_in_the_obligation
        ),
        release_not_applied_at_all=truth(release_not_applied_at_all),
        claim_survives_as_personally_bound=truth(claim_survives_as_personally_bound),
        claim_survives_under_paragraph_six=truth(claim_survives_under_paragraph_six),
        claim_survives_as_unknown_to_creditors=truth(claim_survives_as_unknown_to_creditors),
        claim_survives_under_separate_settlement=truth(claim_survives_under_separate_settlement),
        claim_discharged=truth(claim_discharged),
        writ_of_execution_issued_for_the_surviving_registered_claim=truth(
            writ_of_execution_issued_for_the_surviving_registered_claim
        ),
        discharge_exception_applies_to_this_claim=truth(discharge_exception_applies_to_this_claim),
        requires_human_citizen_release_assessment=truth(requires_human_citizen_release_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель отвечает, достигает ли освобождение этого требования, а не каков "
            "его размер: статья говорит о предъявлении требования в непогашенной части, "
            "а не об её исчислении.",
            "Процедуру отчёта финансового управляющего и его рассмотрения (пункты 1 и "
            "2) модель не разбирает: определение о завершении реализации имущества "
            "принимается как проверенный факт.",
            "Субсидиарная ответственность (глава III.2), ответственность арбитражного "
            "управляющего и оспаривание сделок по статьям 61.2 и 61.3 названы пунктом 6 "
            "как категории требований и в пакете не смоделированы.",
            "Пункт 6 называет статьи 53 и 53.1 ГК РФ, и модель ответственности "
            "управляющих лиц в пакете есть, но связи между ними нет сознательно: та "
            "статья отвечает, возникла ли ответственность, а эта — достигает ли "
            "освобождение требования о ней, и формы вины у них разные — "
            "недобросовестность и неразумность против умысла и грубой неосторожности.",
        ],
    )
