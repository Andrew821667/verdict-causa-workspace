"""Фабулы, привязанные к опубликованным разъяснениям Верховного Суда РФ.

Отличие от `case_scenarios`: там ожидаемый итог выведен из текста ГК мной, здесь
— взят из опубликованной правовой позиции высшей судебной инстанции. Это
следующий уровень независимости ожиданий: система сверяется не с рассуждением
автора модели, а с тем, что суд уже сказал.

**Важное ограничение, влияющее на доверие к набору.** Сетевая политика среды
разрешает поиск, но блокирует загрузку страниц: `WebFetch` отклонён для всех
проверенных правовых источников (`consultant.ru`, `garant.ru`, `vsrf.ru`,
`sudact.ru`, `legalacts.ru`, `pravo.gov.ru`, `government.ru`) и даже для
`en.wikipedia.org`. Тексты позиций получены из выдачи поиска и **не сверены с
первоисточником постранично**. Поэтому каждая фабула несёт поле
`verification`, честно фиксирующее это состояние, а тест требует, чтобы поле
было заполнено и указывало на источник.

Номер пункта в позиции о незаключённости выдача поиска назвала неуверенно
(«пункт 5 или 6»), и это записано в самой фабуле, а не сглажено.

Это не материалы судебных дел: доступ к картотекам арбитражных дел из среды
закрыт. Это опубликованные разъяснения — более слабый, но проверяемый по ссылке
источник ожиданий.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.case_scenarios import _flip
from causa.institutional.contracts.reviewed_analysis import (
    ReviewedContractAnalysisResult,
    run_reviewed_contract_analysis,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)

PRACTICE_SCENARIO_SUITE_VERSION = "contracts-practice-scenarios-v0"

#: Состояние проверки источника. Загрузка страниц в среде заблокирована.
SOURCE_UNVERIFIED_FETCH_BLOCKED = (
    "Текст позиции получен из выдачи поиска; постраничная сверка с "
    "первоисточником невозможна: сетевая политика среды блокирует загрузку "
    "правовых сайтов."
)


class PracticeScenario(BaseModel):
    id: str
    title_ru: str
    #: Опубликованная правовая позиция, из которой выведен ожидаемый итог.
    position_ru: str
    #: Акт и пункт.
    source_ru: str
    source_url: str
    verification: str
    fabula_ru: str
    evidence_overrides: dict[str, dict[str, bool]]
    expected_outcomes: dict[str, bool]


class PracticeScenarioResult(BaseModel):
    scenario_id: str
    title_ru: str
    source_ru: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    mismatched: list[str] = Field(default_factory=list)


class PracticeScenarioReport(BaseModel):
    id: str = "practice-scenario-report-v0"
    suite_version: str = PRACTICE_SCENARIO_SUITE_VERSION
    total: int
    passed: int
    failed: int
    results: list[PracticeScenarioResult] = Field(default_factory=list)


_PLENUM_25 = "https://www.consultant.ru/document/cons_doc_LAW_181602/"
_PLENUM_49 = "https://www.consultant.ru/document/cons_doc_LAW_314779/"
_PLENUM_10_22 = "https://www.consultant.ru/document/cons_doc_LAW_100466/"

#: Обязательство отсутствует: договорный эффект вытеснен.
_NO_DUTY = {
    "case_evidence": {
        "duty_exists": False,
        "performance_completed": False,
        "performance_nonconforming": False,
        "payment_duty_exists": False,
        "payment_due": False,
        "payment_missed": False,
        "loss_claimed": False,
        "causation_established": False,
        "remedy_requested": False,
    },
    "obligation_dynamics_evidence": {
        "obligation_exists": False,
        "obligation_breached": False,
        "accrued_claims_exist": False,
        "performance_rendered": False,
        "performance_accepted_as_proper": False,
        "performance_partial": False,
        "creditor_issued_receipt": False,
    },
    "performance_remedies_evidence": {
        "obligation_exists": False,
        "breach_established": False,
        "performance_tendered": False,
        "partial_performance_tendered": False,
        "early_performance_tendered": False,
    },
    "sale_evidence": {"goods_transfer_completed": False},
    "supply_evidence": {"delivery_completed": False},
    "security_evidence": {"main_obligation_invalid": True, "main_obligation_breached": False},
    "liability_evidence": {
        "breach_established": False,
        "intentional_breach": False,
        "penalty_claimed": False,
        "penalty_reduction_requested": False,
    },
}


def _merge(*layers: dict[str, dict[str, bool]]) -> dict[str, dict[str, bool]]:
    merged: dict[str, dict[str, bool]] = {}
    for layer in layers:
        for field, updates in layer.items():
            merged.setdefault(field, {}).update(updates)
    return merged


PRACTICE_SCENARIOS = (
    PracticeScenario(
        id="practice-abuse-refusal-of-protection",
        title_ru="Недобросовестное поведение стороны: отказ в защите права",
        position_ru=(
            "Если будет установлено недобросовестное поведение одной из сторон, суд в "
            "зависимости от обстоятельств дела и с учётом характера и последствий такого "
            "поведения отказывает в защите принадлежащего ей права полностью или частично."
        ),
        source_ru="Постановление Пленума ВС РФ от 23.06.2015 № 25, пункт 1",
        source_url=_PLENUM_25,
        verification=SOURCE_UNVERIFIED_FETCH_BLOCKED,
        fabula_ru=(
            "По договору поставки установлено заведомо недобросовестное осуществление "
            "права стороной, заявившей требование."
        ),
        evidence_overrides={
            "civil_principles_evidence": {
                "civil_rights_exercise_asserted": True,
                "abuse_of_right_established": True,
            }
        },
        expected_outcomes={
            # Отказ в защите, но сделка не порочится.
            "general_effects_evaluation.protection_refused_for_abuse": True,
            "general_effects_evaluation.contractual_claims_enforceable": False,
            "general_effects_evaluation.contract_legally_effective": True,
            "requires_human_resolution": True,
        },
    ),
    PracticeScenario(
        id="practice-unauthorized-act-refusal-against-principal",
        title_ru="Сделка неуполномоченного лица: отказ в иске к представляемому",
        position_ru=(
            "Установление факта заключения сделки представителем без полномочий или с "
            "превышением таковых служит основанием для отказа в иске, вытекающем из этой "
            "сделки, к представляемому, если только не будет доказано, что последний "
            "одобрил данную сделку."
        ),
        source_ru="Постановление Пленума ВС РФ от 23.06.2015 № 25, пункт 123",
        source_url=_PLENUM_25,
        verification=SOURCE_UNVERIFIED_FETCH_BLOCKED,
        fabula_ru=(
            "Договор подписан лицом без полномочий; доказательств одобрения сделки "
            "представляемым не представлено."
        ),
        evidence_overrides={
            "representation_evidence": {
                "representation_relation_established": True,
                "unauthorized_act_without_ratification": True,
            }
        },
        expected_outcomes={
            "general_effects_evaluation.unauthorized_representation_displaces_contract": True,
            "general_effects_evaluation.contract_legally_effective": False,
            "general_effects_evaluation.contractual_claims_enforceable": False,
            "requires_human_resolution": True,
        },
    ),
    PracticeScenario(
        id="practice-mutual-restitution-presumed-equal",
        title_ru="Недействительная сделка исполнена обеими сторонами: реституция",
        position_ru=(
            "По смыслу пункта 2 статьи 167 ГК РФ взаимные предоставления по "
            "недействительной сделке, которая была исполнена обеими сторонами, считаются "
            "равными, пока не доказано иное."
        ),
        source_ru="Постановление Пленума ВС РФ от 23.06.2015 № 25, пункт 80",
        source_url=_PLENUM_25,
        verification=SOURCE_UNVERIFIED_FETCH_BLOCKED,
        fabula_ru=(
            "Сделка совершена с целью, противной основам правопорядка и нравственности, "
            "обе стороны действовали умышленно и произвели встречное исполнение."
        ),
        evidence_overrides=_merge(
            {
                "invalidity_evidence": {
                    "transaction_concluded": True,
                    "immoral_purpose_proven": True,
                    "both_parties_intentional_immoral_purpose": True,
                    "party_a_performed": True,
                    "party_b_performed": True,
                }
            },
            _NO_DUTY,
        ),
        expected_outcomes={
            "general_effects_evaluation.invalidity_displaces_contract": True,
            "general_effects_evaluation.restitution_regime_applies": True,
            "general_effects_evaluation.contract_legally_effective": False,
            "requires_human_resolution": True,
        },
    ),
    PracticeScenario(
        id="practice-estoppel-against-non-conclusion-objection",
        title_ru="Принявшая исполнение сторона не вправе ссылаться на незаключённость",
        position_ru=(
            "Если сторона приняла от другой стороны полное или частичное исполнение по "
            "договору либо иным образом подтвердила действие договора, она не вправе "
            "недобросовестно ссылаться на то, что договор является незаключённым "
            "(пункт 3 статьи 432 ГК РФ)."
        ),
        source_ru=(
            "Постановление Пленума ВС РФ от 25.12.2018 № 49; выдача поиска назвала пункт "
            "неуверенно — «пункт 5 или 6», номер не подтверждён"
        ),
        source_url=_PLENUM_49,
        verification=SOURCE_UNVERIFIED_FETCH_BLOCKED,
        fabula_ru=(
            "Сторона приняла исполнение без возражений, а затем недобросовестно заявила "
            "о незаключённости договора."
        ),
        evidence_overrides={
            "formation_evidence": {
                "performance_accepted_without_objection": True,
                "bad_faith_non_conclusion_objection": True,
            }
        },
        expected_outcomes={
            "formation_evaluation.non_conclusion_objection_barred": True,
            "general_effects_evaluation.contract_legally_effective": True,
            "general_effects_evaluation.contractual_claims_enforceable": True,
        },
    ),
    PracticeScenario(
        id="practice-missing-consent-is-voidable-only",
        title_ru="Отсутствие необходимого согласия делает сделку оспоримой",
        position_ru=(
            "При отсутствии необходимого в силу закона согласия сделка может быть "
            "оспорена по правилам статьи 173.1 ГК РФ."
        ),
        source_ru="Постановление Пленума ВС РФ от 23.06.2015 № 25, разъяснения о согласии на совершение сделки (статьи 157.1 и 173.1 ГК РФ)",
        source_url=_PLENUM_25,
        verification=SOURCE_UNVERIFIED_FETCH_BLOCKED,
        fabula_ru=(
            "На совершение сделки требовалось согласие третьего лица; согласие получено не было."
        ),
        evidence_overrides={
            "transactions_evidence": {
                "transaction_asserted": True,
                "statutory_consent_not_obtained": True,
            },
            "invalidity_evidence": {"transaction_concluded": True, "required_consent_absent": True},
        },
        expected_outcomes={
            # Оспоримость, а не ничтожность: договор действует до решения суда.
            "general_effects_evaluation.transaction_challengeable_for_missing_consent": True,
            "general_effects_evaluation.contract_legally_effective": True,
            "general_effects_evaluation.contractual_claims_enforceable": True,
            "requires_human_resolution": True,
        },
    ),
    PracticeScenario(
        id="practice-invalidity-alone-does-not-prove-loss-of-possession",
        title_ru="Недействительность сама по себе не означает выбытия имущества помимо воли",
        position_ru=(
            "Недействительность сделки, во исполнение которой передано имущество, не "
            "свидетельствует сама по себе о его выбытии из владения передавшего это "
            "имущество лица помимо его воли."
        ),
        source_ru="Постановление Пленума ВС РФ № 10 и Пленума ВАС РФ № 22 от 29.04.2010, пункт 39",
        source_url=_PLENUM_10_22,
        verification=SOURCE_UNVERIFIED_FETCH_BLOCKED,
        fabula_ru=(
            "Сделка недействительна, но возражений о распоряжении имуществом "
            "неуправомоченным лицом не заявлено."
        ),
        evidence_overrides=_merge(
            {
                "invalidity_evidence": {
                    "transaction_concluded": True,
                    "immoral_purpose_proven": True,
                    "both_parties_intentional_immoral_purpose": True,
                }
            },
            _NO_DUTY,
        ),
        expected_outcomes={
            "general_effects_evaluation.invalidity_displaces_contract": True,
            # Проверка на отсутствие лишнего вывода: титул не должен опровергаться
            # автоматически из одной лишь недействительности.
            "general_effects_evaluation.title_transfer_defeated": False,
            "property_rights_evaluation.unauthorized_disposal_detected": False,
        },
    ),
)


def run_practice_scenario(scenario: PracticeScenario) -> ReviewedContractAnalysisResult:
    request = build_synthetic_supply_analysis_request()
    updates = {
        field: _flip(getattr(request, field), predicate_values)
        for field, predicate_values in scenario.evidence_overrides.items()
    }
    return run_reviewed_contract_analysis(
        request.model_copy(update=updates) if updates else request,
        build_synthetic_supply_analysis_sources(),
    )


def _read(result: ReviewedContractAnalysisResult, path: str) -> bool:
    target = result
    for part in path.split("."):
        target = getattr(target, part)
    return bool(target)


def run_practice_scenario_suite() -> PracticeScenarioReport:
    results = []
    for scenario in PRACTICE_SCENARIOS:
        result = run_practice_scenario(scenario)
        observed = {name: _read(result, name) for name in scenario.expected_outcomes}
        mismatched = sorted(
            name for name, value in scenario.expected_outcomes.items() if observed[name] != value
        )
        results.append(
            PracticeScenarioResult(
                scenario_id=scenario.id,
                title_ru=scenario.title_ru,
                source_ru=scenario.source_ru,
                passed=not mismatched,
                expected_outcomes=scenario.expected_outcomes,
                observed_outcomes=observed,
                mismatched=mismatched,
            )
        )
    passed = sum(item.passed for item in results)
    return PracticeScenarioReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )
