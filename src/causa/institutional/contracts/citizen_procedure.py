"""Формальная модель обоснованности заявления и процедуры банкротства гражданина.

Статья 213.2 закона 127-ФЗ называет процедуры дела о банкротстве гражданина:
реструктуризация долгов, реализация имущества, мировое соглашение. Какая из них
вводится, решается по результатам проверки обоснованности заявления — статья
213.6, — а прямой переход к реализации имущества зависит от требований к плану
реструктуризации пункта 1 статьи 213.13.

**Почему институт появился.** Статья 213.2 — последняя из четырёх статей главы
X, названных долгом в выпуске 1.25.0. Сама статья — одно предложение, и
смоделировать её отдельно значило бы смоделировать перечень. Вопрос, на который
она отвечает по существу, — какую процедуру получит гражданин, — решают статьи
213.6 и 213.13, и институт разбирает их вместе.

## Процедур три, и их перечень закрыт

Реструктуризация долгов гражданина, реализация имущества гражданина, мировое
соглашение — и только они. Наблюдения, финансового оздоровления, внешнего
управления и конкурсного производства статья 213.2 для гражданина не называет.
Мирового соглашения среди определений пункта 1 статьи 213.6 нет: его заключают
в ходе производства по решению собрания кредиторов, и оно служит основанием
прекращения производства (статья 213.31). Модель его не разбирает.

## Пункт 1 статьи 213.6: определений три

* о признании заявления обоснованным и введении реструктуризации долгов;
* о признании заявления необоснованным и оставлении его без рассмотрения;
* о признании заявления необоснованным и прекращении производства по делу.

Перечень закрыт: суд выносит «одно из следующих определений». Из этого модель
выводит, что необоснованное заявление получает одно из двух последних
определений, и выбор между ними решает только одно обстоятельство пункта 2 —
есть ли иное заявление о признании гражданина банкротом.

## Пункт 2 статьи 213.6: обоснованность у двух заявителей разная

Заявление **кредитора или уполномоченного органа** обоснованно, если оно
соответствует пункту 2 статьи 213.3 и статье 213.5, требования признаны
обоснованными, не удовлетворены гражданином на дату заседания и доказана
неплатёжеспособность гражданина.

Заявление **самого гражданина** обоснованно, если оно соответствует статье
213.4 и доказана неплатёжеспособность. Ни пункта 2 статьи 213.3, ни признания
требований обоснованными здесь нет — и это та же развилка, которую институт
возбуждения дела прочитал в оговорке пункта 2 статьи 213.3.

Соответствие статьям 213.3–213.5 модель не выводит заново: его выводит институт
возбуждения дела, и сверка фактов держит оба института на одном ответе.

Отдельное основание необоснованности — **спор о праве**: требование не
подтверждено вступившим в законную силу судебным актом, а между кредитором и
гражданином есть спор, разрешаемый в исковом порядке. Требование из перечня
пункта 2 статьи 213.5 даёт право подать заявление без решения суда, но не
делает заявление обоснованным, если гражданин требование оспаривает по
существу.

## Пункт 3 статьи 213.6: неплатёжеспособность гражданина

Определение дано «для целей настоящего параграфа», то есть для гражданина
своё, а не общее определение статьи 2: неспособность удовлетворить в полном
объёме требования кредиторов по денежным обязательствам и (или) исполнить
обязанность по уплате обязательных платежей.

Неплатёжеспособность **предполагается**, если не доказано иное, при хотя бы
одном из четырёх обстоятельств: гражданин прекратил расчёты с кредиторами;
более десяти процентов наступивших обязательств не исполнены дольше месяца;
задолженность превышает стоимость имущества; есть постановление об окончании
исполнительного производства из-за отсутствия имущества.

И презумпцию, и доказанную иными доказательствами неплатёжеспособность снимает
последний абзац пункта: если есть достаточные основания полагать, что гражданин
в течение непродолжительного времени исполнит наступившие обязательства в
полном объёме, он **не может быть признан** неплатёжеспособным. «Достаточные
основания» и «непродолжительное время» — оценочные понятия, и модель поднимает
флаг юриста всякий раз, когда это правило решает исход.

## Пункт 8 статьи 213.6 и пункт 1 статьи 213.13: реализация без реструктуризации

По умолчанию обоснованное заявление ведёт к реструктуризации. Сразу признать
гражданина банкротом и ввести реализацию имущества суд **вправе** только при
двух условиях: гражданин не соответствует требованиям для утверждения плана
реструктуризации (пункт 1 статьи 213.13) **и** сам об этом ходатайствует.

Требования к плану: источник дохода; нет неснятой или непогашенной судимости за
умышленное преступление в сфере экономики и истёк срок административного
наказания за мелкое хищение, умышленное уничтожение или повреждение имущества,
фиктивное или преднамеренное банкротство; гражданин не признавался банкротом в
течение пяти лет; план реструктуризации его долгов не утверждался в течение
восьми лет.

Ходатайство кредитора этого пути не открывает, и отсутствие дохода само по себе
тоже: без ходатайства гражданина вводится реструктуризация. «Вправе» — усмотрение
суда, поэтому открытый путь к реализации поднимает флаг юриста.

## Отсутствие имущества

Отсутствие имущества, которое после покрытия расходов на процедуру могло бы
пойти кредиторам, **не препятствует** введению реализации имущества (абзац,
введённый законом 289-ФЗ в 2020 году). Модель учитывает этот признак только для
того, чтобы назвать его безразличным: ни на обоснованность, ни на прекращение
производства он не влияет.

## Чего модель не делает

* **Не выводит соответствие заявления статьям 213.3–213.5** — его выводит
  институт возбуждения дела, а здесь оно сверяется.
* **Не считает доли и сроки:** десять процентов, месяц, пять и восемь лет —
  проверенные признаки рецензента.
* **Не разбирает план реструктуризации** (статьи 213.12–213.23) и мировое
  соглашение (статья 213.31): модель отвечает, какая процедура вводится, а не
  как она идёт.
* **Не разбирает сроки рассмотрения** (пункт 5), немедленное исполнение и
  приостановление производства (пункты 6 и 7), содержание определения
  (пункт 4).
* **Отвечает об одном заявлении** по одному делу.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

CITIZEN_PROCEDURE_EVIDENCE_SCHEMA_VERSION = "contracts.citizen-procedure-evidence.v0"
CITIZEN_PROCEDURE_MAPPING_VERSION = "contracts-reviewed-citizen-procedure-to-facts-v0"
CITIZEN_PROCEDURE_MODEL_VERSION = "contracts-citizen-procedure-articles-213-2-213-6-213-13-127fz-v0"

# Дословные тексты — synthetic_sources.py: статья 213.2 с перечнем процедур,
# статья 213.6 об обоснованности заявления и неплатёжеспособности гражданина,
# статья 213.13 с требованиями к плану реструктуризации и статья 213.1 — режим
# должника.
CITIZEN_PROCEDURE_LEGAL_SOURCE_REFS = (
    "synthetic-ru-127fz-213.2-citizen-bankruptcy-procedures-v1",
    "synthetic-ru-127fz-213.6-citizen-application-merits-v1",
    "synthetic-ru-127fz-213.13-restructuring-plan-requirements-v1",
    "synthetic-ru-127fz-213.1-citizen-bankruptcy-regulation-v1",
)


class CitizenProcedureEvidencePredicate(str, Enum):
    # --- Режим: тот же признак, что у остальных институтов главы X ---
    DEBTOR_IS_A_CITIZEN_UNDER_CHAPTER_10 = "debtor_is_a_citizen_under_chapter_10"

    # --- Чьё заявление проверяется ---
    APPLICATION_BY_THE_CITIZEN = "application_by_the_citizen"
    APPLICATION_BY_CREDITOR_OR_AUTHORISED_BODY = "application_by_creditor_or_authorised_body"
    # Заявление соответствует требованиям, которые пункт 2 статьи 213.6 называет
    # для своего заявителя: статье 213.4 — у гражданина, пункту 2 статьи 213.3 и
    # статье 213.5 — у кредитора. Выводит институт возбуждения дела; здесь —
    # сверяемый признак.
    APPLICATION_MEETS_ARTICLES_213_3_TO_213_5 = "application_meets_articles_213_3_to_213_5"

    # --- Требование кредитора: абзацы 1 и 4–5 пункта 2 статьи 213.6 ---
    CREDITOR_CLAIMS_FOUND_WELL_FOUNDED = "creditor_claims_found_well_founded"
    CREDITOR_CLAIMS_FOUND_UNFOUNDED = "creditor_claims_found_unfounded"
    # Гражданин удовлетворил требования к дате заседания.
    CREDITOR_CLAIMS_SATISFIED_BY_HEARING_DATE = "creditor_claims_satisfied_by_hearing_date"
    # Требование подтверждено вступившим в законную силу судебным актом.
    CLAIM_CONFIRMED_BY_COURT_DECISION_IN_FORCE = "claim_confirmed_by_court_decision_in_force"
    # Между кредитором и гражданином есть спор о праве, разрешаемый в исковом
    # порядке.
    DISPUTE_ABOUT_THE_RIGHT_FOR_ACTION_PROCEEDINGS = (
        "dispute_about_the_right_for_action_proceedings"
    )

    # --- Неплатёжеспособность гражданина: пункт 3 статьи 213.6 ---
    CITIZEN_STOPPED_PAYMENTS_TO_CREDITORS = "citizen_stopped_payments_to_creditors"
    OVER_TEN_PERCENT_OF_DUE_OBLIGATIONS_UNPAID_FOR_OVER_A_MONTH = (
        "over_ten_percent_of_due_obligations_unpaid_for_over_a_month"
    )
    DEBT_EXCEEDS_VALUE_OF_PROPERTY = "debt_exceeds_value_of_property"
    # Постановление об окончании исполнительного производства: имущества, на
    # которое может быть обращено взыскание, нет.
    ENFORCEMENT_ENDED_FOR_LACK_OF_PROPERTY = "enforcement_ended_for_lack_of_property"
    # «Если не доказано иное»: презумпция опровергнута.
    INSOLVENCY_PRESUMPTION_REBUTTED = "insolvency_presumption_rebutted"
    # Неспособность исполнить в полном объёме доказана иначе, чем презумпцией.
    INABILITY_TO_PAY_IN_FULL_SHOWN_BY_OTHER_EVIDENCE = (
        "inability_to_pay_in_full_shown_by_other_evidence"
    )
    # Достаточные основания полагать, что с учётом планируемых поступлений
    # гражданин в течение непродолжительного времени исполнит наступившие
    # обязательства в полном объёме.
    FULL_PERFORMANCE_EXPECTED_SHORTLY_FROM_PLANNED_RECEIPTS = (
        "full_performance_expected_shortly_from_planned_receipts"
    )

    # --- Иное заявление: абзацы 4 и 5 пункта 2 статьи 213.6 ---
    ANOTHER_APPLICATION_TO_DECLARE_THE_CITIZEN_BANKRUPT_PENDING = (
        "another_application_to_declare_the_citizen_bankrupt_pending"
    )

    # --- Требования к плану реструктуризации: пункт 1 статьи 213.13 ---
    CITIZEN_HAS_SOURCE_OF_INCOME = "citizen_has_source_of_income"
    # Неснятая или непогашенная судимость за умышленное экономическое
    # преступление либо не истёк срок административного наказания за мелкое
    # хищение, умышленное уничтожение или повреждение имущества, фиктивное или
    # преднамеренное банкротство.
    CONVICTION_OR_ADMINISTRATIVE_PENALTY_BARS_PLAN = (
        "conviction_or_administrative_penalty_bars_plan"
    )
    DECLARED_BANKRUPT_WITHIN_FIVE_YEARS = "declared_bankrupt_within_five_years"
    RESTRUCTURING_PLAN_APPROVED_WITHIN_EIGHT_YEARS = (
        "restructuring_plan_approved_within_eight_years"
    )

    # --- Пункт 8 статьи 213.6 ---
    CITIZEN_PETITIONS_FOR_IMMEDIATE_REALISATION = "citizen_petitions_for_immediate_realisation"

    # --- Абзац 3 пункта 2 статьи 213.6 ---
    RIGHTS_OF_MINOR_OR_INCAPACITATED_PERSON_AFFECTED = (
        "rights_of_minor_or_incapacitated_person_affected"
    )

    # --- Последний абзац пункта 2 статьи 213.6 ---
    NO_PROPERTY_LEFT_FOR_CREDITORS_AFTER_PROCEDURE_COSTS = (
        "no_property_left_for_creditors_after_procedure_costs"
    )


REQUIRED_CITIZEN_PROCEDURE_PREDICATES = frozenset(CitizenProcedureEvidencePredicate)

_CREDITOR_CLAIM_FACTS = (
    "creditor_claims_found_well_founded",
    "creditor_claims_found_unfounded",
    "creditor_claims_satisfied_by_hearing_date",
    "claim_confirmed_by_court_decision_in_force",
    "dispute_about_the_right_for_action_proceedings",
)

_PRESUMPTION_CIRCUMSTANCES = (
    "citizen_stopped_payments_to_creditors",
    "over_ten_percent_of_due_obligations_unpaid_for_over_a_month",
    "debt_exceeds_value_of_property",
    "enforcement_ended_for_lack_of_property",
)


class CitizenProcedureEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: CitizenProcedureEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedCitizenProcedureEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CITIZEN_PROCEDURE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[CitizenProcedureEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedCitizenProcedureEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Citizen-procedure evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Citizen-procedure evidence contains duplicate legal source refs.")
        return self


class CitizenProcedureFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    debtor_is_a_citizen_under_chapter_10: bool
    application_by_the_citizen: bool
    application_by_creditor_or_authorised_body: bool
    application_meets_articles_213_3_to_213_5: bool
    creditor_claims_found_well_founded: bool
    creditor_claims_found_unfounded: bool
    creditor_claims_satisfied_by_hearing_date: bool
    claim_confirmed_by_court_decision_in_force: bool
    dispute_about_the_right_for_action_proceedings: bool
    citizen_stopped_payments_to_creditors: bool
    over_ten_percent_of_due_obligations_unpaid_for_over_a_month: bool
    debt_exceeds_value_of_property: bool
    enforcement_ended_for_lack_of_property: bool
    insolvency_presumption_rebutted: bool
    inability_to_pay_in_full_shown_by_other_evidence: bool
    full_performance_expected_shortly_from_planned_receipts: bool
    another_application_to_declare_the_citizen_bankrupt_pending: bool
    citizen_has_source_of_income: bool
    conviction_or_administrative_penalty_bars_plan: bool
    declared_bankrupt_within_five_years: bool
    restructuring_plan_approved_within_eight_years: bool
    citizen_petitions_for_immediate_realisation: bool
    rights_of_minor_or_incapacitated_person_affected: bool
    no_property_left_for_creditors_after_procedure_costs: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "CitizenProcedureFactSet":
        if self.application_by_the_citizen and self.application_by_creditor_or_authorised_body:
            raise ValueError(
                "Проверяется одно заявление: гражданина либо кредитора (уполномоченного "
                "органа). Пункт 2 статьи 213.6 даёт им разные условия обоснованности, и "
                "каждое заявление разбирается отдельно."
            )
        if (
            any(getattr(self, name) for name in _CREDITOR_CLAIM_FACTS)
            and not self.application_by_creditor_or_authorised_body
        ):
            raise ValueError(
                "Обоснованность, удовлетворение, судебное подтверждение требования или спор "
                "о праве названы, а заявление подал не кредитор и не уполномоченный орган: "
                "эти условия пункт 2 статьи 213.6 ставит заявлению кредитора."
            )
        if self.creditor_claims_found_well_founded and self.creditor_claims_found_unfounded:
            raise ValueError(
                "Требование кредитора не может быть признано одновременно обоснованным и "
                "необоснованным."
            )
        if self.insolvency_presumption_rebutted and not any(
            getattr(self, name) for name in _PRESUMPTION_CIRCUMSTANCES
        ):
            raise ValueError(
                "Презумпция неплатёжеспособности названа опровергнутой, а ни одного из "
                "четырёх обстоятельств, на которых она держится (пункт 3 статьи 213.6), нет: "
                "опровергать нечего."
            )
        if (
            self.insolvency_presumption_rebutted
            and self.inability_to_pay_in_full_shown_by_other_evidence
        ):
            raise ValueError(
                "Презумпция неплатёжеспособности опровергнута — значит, доказано, что "
                "гражданин способен исполнить обязательства; одновременно доказать его "
                "неспособность иными доказательствами нельзя."
            )
        if self.citizen_petitions_for_immediate_realisation and not (
            self.application_by_the_citizen or self.application_by_creditor_or_authorised_body
        ):
            raise ValueError(
                "Ходатайство о признании банкротом и введении реализации имущества "
                "заявляется по результатам рассмотрения обоснованности заявления (пункт 8 "
                "статьи 213.6): без заявления ему не к чему относиться."
            )
        return self


class CitizenProcedureFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class CitizenProcedureEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: CitizenProcedureFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[CitizenProcedureFactProvenance] = Field(default_factory=list)


class CitizenProcedureConstraintSet(BaseModel):
    id: str
    model_version: str = CITIZEN_PROCEDURE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class CitizenProcedureEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    #: Хотя бы одно из четырёх обстоятельств презумпции пункта 3 статьи 213.6.
    insolvency_presumed: bool
    #: Неплатёжеспособность гражданина доказана (пункт 3 статьи 213.6).
    insolvency_established: bool
    #: Заявление признаётся обоснованным (пункт 2 статьи 213.6).
    application_well_founded: bool
    #: Заявление признаётся необоснованным.
    application_unfounded: bool
    #: Необоснованное заявление оставляется без рассмотрения: есть иное заявление.
    application_left_without_consideration: bool
    #: Производство по делу прекращается: иных заявлений нет.
    bankruptcy_proceedings_terminated: bool
    #: Гражданин соответствует требованиям к плану (пункт 1 статьи 213.13).
    citizen_meets_restructuring_plan_requirements: bool
    #: Суд вправе сразу признать гражданина банкротом и ввести реализацию
    #: имущества (пункт 8 статьи 213.6).
    realisation_may_be_introduced_without_restructuring: bool
    #: Вводится реструктуризация долгов гражданина (пункт 1 статьи 213.6).
    debt_restructuring_introduced: bool
    #: К участию в деле привлекается орган опеки и попечительства.
    guardianship_authority_joins_the_case: bool
    #: Отсутствие имущества названо и отброшено: введению реализации оно не
    #: препятствует.
    lack_of_property_disregarded: bool
    requires_human_citizen_procedure_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_citizen_procedure_evidence(
    evidence: ReviewedCitizenProcedureEvidence,
) -> CitizenProcedureEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Citizen-procedure evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Citizen-procedure evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_CITIZEN_PROCEDURE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed citizen-procedure evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_CITIZEN_PROCEDURE_PREDICATES
    }
    return CitizenProcedureEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CITIZEN_PROCEDURE_MAPPING_VERSION,
        facts=CitizenProcedureFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            CitizenProcedureFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_CITIZEN_PROCEDURE_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_citizen_procedure_constraint_set(
    mapping: CitizenProcedureEvidenceMappingResult,
) -> CitizenProcedureConstraintSet:
    return CitizenProcedureConstraintSet(
        id=f"citizen-procedure-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            (
                "insolvency_presumed == debtor_is_a_citizen_under_chapter_10 AND "
                "(citizen_stopped_payments_to_creditors OR "
                "over_ten_percent_of_due_obligations_unpaid_for_over_a_month OR "
                "debt_exceeds_value_of_property OR enforcement_ended_for_lack_of_property)"
            ),
            (
                "insolvency_established == debtor_is_a_citizen_under_chapter_10 AND "
                "((insolvency_presumed AND NOT insolvency_presumption_rebutted) OR "
                "inability_to_pay_in_full_shown_by_other_evidence) AND "
                "NOT full_performance_expected_shortly_from_planned_receipts"
            ),
            (
                "application_well_founded == debtor_is_a_citizen_under_chapter_10 AND "
                "application_meets_articles_213_3_to_213_5 AND insolvency_established AND "
                "(application_by_the_citizen OR (application_by_creditor_or_authorised_body "
                "AND creditor_claims_found_well_founded AND "
                "NOT creditor_claims_satisfied_by_hearing_date AND "
                "NOT (dispute_about_the_right_for_action_proceedings AND "
                "NOT claim_confirmed_by_court_decision_in_force)))"
            ),
            (
                "application_unfounded == debtor_is_a_citizen_under_chapter_10 AND "
                "(application_by_the_citizen OR application_by_creditor_or_authorised_body) "
                "AND NOT application_well_founded"
            ),
            (
                "application_left_without_consideration == application_unfounded AND "
                "another_application_to_declare_the_citizen_bankrupt_pending"
            ),
            (
                "bankruptcy_proceedings_terminated == application_unfounded AND "
                "NOT another_application_to_declare_the_citizen_bankrupt_pending"
            ),
            (
                "citizen_meets_restructuring_plan_requirements == "
                "debtor_is_a_citizen_under_chapter_10 AND citizen_has_source_of_income AND "
                "NOT conviction_or_administrative_penalty_bars_plan AND "
                "NOT declared_bankrupt_within_five_years AND "
                "NOT restructuring_plan_approved_within_eight_years"
            ),
            (
                "realisation_may_be_introduced_without_restructuring == "
                "application_well_founded AND citizen_petitions_for_immediate_realisation AND "
                "NOT citizen_meets_restructuring_plan_requirements"
            ),
            (
                "debt_restructuring_introduced == application_well_founded AND "
                "NOT realisation_may_be_introduced_without_restructuring"
            ),
            (
                "guardianship_authority_joins_the_case == application_well_founded AND "
                "rights_of_minor_or_incapacitated_person_affected"
            ),
            (
                "lack_of_property_disregarded == debtor_is_a_citizen_under_chapter_10 AND "
                "(application_by_the_citizen OR application_by_creditor_or_authorised_body) "
                "AND no_property_left_for_creditors_after_procedure_costs"
            ),
            (
                "requires_human_citizen_procedure_assessment == "
                "realisation_may_be_introduced_without_restructuring OR "
                "(debtor_is_a_citizen_under_chapter_10 AND "
                "(insolvency_presumption_rebutted OR "
                "inability_to_pay_in_full_shown_by_other_evidence OR "
                "(full_performance_expected_shortly_from_planned_receipts AND "
                "(insolvency_presumed OR inability_to_pay_in_full_shown_by_other_evidence))))"
            ),
        ],
    )


def evaluate_citizen_procedure_constraints(
    constraint_set: CitizenProcedureConstraintSet,
    facts: CitizenProcedureFactSet,
) -> CitizenProcedureEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in CitizenProcedureFactSet.model_fields
    }
    insolvency_presumed = Bool("insolvency_presumed")
    insolvency_established = Bool("insolvency_established")
    application_well_founded = Bool("application_well_founded")
    application_unfounded = Bool("application_unfounded")
    application_left_without_consideration = Bool("application_left_without_consideration")
    bankruptcy_proceedings_terminated = Bool("bankruptcy_proceedings_terminated")
    citizen_meets_restructuring_plan_requirements = Bool(
        "citizen_meets_restructuring_plan_requirements"
    )
    realisation_may_be_introduced_without_restructuring = Bool(
        "realisation_may_be_introduced_without_restructuring"
    )
    debt_restructuring_introduced = Bool("debt_restructuring_introduced")
    guardianship_authority_joins_the_case = Bool("guardianship_authority_joins_the_case")
    lack_of_property_disregarded = Bool("lack_of_property_disregarded")
    requires_human_citizen_procedure_assessment = Bool(
        "requires_human_citizen_procedure_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    # Ворота: процедуры статьи 213.2 — процедуры главы X, и вне её режима
    # институт молчит.
    citizen = variables["debtor_is_a_citizen_under_chapter_10"]
    application_filed = Or(
        variables["application_by_the_citizen"],
        variables["application_by_creditor_or_authorised_body"],
    )

    # Пункт 3 статьи 213.6: четыре обстоятельства презумпции, «хотя бы одно».
    solver.add(
        insolvency_presumed
        == And(
            citizen,
            Or(
                variables["citizen_stopped_payments_to_creditors"],
                variables["over_ten_percent_of_due_obligations_unpaid_for_over_a_month"],
                variables["debt_exceeds_value_of_property"],
                variables["enforcement_ended_for_lack_of_property"],
            ),
        )
    )
    # Последний абзац пункта 3 снимает и презумпцию, и иные доказательства:
    # «не может быть признан неплатежеспособным».
    solver.add(
        insolvency_established
        == And(
            citizen,
            Or(
                And(insolvency_presumed, Not(variables["insolvency_presumption_rebutted"])),
                variables["inability_to_pay_in_full_shown_by_other_evidence"],
            ),
            Not(variables["full_performance_expected_shortly_from_planned_receipts"]),
        )
    )
    # Пункт 2 статьи 213.6: у гражданина — статья 213.4 и неплатёжеспособность;
    # у кредитора — ещё обоснованность требований, их неудовлетворение к дате
    # заседания и отсутствие спора о праве по неподтверждённому требованию.
    solver.add(
        application_well_founded
        == And(
            citizen,
            variables["application_meets_articles_213_3_to_213_5"],
            insolvency_established,
            Or(
                variables["application_by_the_citizen"],
                And(
                    variables["application_by_creditor_or_authorised_body"],
                    variables["creditor_claims_found_well_founded"],
                    Not(variables["creditor_claims_satisfied_by_hearing_date"]),
                    Not(
                        And(
                            variables["dispute_about_the_right_for_action_proceedings"],
                            Not(variables["claim_confirmed_by_court_decision_in_force"]),
                        )
                    ),
                ),
            ),
        )
    )
    # Пункт 1 закрывает перечень определений: необоснованное заявление получает
    # одно из двух, и выбор решает иное заявление.
    solver.add(
        application_unfounded == And(citizen, application_filed, Not(application_well_founded))
    )
    solver.add(
        application_left_without_consideration
        == And(
            application_unfounded,
            variables["another_application_to_declare_the_citizen_bankrupt_pending"],
        )
    )
    solver.add(
        bankruptcy_proceedings_terminated
        == And(
            application_unfounded,
            Not(variables["another_application_to_declare_the_citizen_bankrupt_pending"]),
        )
    )
    # Пункт 1 статьи 213.13: четыре требования через «и».
    solver.add(
        citizen_meets_restructuring_plan_requirements
        == And(
            citizen,
            variables["citizen_has_source_of_income"],
            Not(variables["conviction_or_administrative_penalty_bars_plan"]),
            Not(variables["declared_bankrupt_within_five_years"]),
            Not(variables["restructuring_plan_approved_within_eight_years"]),
        )
    )
    # Пункт 8 статьи 213.6: несоответствие требованиям и ходатайство гражданина —
    # оба; суд «вправе».
    solver.add(
        realisation_may_be_introduced_without_restructuring
        == And(
            application_well_founded,
            variables["citizen_petitions_for_immediate_realisation"],
            Not(citizen_meets_restructuring_plan_requirements),
        )
    )
    solver.add(
        debt_restructuring_introduced
        == And(
            application_well_founded,
            Not(realisation_may_be_introduced_without_restructuring),
        )
    )
    solver.add(
        guardianship_authority_joins_the_case
        == And(
            application_well_founded,
            variables["rights_of_minor_or_incapacitated_person_affected"],
        )
    )
    # Отсутствие имущества названо, чтобы быть отброшенным: ни в одно правило
    # выше оно не входит.
    solver.add(
        lack_of_property_disregarded
        == And(
            citizen,
            application_filed,
            variables["no_property_left_for_creditors_after_procedure_costs"],
        )
    )
    solver.add(
        requires_human_citizen_procedure_assessment
        == Or(
            realisation_may_be_introduced_without_restructuring,
            And(
                citizen,
                Or(
                    variables["insolvency_presumption_rebutted"],
                    variables["inability_to_pay_in_full_shown_by_other_evidence"],
                    And(
                        variables["full_performance_expected_shortly_from_planned_receipts"],
                        Or(
                            insolvency_presumed,
                            variables["inability_to_pay_in_full_shown_by_other_evidence"],
                        ),
                    ),
                ),
            ),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return CitizenProcedureEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            insolvency_presumed=False,
            insolvency_established=False,
            application_well_founded=False,
            application_unfounded=False,
            application_left_without_consideration=False,
            bankruptcy_proceedings_terminated=False,
            citizen_meets_restructuring_plan_requirements=False,
            realisation_may_be_introduced_without_restructuring=False,
            debt_restructuring_introduced=False,
            guardianship_authority_joins_the_case=False,
            lack_of_property_disregarded=False,
            requires_human_citizen_procedure_assessment=True,
            reasons_ru=[
                "Набор фактов об обоснованности заявления и процедуре банкротства "
                "гражданина противоречив."
            ],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru: list[str] = []
    if truth(insolvency_presumed):
        reasons_ru.append(
            "Гражданин предполагается неплатёжеспособным: есть хотя бы одно из четырёх "
            "обстоятельств пункта 3 статьи 213.6 закона 127-ФЗ — прекращение расчётов, "
            "просрочка более десяти процентов наступивших обязательств дольше месяца, "
            "превышение задолженности над стоимостью имущества или окончание "
            "исполнительного производства из-за отсутствия имущества."
        )
    if truth(citizen) and truth(variables["insolvency_presumption_rebutted"]):
        reasons_ru.append(
            "Презумпция неплатёжеспособности опровергнута: доказано иное, и признать "
            "гражданина неплатёжеспособным на её основании нельзя."
        )
    if truth(insolvency_established):
        basis = (
            "доказана иными доказательствами"
            if truth(variables["inability_to_pay_in_full_shown_by_other_evidence"])
            else "следует из презумпции, которая не опровергнута"
        )
        reasons_ru.append(
            "Неплатёжеспособность гражданина — неспособность удовлетворить в полном "
            "объёме требования кредиторов и (или) исполнить обязанность по уплате "
            f"обязательных платежей — {basis} (пункт 3 статьи 213.6)."
        )
    if (
        truth(citizen)
        and truth(variables["full_performance_expected_shortly_from_planned_receipts"])
        and (
            truth(insolvency_presumed)
            or truth(variables["inability_to_pay_in_full_shown_by_other_evidence"])
        )
    ):
        reasons_ru.append(
            "Гражданин не может быть признан неплатёжеспособным: есть достаточные "
            "основания полагать, что с учётом планируемых поступлений он в течение "
            "непродолжительного времени исполнит наступившие обязательства в полном "
            "объёме (последний абзац пункта 3 статьи 213.6). Достаточность оснований и "
            "срок оценивает суд."
        )
    if truth(application_well_founded):
        if truth(variables["application_by_the_citizen"]):
            ground = "оно соответствует статье 213.4 и неплатёжеспособность доказана"
        else:
            ground = (
                "оно соответствует пункту 2 статьи 213.3 и статье 213.5, требования "
                "признаны обоснованными и не удовлетворены к дате заседания, и "
                "неплатёжеспособность доказана"
            )
        reasons_ru.append(
            f"Заявление о признании гражданина банкротом обоснованно: {ground} (пункт 2 "
            "статьи 213.6)."
        )
    if truth(application_unfounded):
        grounds = []
        if not truth(variables["application_meets_articles_213_3_to_213_5"]):
            grounds.append(
                "заявление не соответствует условиям статей 213.3–213.5, которые пункт 2 "
                "статьи 213.6 называет для его заявителя"
            )
        if not truth(insolvency_established):
            grounds.append("неплатёжеспособность гражданина не доказана")
        if truth(variables["application_by_creditor_or_authorised_body"]):
            if truth(variables["creditor_claims_found_unfounded"]):
                grounds.append("требования кредитора признаны необоснованными")
            elif not truth(variables["creditor_claims_found_well_founded"]):
                grounds.append("требования кредитора обоснованными не признаны")
            if truth(variables["creditor_claims_satisfied_by_hearing_date"]):
                grounds.append("требования удовлетворены к дате заседания")
            if truth(variables["dispute_about_the_right_for_action_proceedings"]) and not truth(
                variables["claim_confirmed_by_court_decision_in_force"]
            ):
                grounds.append(
                    "требование не подтверждено вступившим в законную силу судебным актом, "
                    "а между кредитором и гражданином есть спор о праве, разрешаемый в "
                    "исковом порядке"
                )
        outcome = (
            "оставляется без рассмотрения: есть иное заявление о признании гражданина банкротом"
            if truth(application_left_without_consideration)
            else "влечёт прекращение производства по делу: иных заявлений нет"
        )
        reasons_ru.append(
            "Заявление о признании гражданина банкротом необоснованно ("
            + "; ".join(grounds)
            + f") и {outcome} (пункты 1 и 2 статьи 213.6)."
        )
    if truth(lack_of_property_disregarded):
        reasons_ru.append(
            "Отсутствие у гражданина имущества, которое после покрытия расходов на "
            "процедуру могло бы пойти кредиторам, не препятствует введению реализации "
            "имущества (последний абзац пункта 2 статьи 213.6) и на выводы модели не "
            "влияет."
        )
    if truth(application_well_founded):
        if truth(citizen_meets_restructuring_plan_requirements):
            reasons_ru.append(
                "Гражданин соответствует требованиям к плану реструктуризации пункта 1 "
                "статьи 213.13: есть источник дохода, нет препятствующей судимости или "
                "административного наказания, он не признавался банкротом пять лет и план "
                "не утверждался восемь лет."
            )
        if truth(realisation_may_be_introduced_without_restructuring):
            reasons_ru.append(
                "Суд вправе по ходатайству гражданина сразу признать его банкротом и ввести "
                "реализацию имущества: гражданин не соответствует требованиям к плану "
                "реструктуризации пункта 1 статьи 213.13 (пункт 8 статьи 213.6). «Вправе» — "
                "усмотрение суда, и модель не решает, воспользуется ли он им."
            )
        elif truth(debt_restructuring_introduced):
            if truth(variables["citizen_petitions_for_immediate_realisation"]):
                tail = (
                    " Ходатайство гражданина о реализации имущества пункт 8 удовлетворить не "
                    "позволяет: требованиям к плану реструктуризации гражданин соответствует."
                )
            elif not truth(citizen_meets_restructuring_plan_requirements):
                tail = (
                    " Требованиям к плану гражданин не соответствует, но без его ходатайства "
                    "пункт 8 к реализации не ведёт: ни ходатайство кредитора, ни само "
                    "несоответствие этого пути не открывают."
                )
            else:
                tail = ""
            reasons_ru.append(
                "Вводится реструктуризация долгов гражданина (пункт 1 статьи 213.6)." + tail
            )
    if truth(guardianship_authority_joins_the_case):
        reasons_ru.append(
            "К участию в деле привлекается орган опеки и попечительства: затрагиваются "
            "права несовершеннолетнего или лица, признанного судом недееспособным "
            "(абзац третий пункта 2 статьи 213.6)."
        )
    if truth(requires_human_citizen_procedure_assessment):
        reasons_ru.append(
            "Требуется оценка юриста: опровержение презумпции, доказанность "
            "неплатёжеспособности иными доказательствами, ожидание скорого исполнения и "
            "усмотрение суда по пункту 8 модель не устанавливает, а называет."
        )
    return CitizenProcedureEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        insolvency_presumed=truth(insolvency_presumed),
        insolvency_established=truth(insolvency_established),
        application_well_founded=truth(application_well_founded),
        application_unfounded=truth(application_unfounded),
        application_left_without_consideration=truth(application_left_without_consideration),
        bankruptcy_proceedings_terminated=truth(bankruptcy_proceedings_terminated),
        citizen_meets_restructuring_plan_requirements=truth(
            citizen_meets_restructuring_plan_requirements
        ),
        realisation_may_be_introduced_without_restructuring=truth(
            realisation_may_be_introduced_without_restructuring
        ),
        debt_restructuring_introduced=truth(debt_restructuring_introduced),
        guardianship_authority_joins_the_case=truth(guardianship_authority_joins_the_case),
        lack_of_property_disregarded=truth(lack_of_property_disregarded),
        requires_human_citizen_procedure_assessment=truth(
            requires_human_citizen_procedure_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Соответствие заявления статьям 213.3–213.5 модель не выводит, а принимает и "
            "сверяет с институтом возбуждения дела.",
            "Десять процентов, месяц, пять и восемь лет — проверенные признаки "
            "рецензента, а не вычисления: денежных величин и дат в фактах модели нет.",
            "Мировое соглашение (статья 213.31) и ход реструктуризации и реализации "
            "имущества модель не разбирает: она отвечает, какая процедура вводится по "
            "результатам проверки обоснованности заявления.",
            "Определение неплатёжеспособности пункта 3 статьи 213.6 дано «для целей "
            "настоящего параграфа»; что статьи 213.4 и 213.6 стоят в одном параграфе "
            "главы X, взято не из локальной выгрузки — разбивки на параграфы в ней нет.",
        ],
    )
