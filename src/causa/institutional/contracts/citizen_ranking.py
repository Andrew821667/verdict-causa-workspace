"""Формальная модель очерёдности удовлетворения требований кредиторов гражданина.

Статья 213.27 закона 127-ФЗ целиком: шесть пунктов.

**Почему институт появился.** Выпуск 1.25.0 закрыл статью 25 ГК РФ и вместе с
ней загатил институт очерёдности статьи 134: для должника-гражданина очереди
конкурсного производства снимались, потому что статья 213.27 вытесняет их по
существу. Но снять ответ — не то же самое, что ответить. Требование гражданина
получало «очередь не определена» и флаг юриста, и это было честно, но пусто.
Институт превращает названное правило в применённое.

**Что именно вытесняется.** Расхождение статей 134 и 213.27 — не редакционное, и
именно оно было измеренным дефектом:

| Требование | Статья 134 (конкурсное производство) | Статья 213.27 (гражданин) |
|---|---|---|
| взыскание алиментов (реестровое) | категории нет → третья очередь | **первая** очередь (пункт 3) |
| вознаграждение автору | вторая очередь | категории нет → третья |
| плата за жилое помещение и ЖКУ | эксплуатационные, четвёртая очередь текущих | отдельная **третья** очередь текущих (пункт 2) |
| капитализация повременных платежей | производится (статья 135) | **не производится** (пункт 4) |
| очередей текущих платежей | пять (пункт 2 статьи 134) | **четыре** (пункт 2) |

Поэтому институт не переиспользует предикаты статьи 134, а вводит свои:
`is_maintenance_claim` — категория, которой у статьи 134 нет вовсе, а
`is_wage_severance_or_authorship_claim` статьи 134 распадается здесь на
`is_labour_or_severance_claim` без авторского вознаграждения, которого пункт 3
не называет.

## Пункт 1: текущие платежи идут вне очереди

«Вне очереди за счет конкурсной массы погашаются требования кредиторов по
текущим платежам преимущественно перед кредиторами, требования которых возникли
до принятия заявления о признании должника банкротом.»

Два порядка не сообщаются между собой: текущий платёж не встаёт ни в одну из
трёх реестровых очередей, а реестровое требование не получает ни одной из
четырёх очередей текущих. Контракт фактов запрещает быть тем и другим сразу
(пункт 2 статьи 5 закона).

## Пункт 2: четыре очереди текущих платежей

Первая — алименты, судебные расходы по делу о банкротстве гражданина,
вознаграждение финансовому управляющему и привлечённым им лицам. Вторая —
выходные пособия и оплата труда. Третья — плата за жилое помещение и
коммунальные услуги, включая взнос на капитальный ремонт. Четвёртая — иные
текущие платежи.

Четвёртая очередь остаточная, и как всякая остаточная категория в этом пакете
она загачена: без ворот любое требование без единого признака попадало бы в неё.

## Пункт 3: три очереди реестра

Первая — требования граждан за причинение вреда жизни или здоровью **и
требования о взыскании алиментов**. Вторая — выходные пособия и оплата труда.
Третья — расчёты с другими кредиторами.

Алименты в первой очереди вместе с вредом жизни и здоровью — то самое место, где
статья 134 отвечала неверно, а не неполно.

## Пункт 4: капитализация не производится

«При удовлетворении требований граждан, перед которыми гражданин несет
ответственность за причинение вреда жизни или здоровью, капитализация
повременных платежей не производится.»

Вывод назван прямо, хотя следует из отрицания: для юридического лица статья 135
капитализацию предписывает, и перенос этого правила на гражданина был бы ошибкой
в пользу кредитора первой очереди за счёт остальных.

## Пункт 5: залог — восемьдесят процентов, но не всё

Восемьдесят процентов выручки от реализации предмета залога идут залоговому
кредитору. Из остатка десять процентов — на требования первой и второй очереди,
**если иного имущества гражданина для них недостаточно**; оставшееся — на
судебные расходы, вознаграждение управляющего и привлечённых им лиц.
Непогашенная из стоимости предмета залога часть требования удовлетворяется в
составе **третьей** очереди.

Модель выводит три следствия — долю залогового кредитора, условный резерв для
первой и второй очереди и переход непогашенного остатка в третью очередь — и
останавливается. Движение денег по специальному счёту, возврат остатков в
конкурсную массу и расходы пункта 6 статьи 138 — распределение, а не
квалификация требования.

## Пункт 6: погашение за недостаточностью имущества

«Требования кредиторов, не удовлетворенные по причине недостаточности имущества
гражданина, считаются погашенными, за исключением случаев, предусмотренных
настоящим Федеральным законом.»

Исключения перечисляет не эта статья, а статья 213.28 (пункты 4–6) и соседние.
Их содержание пакет не моделирует, поэтому заявленное исключение снимает вывод о
погашении и поднимает флаг юриста, а не подменяется догадкой.

## Чего модель не делает

* **Не считает суммы и доли.** Восемьдесят и десять процентов названы как
  правила, а не вычислены: денежных величин в фактах модели нет.
* **Не упорядочивает требования внутри одной очереди.** Пункт 2 устанавливает
  календарный порядок, а дат в фактах модели нет — то же ограничение, что у
  института статьи 134.
* **Не перечисляет исключения из погашения** (статья 213.28): называет
  исключение заявленным и останавливается.
* **Не разбирает процедуры** дела о банкротстве гражданина (статья 213.2) и не
  решает вопрос об освобождении гражданина от обязательств (статья 213.28).
* **Отвечает об одном требовании:** контракт данных даёт один блок доказательств
  на институт.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

CITIZEN_RANKING_EVIDENCE_SCHEMA_VERSION = "contracts.citizen-ranking-evidence.v0"
CITIZEN_RANKING_MAPPING_VERSION = "contracts-reviewed-citizen-ranking-to-facts-v0"
CITIZEN_RANKING_MODEL_VERSION = "contracts-citizen-ranking-article-213-27-127fz-v0"

# Дословный текст статьи 213.27 закона 127-ФЗ — synthetic_sources.py,
# synthetic-ru-127fz-213.27-citizen-creditor-ranking-v1. Статья 213.1 отвечает,
# к какому должнику эта очерёдность применяется; статья 134 — та очерёдность,
# которую она для гражданина вытесняет; статья 25 ГК РФ — вход в режим.
CITIZEN_RANKING_LEGAL_SOURCE_REFS = (
    "synthetic-ru-127fz-213.27-citizen-creditor-ranking-v1",
    "synthetic-ru-127fz-213.1-citizen-bankruptcy-regulation-v1",
    "synthetic-ru-127fz-134-creditor-ranking-v1",
    "synthetic-ru-gk25-citizen-insolvency-v1",
)


class CitizenRankingEvidencePredicate(str, Enum):
    # --- Режим: тот же признак, что у института очерёдности статьи 134 ---
    # Должник — гражданин, и к отношениям применяется глава X закона. Без этого
    # признака институт молчит целиком: очерёдность статьи 213.27 существует
    # только внутри режима главы X.
    DEBTOR_IS_A_CITIZEN_UNDER_CHAPTER_10 = "debtor_is_a_citizen_under_chapter_10"

    # --- Два несообщающихся порядка: пункт 1 ---
    # Требование включено в реестр требований кредиторов (пункт 3).
    CLAIM_FILED_IN_BANKRUPTCY_REGISTER = "claim_filed_in_bankruptcy_register"
    # Требование по текущим платежам (пункты 1 и 2).
    IS_CURRENT_PAYMENT_CLAIM = "is_current_payment_claim"

    # --- Категории требования ---
    # Вред жизни или здоровью: первая очередь реестра (пункт 3).
    IS_LIFE_OR_HEALTH_HARM_CLAIM = "is_life_or_health_harm_claim"
    # Взыскание алиментов: первая очередь реестра (пункт 3) и первая очередь
    # текущих платежей (пункт 2). Категории, которой у статьи 134 нет вовсе.
    IS_MAINTENANCE_CLAIM = "is_maintenance_claim"
    # Выходные пособия и оплата труда: вторая очередь обоих порядков. Без
    # вознаграждения авторам — пункт 3 его не называет, в отличие от статьи 134.
    IS_LABOUR_OR_SEVERANCE_CLAIM = "is_labour_or_severance_claim"
    # Судебные расходы по делу о банкротстве гражданина, вознаграждение
    # финансовому управляющему и привлечённым им лицам: первая очередь текущих
    # платежей наряду с алиментами (пункт 2).
    IS_PROCEEDING_COST_OR_MANAGER_FEE = "is_proceeding_cost_or_manager_fee"
    # Плата за жилое помещение и коммунальные услуги, включая взнос на
    # капитальный ремонт: отдельная третья очередь текущих платежей (пункт 2).
    IS_HOUSING_OR_UTILITY_PAYMENT = "is_housing_or_utility_payment"
    # Обеспечено залогом имущества гражданина: отдельный трек пункта 5.
    IS_SECURED_BY_PLEDGE = "is_secured_by_pledge"

    # --- Условия пункта 5 ---
    # Стоимости предмета залога на требование не хватило.
    PLEDGE_PROCEEDS_INSUFFICIENT_FOR_THE_SECURED_CLAIM = (
        "pledge_proceeds_insufficient_for_the_secured_claim"
    )
    # Иного имущества гражданина недостаточно для погашения требований первой и
    # второй очереди — условие резерва десяти процентов (пункт 5).
    OTHER_PROPERTY_INSUFFICIENT_FOR_FIRST_AND_SECOND_TIERS = (
        "other_property_insufficient_for_first_and_second_tiers"
    )

    # --- Пункт 6 ---
    # Требование не удовлетворено по причине недостаточности имущества гражданина.
    CLAIM_UNSATISFIED_FOR_WANT_OF_PROPERTY = "claim_unsatisfied_for_want_of_property"
    # Случай, предусмотренный законом, при котором требование погашенным не
    # считается. Перечень даёт статья 213.28, и его модель не разбирает.
    STATUTORY_EXCEPTION_TO_DISCHARGE_APPLIES = "statutory_exception_to_discharge_applies"


REQUIRED_CITIZEN_RANKING_PREDICATES = frozenset(CitizenRankingEvidencePredicate)


class CitizenRankingEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: CitizenRankingEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedCitizenRankingEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CITIZEN_RANKING_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[CitizenRankingEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedCitizenRankingEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Citizen-ranking evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Citizen-ranking evidence contains duplicate legal source refs.")
        return self


class CitizenRankingFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    debtor_is_a_citizen_under_chapter_10: bool
    claim_filed_in_bankruptcy_register: bool
    is_current_payment_claim: bool
    is_life_or_health_harm_claim: bool
    is_maintenance_claim: bool
    is_labour_or_severance_claim: bool
    is_proceeding_cost_or_manager_fee: bool
    is_housing_or_utility_payment: bool
    is_secured_by_pledge: bool
    pledge_proceeds_insufficient_for_the_secured_claim: bool
    other_property_insufficient_for_first_and_second_tiers: bool
    claim_unsatisfied_for_want_of_property: bool
    statutory_exception_to_discharge_applies: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "CitizenRankingFactSet":
        if self.claim_filed_in_bankruptcy_register and self.is_current_payment_claim:
            raise ValueError(
                "Требование не может быть одновременно реестровым и текущим: требования "
                "по текущим платежам в реестр не включаются (пункт 2 статьи 5 127-ФЗ), а "
                "пункт 1 статьи 213.27 разводит два порядка удовлетворения."
            )
        categories = (
            self.is_life_or_health_harm_claim,
            self.is_maintenance_claim,
            self.is_labour_or_severance_claim,
            self.is_proceeding_cost_or_manager_fee,
            self.is_housing_or_utility_payment,
            self.is_secured_by_pledge,
        )
        if sum(categories) > 1:
            raise ValueError(
                "Требование не может одновременно относиться к нескольким категориям "
                "статьи 213.27: очереди пунктов 2 и 3 перечислены как взаимно "
                "исключающие, а трек залога пункта 5 идёт отдельно от них."
            )
        claim_present = self.claim_filed_in_bankruptcy_register or self.is_current_payment_claim
        if any(categories) and not claim_present:
            raise ValueError(
                "Категория требования названа, а само требование ни реестровым, ни "
                "текущим не заявлено: очерёдность определяется для требования в деле о "
                "банкротстве, а не вообще."
            )
        if self.is_proceeding_cost_or_manager_fee and not self.is_current_payment_claim:
            raise ValueError(
                "Судебные расходы по делу о банкротстве и вознаграждение финансового "
                "управляющего — текущие платежи по своей природе: пункт 2 статьи 213.27 "
                "относит их к первой очереди текущих, и реестровой очереди у них нет."
            )
        if self.is_secured_by_pledge and not self.claim_filed_in_bankruptcy_register:
            raise ValueError(
                "Трек залога пункта 5 статьи 213.27 определён для требования, "
                "включённого в реестр требований кредиторов."
            )
        for field_name, label in (
            (
                "pledge_proceeds_insufficient_for_the_secured_claim",
                "недостаточность стоимости предмета залога",
            ),
            (
                "other_property_insufficient_for_first_and_second_tiers",
                "недостаточность иного имущества для первой и второй очереди",
            ),
        ):
            if getattr(self, field_name) and not self.is_secured_by_pledge:
                raise ValueError(
                    f"Признак «{label}» относится к распределению выручки от реализации "
                    "предмета залога (пункт 5 статьи 213.27) и без залога беспредметен."
                )
        if self.statutory_exception_to_discharge_applies and not (
            self.claim_unsatisfied_for_want_of_property
        ):
            raise ValueError(
                "Исключение из погашения заявлено, а требование не названо "
                "неудовлетворённым за недостаточностью имущества: пункт 6 статьи 213.27 "
                "делает исключение из погашения, а не из самого требования."
            )
        if self.claim_unsatisfied_for_want_of_property and not claim_present:
            raise ValueError(
                "Неудовлетворённым за недостаточностью имущества может оказаться "
                "требование, заявленное в деле: ни реестровым, ни текущим оно здесь не "
                "названо."
            )
        return self


class CitizenRankingFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class CitizenRankingEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: CitizenRankingFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[CitizenRankingFactProvenance] = Field(default_factory=list)


class CitizenRankingConstraintSet(BaseModel):
    id: str
    model_version: str = CITIZEN_RANKING_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class CitizenRankingEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    #: Текущие платежи погашаются вне очереди, преимущественно перед реестром (пункт 1).
    current_payments_paid_ahead_of_registry_claims: bool
    #: Первая очередь текущих: алименты, судебные расходы, вознаграждение
    #: управляющему и привлечённым им лицам (пункт 2).
    current_payment_first_tier: bool
    #: Вторая очередь текущих: выходные пособия и оплата труда (пункт 2).
    current_payment_second_tier: bool
    #: Третья очередь текущих: плата за жилое помещение и ЖКУ (пункт 2).
    current_payment_third_tier: bool
    #: Четвёртая очередь текущих: иные текущие платежи (пункт 2).
    current_payment_fourth_tier: bool
    #: Первая очередь реестра: вред жизни или здоровью и алименты (пункт 3).
    registry_first_tier: bool
    #: Вторая очередь реестра: выходные пособия и оплата труда (пункт 3).
    registry_second_tier: bool
    #: Третья очередь реестра: расчёты с другими кредиторами (пункт 3).
    registry_third_tier: bool
    #: Капитализация повременных платежей не производится (пункт 4).
    capitalisation_not_performed: bool
    #: Восемьдесят процентов выручки от реализации предмета залога — залоговому
    #: кредитору (пункт 5).
    secured_claim_takes_eighty_percent_of_pledge_proceeds: bool
    #: Десять процентов выручки резервируются на первую и вторую очередь при
    #: недостаточности иного имущества (пункт 5).
    pledge_remainder_reserved_for_first_and_second_tiers: bool
    #: Непогашенная из стоимости предмета залога часть требования идёт в третью
    #: очередь (пункт 5).
    unsecured_remainder_of_the_pledge_claim_joins_the_third_tier: bool
    #: Требование считается погашенным за недостаточностью имущества (пункт 6).
    claim_deemed_discharged_for_want_of_property: bool
    #: Погашение не наступает: заявлен случай, предусмотренный законом (пункт 6).
    discharge_withheld_by_statutory_exception: bool
    requires_human_citizen_ranking_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_citizen_ranking_evidence(
    evidence: ReviewedCitizenRankingEvidence,
) -> CitizenRankingEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Citizen-ranking evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Citizen-ranking evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_CITIZEN_RANKING_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed citizen-ranking evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_CITIZEN_RANKING_PREDICATES
    }
    return CitizenRankingEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CITIZEN_RANKING_MAPPING_VERSION,
        facts=CitizenRankingFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            CitizenRankingFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_CITIZEN_RANKING_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_citizen_ranking_constraint_set(
    mapping: CitizenRankingEvidenceMappingResult,
) -> CitizenRankingConstraintSet:
    return CitizenRankingConstraintSet(
        id=f"citizen-ranking-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            (
                "current_payments_paid_ahead_of_registry_claims == "
                "debtor_is_a_citizen_under_chapter_10 AND is_current_payment_claim"
            ),
            (
                "current_payment_first_tier == debtor_is_a_citizen_under_chapter_10 AND "
                "is_current_payment_claim AND (is_maintenance_claim OR "
                "is_proceeding_cost_or_manager_fee)"
            ),
            (
                "current_payment_second_tier == debtor_is_a_citizen_under_chapter_10 AND "
                "is_current_payment_claim AND is_labour_or_severance_claim"
            ),
            (
                "current_payment_third_tier == debtor_is_a_citizen_under_chapter_10 AND "
                "is_current_payment_claim AND is_housing_or_utility_payment"
            ),
            (
                "current_payment_fourth_tier == debtor_is_a_citizen_under_chapter_10 AND "
                "is_current_payment_claim AND NOT is_maintenance_claim AND "
                "NOT is_proceeding_cost_or_manager_fee AND NOT is_labour_or_severance_claim "
                "AND NOT is_housing_or_utility_payment"
            ),
            (
                "registry_first_tier == debtor_is_a_citizen_under_chapter_10 AND "
                "claim_filed_in_bankruptcy_register AND (is_life_or_health_harm_claim OR "
                "is_maintenance_claim)"
            ),
            (
                "registry_second_tier == debtor_is_a_citizen_under_chapter_10 AND "
                "claim_filed_in_bankruptcy_register AND is_labour_or_severance_claim"
            ),
            (
                "registry_third_tier == debtor_is_a_citizen_under_chapter_10 AND "
                "claim_filed_in_bankruptcy_register AND NOT is_life_or_health_harm_claim AND "
                "NOT is_maintenance_claim AND NOT is_labour_or_severance_claim AND "
                "NOT is_secured_by_pledge"
            ),
            (
                "capitalisation_not_performed == debtor_is_a_citizen_under_chapter_10 AND "
                "claim_filed_in_bankruptcy_register AND is_life_or_health_harm_claim"
            ),
            (
                "secured_claim_takes_eighty_percent_of_pledge_proceeds == "
                "debtor_is_a_citizen_under_chapter_10 AND is_secured_by_pledge"
            ),
            (
                "pledge_remainder_reserved_for_first_and_second_tiers == "
                "debtor_is_a_citizen_under_chapter_10 AND is_secured_by_pledge AND "
                "other_property_insufficient_for_first_and_second_tiers"
            ),
            (
                "unsecured_remainder_of_the_pledge_claim_joins_the_third_tier == "
                "debtor_is_a_citizen_under_chapter_10 AND is_secured_by_pledge AND "
                "pledge_proceeds_insufficient_for_the_secured_claim"
            ),
            (
                "claim_deemed_discharged_for_want_of_property == "
                "debtor_is_a_citizen_under_chapter_10 AND "
                "claim_unsatisfied_for_want_of_property AND "
                "NOT statutory_exception_to_discharge_applies"
            ),
            (
                "discharge_withheld_by_statutory_exception == "
                "debtor_is_a_citizen_under_chapter_10 AND "
                "claim_unsatisfied_for_want_of_property AND "
                "statutory_exception_to_discharge_applies"
            ),
            (
                "requires_human_citizen_ranking_assessment == "
                "discharge_withheld_by_statutory_exception OR "
                "secured_claim_takes_eighty_percent_of_pledge_proceeds"
            ),
        ],
    )


def evaluate_citizen_ranking_constraints(
    constraint_set: CitizenRankingConstraintSet,
    facts: CitizenRankingFactSet,
) -> CitizenRankingEvaluation:
    variables = {field_name: Bool(field_name) for field_name in CitizenRankingFactSet.model_fields}
    current_payments_paid_ahead_of_registry_claims = Bool(
        "current_payments_paid_ahead_of_registry_claims"
    )
    current_payment_first_tier = Bool("current_payment_first_tier")
    current_payment_second_tier = Bool("current_payment_second_tier")
    current_payment_third_tier = Bool("current_payment_third_tier")
    current_payment_fourth_tier = Bool("current_payment_fourth_tier")
    registry_first_tier = Bool("registry_first_tier")
    registry_second_tier = Bool("registry_second_tier")
    registry_third_tier = Bool("registry_third_tier")
    capitalisation_not_performed = Bool("capitalisation_not_performed")
    secured_claim_takes_eighty_percent_of_pledge_proceeds = Bool(
        "secured_claim_takes_eighty_percent_of_pledge_proceeds"
    )
    pledge_remainder_reserved_for_first_and_second_tiers = Bool(
        "pledge_remainder_reserved_for_first_and_second_tiers"
    )
    unsecured_remainder_of_the_pledge_claim_joins_the_third_tier = Bool(
        "unsecured_remainder_of_the_pledge_claim_joins_the_third_tier"
    )
    claim_deemed_discharged_for_want_of_property = Bool(
        "claim_deemed_discharged_for_want_of_property"
    )
    discharge_withheld_by_statutory_exception = Bool("discharge_withheld_by_statutory_exception")
    requires_human_citizen_ranking_assessment = Bool("requires_human_citizen_ranking_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    # Ворота всего института: очерёдность статьи 213.27 существует только внутри
    # режима главы X. Для должника-организации отвечает институт статьи 134, и
    # два института никогда не отвечают об одном требовании одновременно.
    citizen = variables["debtor_is_a_citizen_under_chapter_10"]
    current = And(citizen, variables["is_current_payment_claim"])
    registry = And(citizen, variables["claim_filed_in_bankruptcy_register"])

    solver.add(current_payments_paid_ahead_of_registry_claims == current)
    # Пункт 2, первая очередь: алименты стоят в ней наряду с судебными расходами
    # и вознаграждением управляющего.
    solver.add(
        current_payment_first_tier
        == And(
            current,
            Or(
                variables["is_maintenance_claim"],
                variables["is_proceeding_cost_or_manager_fee"],
            ),
        )
    )
    solver.add(
        current_payment_second_tier == And(current, variables["is_labour_or_severance_claim"])
    )
    # Третья очередь текущих — плата за жилое помещение и ЖКУ. У статьи 134
    # такой очереди нет: там эксплуатационные платежи стоят четвёртыми.
    solver.add(
        current_payment_third_tier == And(current, variables["is_housing_or_utility_payment"])
    )
    # Остаточная категория, и как всякая остаточная — с воротами.
    solver.add(
        current_payment_fourth_tier
        == And(
            current,
            Not(variables["is_maintenance_claim"]),
            Not(variables["is_proceeding_cost_or_manager_fee"]),
            Not(variables["is_labour_or_severance_claim"]),
            Not(variables["is_housing_or_utility_payment"]),
        )
    )
    # Пункт 3, первая очередь: вред жизни или здоровью И алименты. Второе —
    # ровно то, чего нет у пункта 4 статьи 134.
    solver.add(
        registry_first_tier
        == And(
            registry,
            Or(
                variables["is_life_or_health_harm_claim"],
                variables["is_maintenance_claim"],
            ),
        )
    )
    solver.add(registry_second_tier == And(registry, variables["is_labour_or_severance_claim"]))
    solver.add(
        registry_third_tier
        == And(
            registry,
            Not(variables["is_life_or_health_harm_claim"]),
            Not(variables["is_maintenance_claim"]),
            Not(variables["is_labour_or_severance_claim"]),
            Not(variables["is_secured_by_pledge"]),
        )
    )
    # Пункт 4: вывод из отрицания, названный прямо. Для юридического лица статья
    # 135 капитализацию предписывает, и перенос её на гражданина был бы ошибкой.
    solver.add(
        capitalisation_not_performed == And(registry, variables["is_life_or_health_harm_claim"])
    )
    solver.add(
        secured_claim_takes_eighty_percent_of_pledge_proceeds
        == And(citizen, variables["is_secured_by_pledge"])
    )
    solver.add(
        pledge_remainder_reserved_for_first_and_second_tiers
        == And(
            citizen,
            variables["is_secured_by_pledge"],
            variables["other_property_insufficient_for_first_and_second_tiers"],
        )
    )
    solver.add(
        unsecured_remainder_of_the_pledge_claim_joins_the_third_tier
        == And(
            citizen,
            variables["is_secured_by_pledge"],
            variables["pledge_proceeds_insufficient_for_the_secured_claim"],
        )
    )
    solver.add(
        claim_deemed_discharged_for_want_of_property
        == And(
            citizen,
            variables["claim_unsatisfied_for_want_of_property"],
            Not(variables["statutory_exception_to_discharge_applies"]),
        )
    )
    solver.add(
        discharge_withheld_by_statutory_exception
        == And(
            citizen,
            variables["claim_unsatisfied_for_want_of_property"],
            variables["statutory_exception_to_discharge_applies"],
        )
    )
    solver.add(
        requires_human_citizen_ranking_assessment
        == Or(
            discharge_withheld_by_statutory_exception,
            secured_claim_takes_eighty_percent_of_pledge_proceeds,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return CitizenRankingEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            current_payments_paid_ahead_of_registry_claims=False,
            current_payment_first_tier=False,
            current_payment_second_tier=False,
            current_payment_third_tier=False,
            current_payment_fourth_tier=False,
            registry_first_tier=False,
            registry_second_tier=False,
            registry_third_tier=False,
            capitalisation_not_performed=False,
            secured_claim_takes_eighty_percent_of_pledge_proceeds=False,
            pledge_remainder_reserved_for_first_and_second_tiers=False,
            unsecured_remainder_of_the_pledge_claim_joins_the_third_tier=False,
            claim_deemed_discharged_for_want_of_property=False,
            discharge_withheld_by_statutory_exception=False,
            requires_human_citizen_ranking_assessment=True,
            reasons_ru=["Набор фактов об очерёдности требований гражданина противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru: list[str] = []
    if truth(citizen) and not (
        truth(variables["claim_filed_in_bankruptcy_register"])
        or truth(variables["is_current_payment_claim"])
    ):
        # Пустой вывод без объяснения читался бы как «очередь не определена»,
        # тогда как верно другое: очерёдности здесь нет предмета.
        reasons_ru.append(
            "Требование не включено в реестр требований кредиторов и не заявлено как "
            "текущий платёж — очерёдность статьи 213.27 закона 127-ФЗ к нему не "
            "применяется."
        )
    if truth(current_payments_paid_ahead_of_registry_claims):
        reasons_ru.append(
            "Требование по текущим платежам погашается вне очереди за счёт конкурсной "
            "массы, преимущественно перед кредиторами, требования которых возникли до "
            "принятия заявления о признании должника банкротом (пункт 1 статьи 213.27 "
            "закона 127-ФЗ)."
        )
    if truth(current_payment_first_tier):
        ground = (
            "уплата алиментов"
            if truth(variables["is_maintenance_claim"])
            else (
                "судебные расходы по делу о банкротстве гражданина, вознаграждение "
                "финансовому управляющему либо вознаграждение привлечённым им лицам"
            )
        )
        reasons_ru.append(
            f"Первая очередь текущих платежей: {ground} (пункт 2 статьи 213.27 закона)."
        )
    if truth(current_payment_second_tier):
        reasons_ru.append(
            "Вторая очередь текущих платежей: выплата выходных пособий и оплата труда "
            "лиц, работающих или работавших по трудовым договорам (пункт 2 статьи "
            "213.27 закона)."
        )
    if truth(current_payment_third_tier):
        reasons_ru.append(
            "Третья очередь текущих платежей: плата за жилое помещение и коммунальные "
            "услуги, в том числе взнос на капитальный ремонт общего имущества в "
            "многоквартирном доме (пункт 2 статьи 213.27 закона). У очерёдности "
            "конкурсного производства такой очереди нет: пункт 2 статьи 134 относит "
            "эксплуатационные платежи к четвёртой очереди."
        )
    if truth(current_payment_fourth_tier):
        reasons_ru.append(
            "Четвёртая очередь текущих платежей: иные текущие платежи (пункт 2 статьи "
            "213.27 закона)."
        )
    if truth(registry_first_tier):
        ground = (
            "ответственность гражданина за причинение вреда жизни или здоровью"
            if truth(variables["is_life_or_health_harm_claim"])
            else "взыскание алиментов"
        )
        reasons_ru.append(
            f"Первая очередь реестра: {ground} (пункт 3 статьи 213.27 закона). "
            "Требование о взыскании алиментов пункт 3 ставит в первую очередь наравне "
            "с вредом жизни и здоровью, тогда как пункт 4 статьи 134 такой категории "
            "не знает вовсе."
        )
    if truth(registry_second_tier):
        reasons_ru.append(
            "Вторая очередь реестра: расчёты по выплате выходных пособий и оплате труда "
            "лиц, работающих или работавших по трудовому договору (пункт 3 статьи "
            "213.27 закона). Вознаграждения авторам результатов интеллектуальной "
            "деятельности пункт 3 в эту очередь не включает, в отличие от пункта 4 "
            "статьи 134."
        )
    if truth(registry_third_tier):
        reasons_ru.append(
            "Третья очередь реестра: расчёты с другими кредиторами (пункт 3 статьи 213.27 закона)."
        )
    if truth(capitalisation_not_performed):
        reasons_ru.append(
            "Капитализация повременных платежей при удовлетворении требований о "
            "возмещении вреда жизни или здоровью не производится (пункт 4 статьи "
            "213.27 закона). Вывод назван прямо, потому что следует из отрицания: для "
            "юридического лица статья 135 капитализацию предписывает, и перенос того "
            "правила на гражданина был бы ошибкой в пользу кредитора первой очереди за "
            "счёт остальных."
        )
    if truth(secured_claim_takes_eighty_percent_of_pledge_proceeds):
        reasons_ru.append(
            "Восемьдесят процентов суммы, вырученной от реализации предмета залога, "
            "направляются на погашение требования, обеспеченного залогом имущества "
            "должника (пункт 5 статьи 213.27 закона). Остальное распределяется по "
            "правилам того же пункта, и этого распределения модель не считает."
        )
    if truth(pledge_remainder_reserved_for_first_and_second_tiers):
        reasons_ru.append(
            "Десять процентов суммы, вырученной от реализации предмета залога, "
            "резервируются на погашение требований кредиторов первой и второй очереди: "
            "иного имущества гражданина для них недостаточно (пункт 5 статьи 213.27 "
            "закона)."
        )
    if truth(unsecured_remainder_of_the_pledge_claim_joins_the_third_tier):
        reasons_ru.append(
            "Часть требования, не погашенная за счёт стоимости предмета залога, "
            "удовлетворяется в составе требований кредиторов третьей очереди (пункт 5 "
            "статьи 213.27 закона), а не сохраняет залоговый приоритет."
        )
    if truth(claim_deemed_discharged_for_want_of_property):
        reasons_ru.append(
            "Требование, не удовлетворённое по причине недостаточности имущества "
            "гражданина, считается погашенным (пункт 6 статьи 213.27 закона)."
        )
    if truth(discharge_withheld_by_statutory_exception):
        reasons_ru.append(
            "Погашение не наступает: заявлен случай, предусмотренный законом (пункт 6 "
            "статьи 213.27 закона). Перечень таких случаев даёт статья 213.28 и "
            "соседние с ней, и его модель не разбирает — требуется проверка юристом."
        )
    if truth(requires_human_citizen_ranking_assessment):
        reasons_ru.append(
            "Требуется оценка юриста. Исключения из погашения требований (статья "
            "213.28 закона) в пакете не смоделированы; распределение выручки от "
            "реализации предмета залога модель называет правилами, но не считает — "
            "денежных величин в её фактах нет."
        )
    return CitizenRankingEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        current_payments_paid_ahead_of_registry_claims=truth(
            current_payments_paid_ahead_of_registry_claims
        ),
        current_payment_first_tier=truth(current_payment_first_tier),
        current_payment_second_tier=truth(current_payment_second_tier),
        current_payment_third_tier=truth(current_payment_third_tier),
        current_payment_fourth_tier=truth(current_payment_fourth_tier),
        registry_first_tier=truth(registry_first_tier),
        registry_second_tier=truth(registry_second_tier),
        registry_third_tier=truth(registry_third_tier),
        capitalisation_not_performed=truth(capitalisation_not_performed),
        secured_claim_takes_eighty_percent_of_pledge_proceeds=truth(
            secured_claim_takes_eighty_percent_of_pledge_proceeds
        ),
        pledge_remainder_reserved_for_first_and_second_tiers=truth(
            pledge_remainder_reserved_for_first_and_second_tiers
        ),
        unsecured_remainder_of_the_pledge_claim_joins_the_third_tier=truth(
            unsecured_remainder_of_the_pledge_claim_joins_the_third_tier
        ),
        claim_deemed_discharged_for_want_of_property=truth(
            claim_deemed_discharged_for_want_of_property
        ),
        discharge_withheld_by_statutory_exception=truth(discharge_withheld_by_statutory_exception),
        requires_human_citizen_ranking_assessment=truth(requires_human_citizen_ranking_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель определяет очередь требования, а не его размер: восемьдесят и "
            "десять процентов пункта 5 названы как правила, но не вычислены — денежных "
            "величин в фактах модели нет.",
            "Календарный порядок внутри одной очереди текущих платежей (пункт 2) "
            "остаётся вне модели: дат в её фактах нет. То же ограничение у института "
            "очерёдности статьи 134.",
            "Перечень исключений из погашения требований даёт статья 213.28 закона, и "
            "пакет его не моделирует: заявленное исключение снимает вывод о погашении и "
            "поднимает флаг юриста.",
            "Движение денег по специальному банковскому счёту гражданина, возврат "
            "остатков в конкурсную массу и расходы пункта 6 статьи 138 — распределение, "
            "а не квалификация требования, и лежат вне этой модели.",
        ],
    )
