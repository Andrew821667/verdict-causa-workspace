"""Формальная модель несостоятельности (банкротства) гражданина.

Статья 25 ГК РФ целиком: два пункта. Институт — вход в режим, которым
банкротство гражданина разбирается, и граница этого входа.

**Почему институт появился и что при этом нашлось.** Статья 25 была последней
записью `KNOWN_GAPS_RU` и одновременно записью `CODE_GAP_REASONS_RU` — второй
статьёй после 420, объявленной в двух картах сразу. Обе карты называли одну и ту
же причину: институт лиц (статьи 17–53) разбирает право- и дееспособность, а не
банкротство, **и эту область пакет моделирует отдельным институтом
банкротства**. Первая половина причины верна. Вторая оказалась неверной, и
неверность была не редакционной.

Четыре института банкротства пакета разбирают статьи 5, 63, 134, 135, 138,
61.1–61.3, 61.9 и 4.1 закона 127-ФЗ. Ни один из них не знает, кто должник: ни
одного предиката о гражданине в их контрактах данных нет. Между тем глава X
закона (статьи 213.1–213.32) устанавливает для гражданина **свою** очерёдность —
статья 213.27, — и она отличается от очерёдности конкурсного производства по
существу, а не по редакции:

* требование о взыскании **алиментов** статья 213.27 пункт 3 относит к первой
  очереди реестра; у статьи 134 пункт 4 такой категории нет вовсе, и требование
  падало в остаточную третью очередь;
* **вознаграждение автору** результата интеллектуальной деятельности статья 134
  пункт 4 относит ко второй очереди; статья 213.27 пункт 3 его не называет, и
  оно идёт в расчёты с другими кредиторами;
* среди текущих платежей статья 213.27 пункт 2 называет отдельной третьей
  очередью **плату за жилое помещение и коммунальные услуги**; пять очередей
  статьи 134 пункт 2 этой категории не знают.

Проверено прогоном, а не прочтением: институт очерёдности отвечал «третья
очередь» на требование об алиментах гражданина-должника и не поднимал флага. Это
не пробел, а **неверный ответ**, и объявить статью 25 покрытой, оставив его на
месте, значило бы закрыть пробел на словах.

## Пункт 1: условие признания и единственный путь к нему

«Гражданин, который не способен удовлетворить требования кредиторов по денежным
обязательствам и (или) исполнить обязанность по уплате обязательных платежей,
может быть признан несостоятельным (банкротом) по решению арбитражного суда.»

Четыре элемента, и каждый важен:

* **субъект — гражданин.** Для юридического лица условия устанавливает статья 65
  и свои нормы 127-ФЗ; эта модель о гражданине.
* **«и (или)»** — достаточно одной из двух неспособностей: по денежным
  обязательствам либо по обязательным платежам. Союз прочитан как ИЛИ, потому
  что так он и написан.
* **«может быть признан»** — возможность, а не следствие. Неспособность сама по
  себе банкротом не делает.
* **«по решению арбитражного суда»** — единственный путь. Заявление кредитора,
  признание самого должника, внесудебный порядок — ничто из этого решением суда
  не является, и вывод об этом назван прямо, потому что в споре о последствиях
  банкротства подмена заявления решением встречается чаще, чем кажется.

Конкретные пороги — не менее пятисот тысяч рублей и три месяца неисполнения —
устанавливает статья 213.3 пункт 2 закона 127-ФЗ, а не статья 25: статья 25 даёт
содержательное условие, а не процессуальный порог. Пороги проверяет институт
возбуждения дела о банкротстве гражданина (статьи 213.3–213.5, `citizen_commencement`).

## Пункт 2: что устанавливает закон о банкротстве

«Основания, порядок и последствия признания арбитражным судом гражданина
несостоятельным (банкротом), очередность удовлетворения требований кредиторов,
порядок применения процедур в деле о несостоятельности (банкротстве) гражданина
устанавливаются законом, регулирующим вопросы несостоятельности
(банкротства).»

Пять отсылок, и одна из них в этом пакете работает: **очередность
удовлетворения требований кредиторов**. Статья 25 отвечает не на вопрос об
очерёдности, а на вопрос о том, **чем её определять** — и этого достаточно,
чтобы запретить определять её не тем.

## Какой режим применяется: статья 213.1 закона

Отсылка пункта 2 ведёт не в одну точку. Статья 213.1 закона распределяет
должников-граждан по режимам, и распределение существенно:

* **гражданин** — глава X закона, а в неурегулированной ею части главы I–III.1,
  VII, VIII, параграф 7 главы IX и параграф 2 главы XI (пункт 1);
* **индивидуальный предприниматель** — та же глава X «с учётом особенностей»
  (пункт 3), и среди особенностей, например, продажа предпринимательского
  имущества по правилам для юридических лиц (пункт 4);
* **крестьянское (фермерское) хозяйство** — глава X **не применяется** вовсе
  (пункт 2).

Без этой развилки модель, сказавшая «гражданин — значит глава X», ошибалась бы
на крестьянском хозяйстве. Поэтому исключение выведено отдельным выводом, а не
спрятано в отрицании.

## Чего модель не делает

* **Не определяет очерёдность требований гражданина сама.** Её определяет институт
  статьи 213.27 (`citizen_ranking`); эта модель называет, каким законом очерёдность
  определяется. В выпуске 1.25.0, пока статья 213.27 не была смоделирована, на этом
  выводе поднимался флаг юриста; с выпуска 1.26.0 вопрос имеет ответ, и флаг снят.
* **Не проверяет пороги возбуждения дела сама** — это делает институт статей
  213.3–213.5 (`citizen_commencement`) — и не разбирает процедуры
  (реструктуризация долгов, реализация имущества, мировое соглашение — статья 213.2).
* **Не решает вопрос об освобождении гражданина от обязательств** — это делает
  институт статьи 213.28 (`citizen_release`).
* **Не разбирает банкротство юридического лица:** условия для него даёт статья
  65 ГК РФ, а не статья 25.
* **Отвечает об одном должнике** по одному делу: контракт данных даёт один блок
  доказательств на институт.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

CITIZEN_BANKRUPTCY_EVIDENCE_SCHEMA_VERSION = "contracts.citizen-bankruptcy-evidence.v0"
CITIZEN_BANKRUPTCY_MAPPING_VERSION = "contracts-reviewed-citizen-bankruptcy-to-facts-v0"
CITIZEN_BANKRUPTCY_MODEL_VERSION = "contracts-citizen-bankruptcy-article-25-v0"

# Дословный текст статьи 25 ГК РФ — synthetic_sources.py,
# synthetic-ru-gk25-citizen-insolvency-v1. Отсылка пункта 2 ведёт в закон
# 127-ФЗ: статья 213.1 распределяет должников-граждан по режимам, статья
# 213.27 устанавливает очерёдность для гражданина, а статья 134 — ту
# очерёдность конкурсного производства, которую она для гражданина вытесняет.
CITIZEN_BANKRUPTCY_LEGAL_SOURCE_REFS = (
    "synthetic-ru-gk25-citizen-insolvency-v1",
    "synthetic-ru-127fz-213.1-citizen-bankruptcy-regulation-v1",
    "synthetic-ru-127fz-213.27-citizen-creditor-ranking-v1",
    "synthetic-ru-127fz-134-creditor-ranking-v1",
)


class CitizenBankruptcyEvidencePredicate(str, Enum):
    # --- Пункт 1: субъект и условие ---
    # Должник — гражданин. Для юридического лица условия даёт статья 65 ГК РФ.
    DEBTOR_IS_A_CITIZEN = "debtor_is_a_citizen"
    # Не способен удовлетворить требования кредиторов по денежным обязательствам.
    UNABLE_TO_SATISFY_MONETARY_OBLIGATIONS = "unable_to_satisfy_monetary_obligations"
    # Не способен исполнить обязанность по уплате обязательных платежей.
    # Союз «и (или)» пункта 1 делает достаточной любую из двух неспособностей.
    UNABLE_TO_PAY_OBLIGATORY_PAYMENTS = "unable_to_pay_obligatory_payments"
    # Арбитражный суд признал гражданина несостоятельным (банкротом).
    ARBITRATION_COURT_DECLARED_BANKRUPT = "arbitration_court_declared_bankrupt"
    # Несостоятельность заявлена вне решения арбитражного суда: кредитором, самим
    # должником, во внесудебном порядке. Пункт 1 такого пути не знает.
    BANKRUPTCY_ASSERTED_WITHOUT_A_COURT_DECISION = "bankruptcy_asserted_without_a_court_decision"

    # --- Режим: статья 213.1 закона 127-ФЗ ---
    # Гражданин является индивидуальным предпринимателем: глава X применяется с
    # особенностями (пункт 3 статьи 213.1).
    DEBTOR_IS_AN_INDIVIDUAL_ENTREPRENEUR = "debtor_is_an_individual_entrepreneur"
    # Крестьянское (фермерское) хозяйство: глава X не применяется вовсе
    # (пункт 2 статьи 213.1).
    DEBTOR_IS_A_PEASANT_FARM_HOLDING = "debtor_is_a_peasant_farm_holding"

    # --- Пункт 2: отсылка, которая в этом пакете работает ---
    # В деле поставлен вопрос об очерёдности удовлетворения требований кредиторов.
    CREDITOR_RANKING_QUESTION_RAISED = "creditor_ranking_question_raised"
    # К требованию применена очерёдность конкурсного производства (статья 134
    # закона 127-ФЗ). Для гражданина её вытесняет статья 213.27.
    LIQUIDATION_RANKING_OF_ARTICLE_134_APPLIED = "liquidation_ranking_of_article_134_applied"


REQUIRED_CITIZEN_BANKRUPTCY_PREDICATES = frozenset(CitizenBankruptcyEvidencePredicate)


class CitizenBankruptcyEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: CitizenBankruptcyEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedCitizenBankruptcyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CITIZEN_BANKRUPTCY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[CitizenBankruptcyEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedCitizenBankruptcyEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Citizen-bankruptcy evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Citizen-bankruptcy evidence contains duplicate legal source refs.")
        return self


class CitizenBankruptcyFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    debtor_is_a_citizen: bool
    unable_to_satisfy_monetary_obligations: bool
    unable_to_pay_obligatory_payments: bool
    arbitration_court_declared_bankrupt: bool
    bankruptcy_asserted_without_a_court_decision: bool
    debtor_is_an_individual_entrepreneur: bool
    debtor_is_a_peasant_farm_holding: bool
    creditor_ranking_question_raised: bool
    liquidation_ranking_of_article_134_applied: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "CitizenBankruptcyFactSet":
        citizen_only = {
            "unable_to_satisfy_monetary_obligations": "неспособность по денежным обязательствам",
            "unable_to_pay_obligatory_payments": "неспособность по обязательным платежам",
            "arbitration_court_declared_bankrupt": "решение суда о признании банкротом",
            "bankruptcy_asserted_without_a_court_decision": "заявление о несостоятельности",
            "debtor_is_an_individual_entrepreneur": "статус индивидуального предпринимателя",
            "debtor_is_a_peasant_farm_holding": "статус крестьянского хозяйства",
        }
        for field_name, label in citizen_only.items():
            if getattr(self, field_name) and not self.debtor_is_a_citizen:
                raise ValueError(
                    f"Признак «{label}» заявлен, а должник не назван гражданином: "
                    "статья 25 ГК РФ отвечает о гражданине, а условия банкротства "
                    "юридического лица даёт статья 65 ГК РФ."
                )
        if self.arbitration_court_declared_bankrupt and (
            self.bankruptcy_asserted_without_a_court_decision
        ):
            raise ValueError(
                "Решение арбитражного суда о признании банкротом и заявление о "
                "несостоятельности вне такого решения исключают друг друга: пункт 1 "
                "статьи 25 ГК РФ знает только один путь."
            )
        if self.arbitration_court_declared_bankrupt and not (
            self.unable_to_satisfy_monetary_obligations or self.unable_to_pay_obligatory_payments
        ):
            raise ValueError(
                "Решение о признании банкротом без неспособности удовлетворить "
                "требования кредиторов или исполнить обязанность по уплате "
                "обязательных платежей беспредметно: пункт 1 статьи 25 ГК РФ делает "
                "её условием признания."
            )
        if self.liquidation_ranking_of_article_134_applied and not (
            self.creditor_ranking_question_raised
        ):
            raise ValueError(
                "Очерёдность применена, а вопрос об очерёдности в деле не поставлен: "
                "применение правила предполагает вопрос, на который оно отвечает."
            )
        return self


class CitizenBankruptcyFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class CitizenBankruptcyEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: CitizenBankruptcyFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[CitizenBankruptcyFactProvenance] = Field(default_factory=list)


class CitizenBankruptcyConstraintSet(BaseModel):
    id: str
    model_version: str = CITIZEN_BANKRUPTCY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class CitizenBankruptcyEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    #: Условие пункта 1 статьи 25 выполнено: гражданин и хотя бы одна неспособность.
    citizen_may_be_declared_bankrupt: bool
    #: Гражданин признан банкротом решением арбитражного суда (пункт 1).
    citizen_declared_bankrupt: bool
    #: Банкротом делает только решение суда: заявление им не является (пункт 1).
    bankruptcy_requires_a_court_decision: bool
    #: Гражданин в деле есть, но условие пункта 1 не выполнено.
    insolvency_test_not_met: bool
    #: Применяется режим главы X закона 127-ФЗ (пункты 1 и 3 статьи 213.1).
    citizen_bankruptcy_regime_applies: bool
    #: Глава X применяется с особенностями для предпринимателя (пункт 3 статьи 213.1).
    entrepreneur_specifics_apply: bool
    #: Глава X не применяется: крестьянское хозяйство (пункт 2 статьи 213.1).
    citizen_regime_excluded_for_peasant_farm: bool
    #: Очерёдность требований устанавливает закон о банкротстве, а не ГК (пункт 2).
    creditor_ranking_governed_by_bankruptcy_law: bool
    #: К требованию гражданина применена очерёдность статьи 134, которую для него
    #: вытесняет статья 213.27.
    liquidation_ranking_wrongly_applied_to_a_citizen: bool
    requires_human_citizen_bankruptcy_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_citizen_bankruptcy_evidence(
    evidence: ReviewedCitizenBankruptcyEvidence,
) -> CitizenBankruptcyEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Citizen-bankruptcy evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Citizen-bankruptcy evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_CITIZEN_BANKRUPTCY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed citizen-bankruptcy evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_CITIZEN_BANKRUPTCY_PREDICATES
    }
    return CitizenBankruptcyEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CITIZEN_BANKRUPTCY_MAPPING_VERSION,
        facts=CitizenBankruptcyFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            CitizenBankruptcyFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_CITIZEN_BANKRUPTCY_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_citizen_bankruptcy_constraint_set(
    mapping: CitizenBankruptcyEvidenceMappingResult,
) -> CitizenBankruptcyConstraintSet:
    return CitizenBankruptcyConstraintSet(
        id=f"citizen-bankruptcy-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            (
                "citizen_may_be_declared_bankrupt == debtor_is_a_citizen AND "
                "(unable_to_satisfy_monetary_obligations OR unable_to_pay_obligatory_payments)"
            ),
            (
                "citizen_declared_bankrupt == debtor_is_a_citizen AND "
                "arbitration_court_declared_bankrupt"
            ),
            (
                "bankruptcy_requires_a_court_decision == debtor_is_a_citizen AND "
                "bankruptcy_asserted_without_a_court_decision"
            ),
            (
                "insolvency_test_not_met == debtor_is_a_citizen AND "
                "NOT unable_to_satisfy_monetary_obligations AND "
                "NOT unable_to_pay_obligatory_payments"
            ),
            (
                "citizen_bankruptcy_regime_applies == debtor_is_a_citizen AND "
                "NOT debtor_is_a_peasant_farm_holding"
            ),
            (
                "entrepreneur_specifics_apply == debtor_is_an_individual_entrepreneur AND "
                "NOT debtor_is_a_peasant_farm_holding"
            ),
            (
                "citizen_regime_excluded_for_peasant_farm == debtor_is_a_citizen AND "
                "debtor_is_a_peasant_farm_holding"
            ),
            (
                "creditor_ranking_governed_by_bankruptcy_law == "
                "citizen_bankruptcy_regime_applies AND creditor_ranking_question_raised"
            ),
            (
                "liquidation_ranking_wrongly_applied_to_a_citizen == "
                "citizen_bankruptcy_regime_applies AND "
                "liquidation_ranking_of_article_134_applied"
            ),
            (
                "requires_human_citizen_bankruptcy_assessment == "
                "liquidation_ranking_wrongly_applied_to_a_citizen OR "
                "entrepreneur_specifics_apply OR citizen_regime_excluded_for_peasant_farm"
            ),
        ],
    )


def evaluate_citizen_bankruptcy_constraints(
    constraint_set: CitizenBankruptcyConstraintSet,
    facts: CitizenBankruptcyFactSet,
) -> CitizenBankruptcyEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in CitizenBankruptcyFactSet.model_fields
    }
    citizen_may_be_declared_bankrupt = Bool("citizen_may_be_declared_bankrupt")
    citizen_declared_bankrupt = Bool("citizen_declared_bankrupt")
    bankruptcy_requires_a_court_decision = Bool("bankruptcy_requires_a_court_decision")
    insolvency_test_not_met = Bool("insolvency_test_not_met")
    citizen_bankruptcy_regime_applies = Bool("citizen_bankruptcy_regime_applies")
    entrepreneur_specifics_apply = Bool("entrepreneur_specifics_apply")
    citizen_regime_excluded_for_peasant_farm = Bool("citizen_regime_excluded_for_peasant_farm")
    creditor_ranking_governed_by_bankruptcy_law = Bool(
        "creditor_ranking_governed_by_bankruptcy_law"
    )
    liquidation_ranking_wrongly_applied_to_a_citizen = Bool(
        "liquidation_ranking_wrongly_applied_to_a_citizen"
    )
    requires_human_citizen_bankruptcy_assessment = Bool(
        "requires_human_citizen_bankruptcy_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    # Союз «и (или)» пункта 1 прочитан как ИЛИ: достаточно одной неспособности.
    unable = Or(
        variables["unable_to_satisfy_monetary_obligations"],
        variables["unable_to_pay_obligatory_payments"],
    )
    solver.add(citizen_may_be_declared_bankrupt == And(variables["debtor_is_a_citizen"], unable))
    # «Может быть признан ... по решению арбитражного суда»: признание — это
    # решение суда, а не наступление условия.
    solver.add(
        citizen_declared_bankrupt
        == And(
            variables["debtor_is_a_citizen"],
            variables["arbitration_court_declared_bankrupt"],
        )
    )
    # Вывод, который легко потерять: заявление о несостоятельности банкротом не
    # делает, каким бы обоснованным оно ни было.
    solver.add(
        bankruptcy_requires_a_court_decision
        == And(
            variables["debtor_is_a_citizen"],
            variables["bankruptcy_asserted_without_a_court_decision"],
        )
    )
    solver.add(insolvency_test_not_met == And(variables["debtor_is_a_citizen"], Not(unable)))
    # Статья 213.1 закона 127-ФЗ: гражданин — глава X, предприниматель — та же
    # глава с особенностями, крестьянское хозяйство — не глава X вовсе.
    solver.add(
        citizen_bankruptcy_regime_applies
        == And(
            variables["debtor_is_a_citizen"],
            Not(variables["debtor_is_a_peasant_farm_holding"]),
        )
    )
    solver.add(
        entrepreneur_specifics_apply
        == And(
            variables["debtor_is_an_individual_entrepreneur"],
            Not(variables["debtor_is_a_peasant_farm_holding"]),
        )
    )
    # Исключение выведено отдельно, а не оставлено в отрицании: модель, сказавшая
    # «гражданин — значит глава X», ошибалась бы на крестьянском хозяйстве.
    solver.add(
        citizen_regime_excluded_for_peasant_farm
        == And(
            variables["debtor_is_a_citizen"],
            variables["debtor_is_a_peasant_farm_holding"],
        )
    )
    solver.add(
        creditor_ranking_governed_by_bankruptcy_law
        == And(
            citizen_bankruptcy_regime_applies,
            variables["creditor_ranking_question_raised"],
        )
    )
    # Измеренный дефект: очерёдность конкурсного производства, применённая к
    # требованию гражданина, расходится со статьёй 213.27 по существу.
    solver.add(
        liquidation_ranking_wrongly_applied_to_a_citizen
        == And(
            citizen_bankruptcy_regime_applies,
            variables["liquidation_ranking_of_article_134_applied"],
        )
    )
    solver.add(
        requires_human_citizen_bankruptcy_assessment
        == Or(
            # Поставленный вопрос об очерёдности флага больше не поднимает: с
            # выпуска 1.26.0 очередь определяет институт статьи 213.27. Флаг
            # остаётся там, где правило уже применено неверно или не смоделировано.
            liquidation_ranking_wrongly_applied_to_a_citizen,
            entrepreneur_specifics_apply,
            citizen_regime_excluded_for_peasant_farm,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return CitizenBankruptcyEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            citizen_may_be_declared_bankrupt=False,
            citizen_declared_bankrupt=False,
            bankruptcy_requires_a_court_decision=False,
            insolvency_test_not_met=False,
            citizen_bankruptcy_regime_applies=False,
            entrepreneur_specifics_apply=False,
            citizen_regime_excluded_for_peasant_farm=False,
            creditor_ranking_governed_by_bankruptcy_law=False,
            liquidation_ranking_wrongly_applied_to_a_citizen=False,
            requires_human_citizen_bankruptcy_assessment=True,
            reasons_ru=["Набор фактов о банкротстве гражданина противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru: list[str] = []
    if truth(citizen_may_be_declared_bankrupt):
        grounds = []
        if truth(variables["unable_to_satisfy_monetary_obligations"]):
            grounds.append("требования кредиторов по денежным обязательствам")
        if truth(variables["unable_to_pay_obligatory_payments"]):
            grounds.append("обязанность по уплате обязательных платежей")
        reasons_ru.append(
            "Условие пункта 1 статьи 25 ГК РФ выполнено: гражданин не способен "
            "исполнить " + " и ".join(grounds) + ". Признание банкротом при этом "
            "остаётся возможностью, а не следствием: статья говорит «может быть "
            "признан»."
        )
    if truth(insolvency_test_not_met):
        reasons_ru.append(
            "Условие пункта 1 статьи 25 ГК РФ не выполнено: неспособность "
            "удовлетворить требования кредиторов по денежным обязательствам либо "
            "исполнить обязанность по уплате обязательных платежей не установлена. "
            "Оснований признавать гражданина банкротом по этой статье нет."
        )
    if truth(citizen_declared_bankrupt):
        reasons_ru.append(
            "Гражданин признан несостоятельным (банкротом) решением арбитражного суда "
            "(пункт 1 статьи 25 ГК РФ)."
        )
    if truth(bankruptcy_requires_a_court_decision):
        reasons_ru.append(
            "Несостоятельность заявлена вне решения арбитражного суда. Банкротом "
            "гражданина делает только решение суда: пункт 1 статьи 25 ГК РФ иного "
            "пути не знает, и заявление кредитора, признание самого должника или "
            "внесудебный порядок решением не являются."
        )
    if truth(citizen_bankruptcy_regime_applies):
        reasons_ru.append(
            "Отношения, связанные с банкротством этого должника, регулируются главой X "
            "закона 127-ФЗ, а в неурегулированной ею части — главами I–III.1, VII, "
            "VIII, параграфом 7 главы IX и параграфом 2 главы XI (пункт 1 статьи 213.1 "
            "закона). Основания, порядок, последствия, очерёдность и порядок применения "
            "процедур пункт 2 статьи 25 ГК РФ отдаёт этому закону."
        )
    if truth(entrepreneur_specifics_apply):
        reasons_ru.append(
            "Должник — индивидуальный предприниматель: глава X применяется с "
            "особенностями (пункт 3 статьи 213.1 закона 127-ФЗ). Среди них, например, "
            "продажа предпринимательского имущества по правилам, установленным для "
            "юридических лиц (пункт 4 той же статьи). Особенности модель не разбирает."
        )
    if truth(citizen_regime_excluded_for_peasant_farm):
        reasons_ru.append(
            "Должник — крестьянское (фермерское) хозяйство, и к его банкротству "
            "положения о банкротстве граждан не применяются вовсе (пункт 2 статьи 213.1 "
            "закона 127-ФЗ). Эту область пакет не моделирует."
        )
    if truth(creditor_ranking_governed_by_bankruptcy_law):
        reasons_ru.append(
            "Очерёдность удовлетворения требований кредиторов гражданина устанавливает "
            "закон о банкротстве, а не ГК РФ (пункт 2 статьи 25 ГК РФ): для гражданина "
            "это статья 213.27 закона 127-ФЗ. Очередь требования определяет институт "
            "этой статьи, а здесь называется, каким законом её определять."
        )
    if truth(liquidation_ranking_wrongly_applied_to_a_citizen):
        reasons_ru.append(
            "К требованию в деле о банкротстве гражданина применена очерёдность "
            "конкурсного производства (статья 134 закона 127-ФЗ). Для гражданина её "
            "вытесняет статья 213.27, и расхождение не редакционное: требование о "
            "взыскании алиментов статья 213.27 пункт 3 относит к первой очереди "
            "реестра, а у статьи 134 такой категории нет; вознаграждение автору "
            "результата интеллектуальной деятельности статья 134 относит ко второй "
            "очереди, а статья 213.27 его не называет; плату за жилое помещение и "
            "коммунальные услуги статья 213.27 пункт 2 выделяет в третью очередь "
            "текущих платежей, которой пять очередей статьи 134 не знают. Очерёдность "
            "подлежит определению заново."
        )
    if truth(requires_human_citizen_bankruptcy_assessment):
        reasons_ru.append(
            "Требуется оценка юриста. Особенности банкротства предпринимателя и "
            "банкротство крестьянского хозяйства в пакете не смоделированы, а "
            "очерёдность, применённая к гражданину по статье 134, подлежит определению "
            "заново: модель называет применимое правило, но не исправляет уже "
            "состоявшееся распределение."
        )
    return CitizenBankruptcyEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        citizen_may_be_declared_bankrupt=truth(citizen_may_be_declared_bankrupt),
        citizen_declared_bankrupt=truth(citizen_declared_bankrupt),
        bankruptcy_requires_a_court_decision=truth(bankruptcy_requires_a_court_decision),
        insolvency_test_not_met=truth(insolvency_test_not_met),
        citizen_bankruptcy_regime_applies=truth(citizen_bankruptcy_regime_applies),
        entrepreneur_specifics_apply=truth(entrepreneur_specifics_apply),
        citizen_regime_excluded_for_peasant_farm=truth(citizen_regime_excluded_for_peasant_farm),
        creditor_ranking_governed_by_bankruptcy_law=truth(
            creditor_ranking_governed_by_bankruptcy_law
        ),
        liquidation_ranking_wrongly_applied_to_a_citizen=truth(
            liquidation_ranking_wrongly_applied_to_a_citizen
        ),
        requires_human_citizen_bankruptcy_assessment=truth(
            requires_human_citizen_bankruptcy_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель отвечает, при каком условии гражданин может быть признан банкротом "
            "и каким законом его банкротство разбирается. Сами основания, порядок, "
            "последствия и очерёдность пункт 2 статьи 25 ГК РФ отдаёт закону 127-ФЗ. Из "
            "главы X этого закона пакет моделирует возбуждение дела (статьи 213.3–213.5), "
            "очерёдность (статья 213.27) и освобождение от обязательств (статья 213.28) — "
            "каждое своим институтом.",
            "Пороги возбуждения дела — не менее пятисот тысяч рублей и три месяца "
            "неисполнения — устанавливает пункт 2 статьи 213.3 закона 127-ФЗ, а не "
            "статья 25; их проверяет институт возбуждения дела.",
            "Процедуры дела о банкротстве гражданина (реструктуризация долгов, "
            "реализация имущества, мировое соглашение — статья 213.2 закона) в пакете не "
            "смоделированы.",
            "Условия банкротства юридического лица даёт статья 65 ГК РФ, а не статья 25: "
            "модель о гражданине и молчит о юридическом лице.",
        ],
    )
