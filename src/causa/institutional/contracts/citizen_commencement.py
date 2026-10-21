"""Формальная модель возбуждения дела о банкротстве гражданина.

Статья 213.3 закона 127-ФЗ и те две статьи, на которые ведёт её оговорка «если
иное не предусмотрено настоящим Федеральным законом»: статья 213.4 (заявление
самого гражданина) и статья 213.5 (заявление кредитора или уполномоченного
органа). Определения конкурсного кредитора, уполномоченного органа,
неплатёжеспособности и недостаточности имущества — из статьи 2.

**Почему институт появился.** Институт статьи 25 ГК РФ с выпуска 1.25.0 писал в
предупреждениях, что пороги возбуждения дела устанавливает статья 213.3 и модель
их не проверяет. Предупреждение было верным; этот институт делает его ненужным.

## Кто вправе обратиться: статья 213.3 пункт 1 и статья 2

Гражданин, конкурсный кредитор, уполномоченный орган — и никто больше. Ловушка
здесь в слове «конкурсный»: не всякий кредитор по денежному обязательству
конкурсный. Статья 2 исключает из конкурсных кредиторов уполномоченные органы
(у них своё основание), граждан, перед которыми должник отвечает за вред жизни
или здоровью, лиц с правом на компенсацию сверх возмещения вреда по
Градостроительному кодексу, авторов результатов интеллектуальной деятельности и
участников должника по обязательствам из участия. Такой кредитор права на
заявление по статье 213.3 не имеет.

Кредитор по заработной плате из этого перечня **не исключён**: действующая
редакция статьи 2 его не называет. Модель следует редакции, а не памяти о
прежней.

## Порог: статья 213.3 пункт 2

Заявление принимается, если требования к гражданину составляют не менее пятисот
тысяч рублей **и** не исполнены в течение трёх месяцев с даты, когда должны были
быть исполнены. Два условия соединены союзом «и», и модель требует обоих.

Денежных величин и дат в фактах модели нет: оба условия — проверенные признаки
рецензента, а не вычисления.

## «Если иное не предусмотрено»: заявление самого гражданина

Статья 213.4 даёт гражданину два основания, и каждое сформулировано своими
условиями:

* **обязанность** (пункт 1): удовлетворение требований одного или нескольких
  кредиторов приводит к невозможности исполнения перед другими в полном объёме,
  и совокупный размер обязательств не менее пятисот тысяч рублей; заявление —
  не позднее тридцати рабочих дней со дня, когда гражданин узнал или должен был
  узнать об этом;
* **право** (пункт 2): предвидение банкротства — обстоятельства, очевидно
  свидетельствующие, что он не в состоянии исполнить обязательства в
  установленный срок, и при этом он отвечает признакам неплатёжеспособности и
  (или) недостаточности имущества.

Модель читает оба основания как то «иное», о котором говорит оговорка пункта 2
статьи 213.3, и **называет это прочтением, а не нормой**. Довод — в структуре
текста: обязанность пункта 1 надо исполнить в тридцать рабочих дней, а
предвидение банкротства пункта 2 по своей природе предшествует просрочке; если
требовать от заявления гражданина трёх месяцев неисполнения, первое основание
стало бы неисполнимым, а второе — пустым. Прямой нормы, вытесняющей порог,
в тексте нет, и разъяснения Пленума о банкротстве граждан среди материалов
пакета тоже нет, поэтому допустимость, основанная на этом прочтении, всегда
поднимает флаг юриста.

## Основание требования кредитора: статья 213.5

Кредитор или уполномоченный орган подаёт заявление при наличии **вступившего в
законную силу решения суда**, подтверждающего требование. Без такого решения —
только по требованиям закрытого перечня пункта 2: обязательные платежи;
нотариальный протест векселя; исполнительная надпись нотариуса; документы
кредитора, устанавливающие обязательство, которое гражданин признаёт, но не
исполняет; нотариально удостоверенные сделки; кредитные договоры с кредитными
организациями; алименты на несовершеннолетних детей, если спор не связан с
отцовством или привлечением других лиц.

Порог пункта 2 статьи 213.3 к заявлению кредитора применяется без изъятий:
оговорка «если иное не предусмотрено» не находит в статье 213.5 ничего, что её
вытесняло бы.

## Индивидуальный предприниматель: уведомление за пятнадцать дней

Если должник — предприниматель, право на заявление возникает только после
опубликования уведомления о намерении в Едином федеральном реестре сведений о
фактах деятельности юридических лиц не менее чем за пятнадцать календарных дней
до обращения. Требование адресовано:

* самому гражданину-предпринимателю (пункт 2.1 статьи 213.4);
* конкурсным кредиторам по требованиям перечня пункта 2 статьи 213.5, то есть
  без решения суда (последний абзац того же пункта).

Кредитора с вступившим в силу решением суда и уполномоченный орган этот абзац
не называет, и модель уведомления от них не требует — следуя тексту, а не
расширяя его.

## Чего модель не делает

* **Не проверяет комплект документов** (пункт 3 статьи 213.4, пункт 3 статьи
  213.5) и внесение вознаграждения финансового управляющего на депозит суда —
  это порядок подачи, а не право на неё.
* **Не разбирает обоснованность заявления** (статья 213.6) и выбор процедуры:
  модель отвечает, примет ли суд заявление, а не чем закончится его
  рассмотрение.
* **Не считает сроки и суммы:** пятьсот тысяч рублей, три месяца, тридцать
  рабочих и пятнадцать календарных дней — проверенные признаки рецензента.
* **Не устанавливает последствия нарушения обязанности** обратиться в суд:
  статья 213.4 их не называет, и модель называет только само нарушение.
* **Отвечает об одном заявлении** по одному делу.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

CITIZEN_COMMENCEMENT_EVIDENCE_SCHEMA_VERSION = "contracts.citizen-commencement-evidence.v0"
CITIZEN_COMMENCEMENT_MAPPING_VERSION = "contracts-reviewed-citizen-commencement-to-facts-v0"
CITIZEN_COMMENCEMENT_MODEL_VERSION = "contracts-citizen-commencement-articles-213-3-213-5-127fz-v0"

# Дословные тексты — synthetic_sources.py: статья 213.3 и две статьи её оговорки
# (213.4 и 213.5), статья 2 с определениями, на которых держатся право на
# обращение и признаки неплатёжеспособности, и статья 213.1 — режим должника.
CITIZEN_COMMENCEMENT_LEGAL_SOURCE_REFS = (
    "synthetic-ru-127fz-213.3-citizen-case-commencement-v1",
    "synthetic-ru-127fz-213.4-citizen-own-application-v1",
    "synthetic-ru-127fz-213.5-creditor-application-v1",
    "synthetic-ru-127fz-2-basic-definitions-v1",
    "synthetic-ru-127fz-213.1-citizen-bankruptcy-regulation-v1",
)


class CitizenCommencementEvidencePredicate(str, Enum):
    # --- Режим: тот же признак, что у остальных институтов главы X ---
    DEBTOR_IS_A_CITIZEN_UNDER_CHAPTER_10 = "debtor_is_a_citizen_under_chapter_10"

    # --- Заявитель: пункт 1 статьи 213.3 ---
    # Заявление подаёт сам гражданин.
    APPLICANT_IS_THE_CITIZEN = "applicant_is_the_citizen"
    # Заявление подаёт кредитор по денежному обязательству. Конкурсный ли он —
    # решает статья 2, и это вывод модели, а не признак.
    APPLICANT_IS_A_MONETARY_CREDITOR = "applicant_is_a_monetary_creditor"
    # Заявление подаёт уполномоченный орган (статья 2).
    APPLICANT_IS_AUTHORISED_BODY = "applicant_is_authorised_body"
    # Заявление подаёт иное лицо: родственник, контрагент без денежного
    # требования, представитель без полномочий.
    APPLICANT_IS_ANOTHER_PERSON = "applicant_is_another_person"
    # Требование кредитора — из исключённых статьёй 2: вред жизни или здоровью,
    # компенсация сверх возмещения вреда по Градостроительному кодексу,
    # вознаграждение автору, обязательство из участия в должнике.
    CREDITOR_CLAIM_EXCLUDED_FROM_COMPETITIVE_CREDITORS = (
        "creditor_claim_excluded_from_competitive_creditors"
    )

    # --- Предприниматель: пункт 2.1 статьи 213.4, пункт 2 статьи 213.5 ---
    DEBTOR_IS_AN_INDIVIDUAL_ENTREPRENEUR = "debtor_is_an_individual_entrepreneur"
    # Уведомление о намерении опубликовано не менее чем за пятнадцать
    # календарных дней до обращения в суд.
    NOTICE_OF_INTENT_PUBLISHED_AT_LEAST_15_DAYS_BEFORE = (
        "notice_of_intent_published_at_least_15_days_before"
    )

    # --- Порог: пункт 2 статьи 213.3 ---
    # Требования к гражданину составляют не менее пятисот тысяч рублей. Тот же
    # признак служит совокупному размеру пункта 1 статьи 213.4.
    CLAIMS_AGAINST_THE_CITIZEN_AT_LEAST_500K = "claims_against_the_citizen_at_least_500k"
    # Требования не исполнены в течение трёх месяцев с даты исполнения.
    CLAIMS_UNPAID_FOR_THREE_MONTHS_AFTER_DUE = "claims_unpaid_for_three_months_after_due"

    # --- Обязанность гражданина: пункт 1 статьи 213.4 ---
    # Удовлетворение требований одних кредиторов приводит к невозможности
    # исполнения перед другими в полном объёме.
    PAYING_SOME_CREDITORS_MAKES_FULL_PERFORMANCE_TO_OTHERS_IMPOSSIBLE = (
        "paying_some_creditors_makes_full_performance_to_others_impossible"
    )
    # Тридцать рабочих дней со дня, когда гражданин узнал или должен был узнать,
    # истекли без заявления.
    DUTY_DEADLINE_OF_30_WORKING_DAYS_MISSED = "duty_deadline_of_30_working_days_missed"

    # --- Право гражданина: пункт 2 статьи 213.4 ---
    # Обстоятельства очевидно свидетельствуют, что гражданин не в состоянии
    # исполнить обязательства в установленный срок.
    CIRCUMSTANCES_OBVIOUSLY_SHOW_INABILITY_TO_PERFORM_ON_TIME = (
        "circumstances_obviously_show_inability_to_perform_on_time"
    )
    # Гражданин отвечает признакам неплатёжеспособности и (или) недостаточности
    # имущества (определения — статья 2).
    SIGNS_OF_INSOLVENCY_OR_INSUFFICIENCY_OF_PROPERTY = (
        "signs_of_insolvency_or_insufficiency_of_property"
    )

    # --- Основание требования кредитора: статья 213.5 ---
    # Требование подтверждено вступившим в законную силу решением суда (пункт 1).
    CLAIM_CONFIRMED_BY_COURT_DECISION_IN_FORCE = "claim_confirmed_by_court_decision_in_force"
    # Требование входит в закрытый перечень пункта 2, подаваемый без решения суда.
    CLAIM_LISTED_IN_ARTICLE_213_5_PARAGRAPH_2 = "claim_listed_in_article_213_5_paragraph_2"


REQUIRED_CITIZEN_COMMENCEMENT_PREDICATES = frozenset(CitizenCommencementEvidencePredicate)

_APPLICANTS = (
    "applicant_is_the_citizen",
    "applicant_is_a_monetary_creditor",
    "applicant_is_authorised_body",
    "applicant_is_another_person",
)


class CitizenCommencementEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: CitizenCommencementEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedCitizenCommencementEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CITIZEN_COMMENCEMENT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[CitizenCommencementEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedCitizenCommencementEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Citizen-commencement evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Citizen-commencement evidence contains duplicate legal source refs.")
        return self


class CitizenCommencementFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    debtor_is_a_citizen_under_chapter_10: bool
    applicant_is_the_citizen: bool
    applicant_is_a_monetary_creditor: bool
    applicant_is_authorised_body: bool
    applicant_is_another_person: bool
    creditor_claim_excluded_from_competitive_creditors: bool
    debtor_is_an_individual_entrepreneur: bool
    notice_of_intent_published_at_least_15_days_before: bool
    claims_against_the_citizen_at_least_500k: bool
    claims_unpaid_for_three_months_after_due: bool
    paying_some_creditors_makes_full_performance_to_others_impossible: bool
    duty_deadline_of_30_working_days_missed: bool
    circumstances_obviously_show_inability_to_perform_on_time: bool
    signs_of_insolvency_or_insufficiency_of_property: bool
    claim_confirmed_by_court_decision_in_force: bool
    claim_listed_in_article_213_5_paragraph_2: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "CitizenCommencementFactSet":
        if sum(getattr(self, name) for name in _APPLICANTS) > 1:
            raise ValueError(
                "Заявление подаёт одно лицо: гражданин, кредитор, уполномоченный орган "
                "либо иное лицо. Несколько заявителей одного заявления пункт 1 статьи "
                "213.3 не предусматривает — каждое заявление разбирается отдельно."
            )
        if (
            self.creditor_claim_excluded_from_competitive_creditors
            and not self.applicant_is_a_monetary_creditor
        ):
            raise ValueError(
                "Исключение из конкурсных кредиторов по статье 2 названо, а заявитель "
                "кредитором по денежному обязательству не назван: исключение относится к "
                "кредитору, а не к заявителю вообще."
            )
        if (
            self.notice_of_intent_published_at_least_15_days_before
            and not self.debtor_is_an_individual_entrepreneur
        ):
            raise ValueError(
                "Уведомление о намерении обратиться в суд требуется, когда должник — "
                "индивидуальный предприниматель (пункт 2.1 статьи 213.4, пункт 2 статьи "
                "213.5); для иного гражданина признак беспредметен."
            )
        if self.duty_deadline_of_30_working_days_missed and not (
            self.paying_some_creditors_makes_full_performance_to_others_impossible
            and self.claims_against_the_citizen_at_least_500k
        ):
            raise ValueError(
                "Срок обязанности обратиться в суд пропущен, а сама обязанность не "
                "возникла: пункт 1 статьи 213.4 связывает её с невозможностью исполнить "
                "всем кредиторам и совокупным размером не менее пятисот тысяч рублей."
            )
        if (
            self.claim_confirmed_by_court_decision_in_force
            or self.claim_listed_in_article_213_5_paragraph_2
        ) and not (self.applicant_is_a_monetary_creditor or self.applicant_is_authorised_body):
            raise ValueError(
                "Основание требования по статье 213.5 названо, а заявитель не кредитор и "
                "не уполномоченный орган: статья 213.5 говорит о заявлении кредитора."
            )
        return self


class CitizenCommencementFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class CitizenCommencementEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: CitizenCommencementFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[CitizenCommencementFactProvenance] = Field(default_factory=list)


class CitizenCommencementConstraintSet(BaseModel):
    id: str
    model_version: str = CITIZEN_COMMENCEMENT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class CitizenCommencementEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    #: Заявитель — конкурсный кредитор в смысле статьи 2.
    applicant_is_competitive_creditor_under_article_2: bool
    #: Заявитель вправе обратиться в суд (пункт 1 статьи 213.3).
    applicant_has_standing: bool
    #: Заявитель права на обращение не имеет (пункт 1 статьи 213.3, статья 2).
    applicant_lacks_standing: bool
    #: Порог пункта 2 статьи 213.3: пятьсот тысяч рублей и три месяца.
    statutory_threshold_met: bool
    #: Гражданин обязан обратиться в суд (пункт 1 статьи 213.4).
    debtor_obliged_to_file: bool
    #: Обязанность обратиться в суд нарушена: тридцать рабочих дней истекли.
    debtor_duty_to_file_breached: bool
    #: Гражданин вправе обратиться при предвидении банкротства (пункт 2 статьи 213.4).
    debtor_may_file_on_foreseen_bankruptcy: bool
    #: Требование кредитора имеет основание статьи 213.5.
    creditor_claim_basis_sufficient: bool
    #: Предприниматель: уведомление за пятнадцать дней требуется и не опубликовано.
    entrepreneur_notice_missing: bool
    #: Заявление самого гражданина подлежит принятию.
    debtors_application_admissible: bool
    #: Заявление кредитора или уполномоченного органа подлежит принятию.
    creditors_application_admissible: bool
    #: Заявление гражданина принимается без порога пункта 2 статьи 213.3 — по
    #: прочтению статьи 213.4 как «иного», которое модель называет прочтением.
    threshold_displaced_for_the_debtors_own_application: bool
    requires_human_citizen_commencement_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_citizen_commencement_evidence(
    evidence: ReviewedCitizenCommencementEvidence,
) -> CitizenCommencementEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Citizen-commencement evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Citizen-commencement evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value
        for predicate in REQUIRED_CITIZEN_COMMENCEMENT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed citizen-commencement evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_CITIZEN_COMMENCEMENT_PREDICATES
    }
    return CitizenCommencementEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CITIZEN_COMMENCEMENT_MAPPING_VERSION,
        facts=CitizenCommencementFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            CitizenCommencementFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_CITIZEN_COMMENCEMENT_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_citizen_commencement_constraint_set(
    mapping: CitizenCommencementEvidenceMappingResult,
) -> CitizenCommencementConstraintSet:
    return CitizenCommencementConstraintSet(
        id=f"citizen-commencement-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            (
                "applicant_is_competitive_creditor_under_article_2 == "
                "debtor_is_a_citizen_under_chapter_10 AND applicant_is_a_monetary_creditor "
                "AND NOT creditor_claim_excluded_from_competitive_creditors"
            ),
            (
                "applicant_has_standing == debtor_is_a_citizen_under_chapter_10 AND "
                "(applicant_is_the_citizen OR "
                "applicant_is_competitive_creditor_under_article_2 OR "
                "applicant_is_authorised_body)"
            ),
            (
                "applicant_lacks_standing == debtor_is_a_citizen_under_chapter_10 AND "
                "(applicant_is_another_person OR (applicant_is_a_monetary_creditor AND "
                "creditor_claim_excluded_from_competitive_creditors))"
            ),
            (
                "statutory_threshold_met == debtor_is_a_citizen_under_chapter_10 AND "
                "claims_against_the_citizen_at_least_500k AND "
                "claims_unpaid_for_three_months_after_due"
            ),
            (
                "debtor_obliged_to_file == debtor_is_a_citizen_under_chapter_10 AND "
                "paying_some_creditors_makes_full_performance_to_others_impossible AND "
                "claims_against_the_citizen_at_least_500k"
            ),
            (
                "debtor_duty_to_file_breached == debtor_obliged_to_file AND "
                "duty_deadline_of_30_working_days_missed"
            ),
            (
                "debtor_may_file_on_foreseen_bankruptcy == "
                "debtor_is_a_citizen_under_chapter_10 AND "
                "circumstances_obviously_show_inability_to_perform_on_time AND "
                "signs_of_insolvency_or_insufficiency_of_property"
            ),
            (
                "creditor_claim_basis_sufficient == debtor_is_a_citizen_under_chapter_10 AND "
                "(claim_confirmed_by_court_decision_in_force OR "
                "claim_listed_in_article_213_5_paragraph_2)"
            ),
            (
                "entrepreneur_notice_missing == debtor_is_a_citizen_under_chapter_10 AND "
                "debtor_is_an_individual_entrepreneur AND "
                "NOT notice_of_intent_published_at_least_15_days_before AND "
                "(applicant_is_the_citizen OR "
                "(applicant_is_competitive_creditor_under_article_2 AND "
                "NOT claim_confirmed_by_court_decision_in_force AND "
                "claim_listed_in_article_213_5_paragraph_2))"
            ),
            (
                "debtors_application_admissible == debtor_is_a_citizen_under_chapter_10 AND "
                "applicant_is_the_citizen AND (statutory_threshold_met OR "
                "debtor_obliged_to_file OR debtor_may_file_on_foreseen_bankruptcy) AND "
                "NOT entrepreneur_notice_missing"
            ),
            (
                "creditors_application_admissible == debtor_is_a_citizen_under_chapter_10 "
                "AND (applicant_is_competitive_creditor_under_article_2 OR "
                "applicant_is_authorised_body) AND creditor_claim_basis_sufficient AND "
                "statutory_threshold_met AND NOT entrepreneur_notice_missing"
            ),
            (
                "threshold_displaced_for_the_debtors_own_application == "
                "debtors_application_admissible AND NOT statutory_threshold_met"
            ),
            (
                "requires_human_citizen_commencement_assessment == "
                "threshold_displaced_for_the_debtors_own_application OR "
                "debtor_may_file_on_foreseen_bankruptcy"
            ),
        ],
    )


def evaluate_citizen_commencement_constraints(
    constraint_set: CitizenCommencementConstraintSet,
    facts: CitizenCommencementFactSet,
) -> CitizenCommencementEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in CitizenCommencementFactSet.model_fields
    }
    applicant_is_competitive_creditor_under_article_2 = Bool(
        "applicant_is_competitive_creditor_under_article_2"
    )
    applicant_has_standing = Bool("applicant_has_standing")
    applicant_lacks_standing = Bool("applicant_lacks_standing")
    statutory_threshold_met = Bool("statutory_threshold_met")
    debtor_obliged_to_file = Bool("debtor_obliged_to_file")
    debtor_duty_to_file_breached = Bool("debtor_duty_to_file_breached")
    debtor_may_file_on_foreseen_bankruptcy = Bool("debtor_may_file_on_foreseen_bankruptcy")
    creditor_claim_basis_sufficient = Bool("creditor_claim_basis_sufficient")
    entrepreneur_notice_missing = Bool("entrepreneur_notice_missing")
    debtors_application_admissible = Bool("debtors_application_admissible")
    creditors_application_admissible = Bool("creditors_application_admissible")
    threshold_displaced_for_the_debtors_own_application = Bool(
        "threshold_displaced_for_the_debtors_own_application"
    )
    requires_human_citizen_commencement_assessment = Bool(
        "requires_human_citizen_commencement_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    # Ворота: возбуждение дела по статьям 213.3–213.5 — правило главы X, и вне
    # её режима институт молчит.
    citizen = variables["debtor_is_a_citizen_under_chapter_10"]

    # Статья 2: не всякий кредитор по денежному обязательству конкурсный.
    solver.add(
        applicant_is_competitive_creditor_under_article_2
        == And(
            citizen,
            variables["applicant_is_a_monetary_creditor"],
            Not(variables["creditor_claim_excluded_from_competitive_creditors"]),
        )
    )
    solver.add(
        applicant_has_standing
        == And(
            citizen,
            Or(
                variables["applicant_is_the_citizen"],
                applicant_is_competitive_creditor_under_article_2,
                variables["applicant_is_authorised_body"],
            ),
        )
    )
    solver.add(
        applicant_lacks_standing
        == And(
            citizen,
            Or(
                variables["applicant_is_another_person"],
                And(
                    variables["applicant_is_a_monetary_creditor"],
                    variables["creditor_claim_excluded_from_competitive_creditors"],
                ),
            ),
        )
    )
    # Пункт 2 статьи 213.3: два условия через «и».
    solver.add(
        statutory_threshold_met
        == And(
            citizen,
            variables["claims_against_the_citizen_at_least_500k"],
            variables["claims_unpaid_for_three_months_after_due"],
        )
    )
    # Пункт 1 статьи 213.4: обязанность — со своим совокупным размером, но без
    # трёх месяцев неисполнения, иначе её нельзя было бы исполнить в срок.
    solver.add(
        debtor_obliged_to_file
        == And(
            citizen,
            variables["paying_some_creditors_makes_full_performance_to_others_impossible"],
            variables["claims_against_the_citizen_at_least_500k"],
        )
    )
    solver.add(
        debtor_duty_to_file_breached
        == And(debtor_obliged_to_file, variables["duty_deadline_of_30_working_days_missed"])
    )
    # Пункт 2 статьи 213.4: право при предвидении банкротства.
    solver.add(
        debtor_may_file_on_foreseen_bankruptcy
        == And(
            citizen,
            variables["circumstances_obviously_show_inability_to_perform_on_time"],
            variables["signs_of_insolvency_or_insufficiency_of_property"],
        )
    )
    # Статья 213.5: решение суда либо закрытый перечень пункта 2.
    solver.add(
        creditor_claim_basis_sufficient
        == And(
            citizen,
            Or(
                variables["claim_confirmed_by_court_decision_in_force"],
                variables["claim_listed_in_article_213_5_paragraph_2"],
            ),
        )
    )
    # Уведомление предпринимателя: самому гражданину и конкурсному кредитору с
    # требованием из перечня пункта 2 статьи 213.5. Кредитора с решением суда и
    # уполномоченный орган текст не называет, и модель его не расширяет.
    solver.add(
        entrepreneur_notice_missing
        == And(
            citizen,
            variables["debtor_is_an_individual_entrepreneur"],
            Not(variables["notice_of_intent_published_at_least_15_days_before"]),
            Or(
                variables["applicant_is_the_citizen"],
                And(
                    applicant_is_competitive_creditor_under_article_2,
                    Not(variables["claim_confirmed_by_court_decision_in_force"]),
                    variables["claim_listed_in_article_213_5_paragraph_2"],
                ),
            ),
        )
    )
    solver.add(
        debtors_application_admissible
        == And(
            citizen,
            variables["applicant_is_the_citizen"],
            Or(
                statutory_threshold_met,
                debtor_obliged_to_file,
                debtor_may_file_on_foreseen_bankruptcy,
            ),
            Not(entrepreneur_notice_missing),
        )
    )
    # К заявлению кредитора порог применяется без изъятий: статья 213.5 ничего
    # «иного» по отношению к нему не содержит.
    solver.add(
        creditors_application_admissible
        == And(
            citizen,
            Or(
                applicant_is_competitive_creditor_under_article_2,
                variables["applicant_is_authorised_body"],
            ),
            creditor_claim_basis_sufficient,
            statutory_threshold_met,
            Not(entrepreneur_notice_missing),
        )
    )
    # Прочтение, названное прочтением: заявление гражданина принято без порога.
    solver.add(
        threshold_displaced_for_the_debtors_own_application
        == And(debtors_application_admissible, Not(statutory_threshold_met))
    )
    solver.add(
        requires_human_citizen_commencement_assessment
        == Or(
            threshold_displaced_for_the_debtors_own_application,
            debtor_may_file_on_foreseen_bankruptcy,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return CitizenCommencementEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            applicant_is_competitive_creditor_under_article_2=False,
            applicant_has_standing=False,
            applicant_lacks_standing=False,
            statutory_threshold_met=False,
            debtor_obliged_to_file=False,
            debtor_duty_to_file_breached=False,
            debtor_may_file_on_foreseen_bankruptcy=False,
            creditor_claim_basis_sufficient=False,
            entrepreneur_notice_missing=False,
            debtors_application_admissible=False,
            creditors_application_admissible=False,
            threshold_displaced_for_the_debtors_own_application=False,
            requires_human_citizen_commencement_assessment=True,
            reasons_ru=["Набор фактов о возбуждении дела о банкротстве гражданина противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru: list[str] = []
    if truth(applicant_lacks_standing):
        if truth(variables["applicant_is_another_person"]):
            ground = (
                "заявитель не гражданин-должник, не кредитор по денежному обязательству и "
                "не уполномоченный орган"
            )
        else:
            ground = (
                "заявитель — кредитор, но его требование из исключённых статьёй 2: вред "
                "жизни или здоровью, компенсация сверх возмещения вреда по "
                "Градостроительному кодексу, вознаграждение автору либо обязательство из "
                "участия в должнике; конкурсным кредитором он не является"
            )
        reasons_ru.append(
            f"Права на обращение в суд с заявлением о признании гражданина банкротом нет: "
            f"{ground} (пункт 1 статьи 213.3 и статья 2 закона 127-ФЗ)."
        )
    if truth(statutory_threshold_met):
        reasons_ru.append(
            "Порог пункта 2 статьи 213.3 закона 127-ФЗ выполнен: требования к гражданину "
            "составляют не менее пятисот тысяч рублей и не исполнены в течение трёх "
            "месяцев с даты, когда должны были быть исполнены."
        )
    if truth(debtor_obliged_to_file):
        reasons_ru.append(
            "Гражданин обязан обратиться в арбитражный суд с заявлением о признании его "
            "банкротом: удовлетворение требований одних кредиторов приводит к "
            "невозможности исполнения перед другими в полном объёме, и совокупный размер "
            "обязательств не менее пятисот тысяч рублей (пункт 1 статьи 213.4 закона). "
            "Срок — тридцать рабочих дней со дня, когда он узнал или должен был узнать об "
            "этом."
        )
    if truth(debtor_duty_to_file_breached):
        reasons_ru.append(
            "Обязанность обратиться в суд нарушена: тридцать рабочих дней истекли без "
            "заявления. Последствий нарушения статья 213.4 не называет, и модель называет "
            "только само нарушение."
        )
    if truth(debtor_may_file_on_foreseen_bankruptcy):
        reasons_ru.append(
            "Гражданин вправе обратиться с заявлением при предвидении банкротства: "
            "обстоятельства очевидно свидетельствуют, что он не в состоянии исполнить "
            "обязательства в установленный срок, и он отвечает признакам "
            "неплатёжеспособности и (или) недостаточности имущества (пункт 2 статьи 213.4 "
            "закона). Что «очевидно свидетельствует», оценивает суд."
        )
    if truth(creditor_claim_basis_sufficient):
        ground = (
            "вступившим в законную силу решением суда (пункт 1 статьи 213.5)"
            if truth(variables["claim_confirmed_by_court_decision_in_force"])
            else "требованием из закрытого перечня пункта 2 статьи 213.5, подаваемым без "
            "решения суда"
        )
        reasons_ru.append(f"Требование кредитора имеет основание: оно подтверждено {ground}.")
    if truth(entrepreneur_notice_missing):
        reasons_ru.append(
            "Должник — индивидуальный предприниматель, и право на заявление ещё не "
            "возникло: уведомление о намерении обратиться в суд не опубликовано в Едином "
            "федеральном реестре сведений о фактах деятельности юридических лиц не менее "
            "чем за пятнадцать календарных дней (пункт 2.1 статьи 213.4, пункт 2 статьи "
            "213.5 закона)."
        )
    if truth(debtors_application_admissible):
        reasons_ru.append(
            "Заявление гражданина о признании его банкротом подлежит принятию арбитражным судом."
        )
    if truth(threshold_displaced_for_the_debtors_own_application):
        reasons_ru.append(
            "Заявление гражданина принимается без порога пункта 2 статьи 213.3: модель "
            "читает основания статьи 213.4 как то «иное», о котором говорит оговорка этого "
            "пункта, потому что обязанность пункта 1 надо исполнить в тридцать рабочих "
            "дней, а предвидение банкротства пункта 2 предшествует просрочке. Это "
            "прочтение структуры текста, а не прямая норма, и разъяснения Пленума о "
            "банкротстве граждан среди материалов пакета нет — требуется проверка юристом."
        )
    if truth(creditors_application_admissible):
        reasons_ru.append(
            "Заявление кредитора или уполномоченного органа о признании гражданина "
            "банкротом подлежит принятию арбитражным судом: заявитель вправе обратиться, "
            "требование имеет основание статьи 213.5, и порог пункта 2 статьи 213.3 "
            "выполнен."
        )
    if (
        truth(citizen)
        and (
            truth(applicant_is_competitive_creditor_under_article_2)
            or truth(variables["applicant_is_authorised_body"])
        )
        and not truth(creditors_application_admissible)
    ):
        missing = []
        if not truth(creditor_claim_basis_sufficient):
            missing.append(
                "нет ни решения суда, вступившего в законную силу, ни требования из "
                "перечня пункта 2 статьи 213.5"
            )
        if not truth(statutory_threshold_met):
            missing.append(
                "порог пункта 2 статьи 213.3 не выполнен, а к заявлению кредитора он "
                "применяется без изъятий"
            )
        if truth(entrepreneur_notice_missing):
            missing.append("уведомление предпринимателя не опубликовано")
        reasons_ru.append("Заявление кредитора принятию не подлежит: " + "; ".join(missing) + ".")
    if truth(requires_human_citizen_commencement_assessment):
        reasons_ru.append(
            "Требуется оценка юриста: очевидность неспособности исполнить обязательства в "
            "срок и вытеснение порога статьёй 213.4 модель не устанавливает, а называет."
        )
    return CitizenCommencementEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        applicant_is_competitive_creditor_under_article_2=truth(
            applicant_is_competitive_creditor_under_article_2
        ),
        applicant_has_standing=truth(applicant_has_standing),
        applicant_lacks_standing=truth(applicant_lacks_standing),
        statutory_threshold_met=truth(statutory_threshold_met),
        debtor_obliged_to_file=truth(debtor_obliged_to_file),
        debtor_duty_to_file_breached=truth(debtor_duty_to_file_breached),
        debtor_may_file_on_foreseen_bankruptcy=truth(debtor_may_file_on_foreseen_bankruptcy),
        creditor_claim_basis_sufficient=truth(creditor_claim_basis_sufficient),
        entrepreneur_notice_missing=truth(entrepreneur_notice_missing),
        debtors_application_admissible=truth(debtors_application_admissible),
        creditors_application_admissible=truth(creditors_application_admissible),
        threshold_displaced_for_the_debtors_own_application=truth(
            threshold_displaced_for_the_debtors_own_application
        ),
        requires_human_citizen_commencement_assessment=truth(
            requires_human_citizen_commencement_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель отвечает, примет ли суд заявление, а не чем закончится его "
            "рассмотрение: обоснованность заявления и выбор процедуры (статья 213.6) лежат "
            "вне её.",
            "Пятьсот тысяч рублей, три месяца, тридцать рабочих и пятнадцать календарных "
            "дней — проверенные признаки рецензента, а не вычисления: денежных величин и "
            "дат в фактах модели нет.",
            "Комплект документов к заявлению (пункт 3 статьи 213.4, пункт 3 статьи 213.5) и "
            "внесение вознаграждения финансового управляющего на депозит суда — порядок "
            "подачи, а не право на неё; модель их не проверяет.",
            "Вытеснение порога пункта 2 статьи 213.3 основаниями статьи 213.4 — прочтение "
            "структуры текста. Разъяснения Пленума Верховного Суда о банкротстве граждан "
            "среди материалов пакета нет, и на него модель не ссылается.",
        ],
    )
