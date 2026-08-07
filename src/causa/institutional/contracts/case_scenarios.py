"""Смоделированные фабулы дел и сквозная проверка анализа на них.

Benchmark и red-team проверяют один институт в отрыве от остальных: один-два
переключённых факта и ожидаемый вывод той же модели. Этого недостаточно, чтобы
судить о системе: юрист приносит не отдельный факт, а связную фабулу, в которой
одновременно действуют несколько институтов.

Здесь смоделированы полные фабулы. Каждая проходит через
`run_reviewed_contract_analysis` целиком, и проверяется не вывод одной модели, а
итог всего анализа: действует ли договор, исполнимы ли требования, вытеснены ли
выводы специальных институтов, поднят ли флаг экспертизы.

Ожидаемый результат каждой фабулы выведен из закона до запуска системы и
записан в поле `legal_basis_ru`. Совпадение вывода системы с ним — предмет
проверки, а не источник ожиданий.

Фабулы согласованы внутри себя: рецензент, готовя дело, обязан отразить один и
тот же факт одинаково во всех институтах и привести в соответствие
существование обязательства (`duty_exists`, `obligation_exists`) с выводами о
заключённости и действительности. Слой сверки следит за первым, прежние
проверки входов — за вторым.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.reviewed_analysis import (
    ReviewedContractAnalysisResult,
    run_reviewed_contract_analysis,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)

CASE_SCENARIO_SUITE_VERSION = "contracts-case-scenarios-v0"


class CaseScenario(BaseModel):
    id: str
    title_ru: str
    fabula_ru: str
    legal_basis_ru: str
    #: {поле запроса: {предикат: значение}}
    evidence_overrides: dict[str, dict[str, bool]]
    #: Ожидаемые значения полей итогового анализа и слоёв.
    expected_outcomes: dict[str, bool]


class CaseScenarioResult(BaseModel):
    scenario_id: str
    title_ru: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    mismatched: list[str] = Field(default_factory=list)
    reasons_ru: list[str] = Field(default_factory=list)


class CaseScenarioReport(BaseModel):
    id: str = "case-scenario-report-v0"
    suite_version: str = CASE_SCENARIO_SUITE_VERSION
    total: int
    passed: int
    failed: int
    results: list[CaseScenarioResult] = Field(default_factory=list)


#: Факты обязательства при вытеснении договорного эффекта: обязанности нет.
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
    "security_evidence": {
        "main_obligation_invalid": True,
        "main_obligation_breached": False,
    },
    "liability_evidence": {
        "breach_established": False,
        "intentional_breach": False,
        "penalty_claimed": False,
        "penalty_reduction_requested": False,
    },
}

#: Истёкшая и заявленная исковая давность (статьи 196 и 199 ГК РФ).
_LIMITATION_ELAPSED = {
    "claim_subject_to_limitation": True,
    "right_violation_and_defendant_known": True,
    "general_three_year_term_elapsed": True,
    "limitation_pleaded_by_party_before_judgment": True,
}


def _merge(*layers: dict[str, dict[str, bool]]) -> dict[str, dict[str, bool]]:
    merged: dict[str, dict[str, bool]] = {}
    for layer in layers:
        for field, updates in layer.items():
            merged.setdefault(field, {}).update(updates)
    return merged


CASE_SCENARIOS = (
    CaseScenario(
        id="scenario-supply-breach-enforceable",
        title_ru="Просрочка поставки, спор рассматривается по существу",
        fabula_ru=(
            "Поставщик просрочил поставку партии товара. Возражений о "
            "недействительности, форме, давности и полномочиях не заявлено."
        ),
        legal_basis_ru=(
            "Договор заключён и действует (статья 432 ГК РФ), оснований для отказа в защите "
            "нет, поэтому требования из договора рассматриваются по существу."
        ),
        evidence_overrides={},
        expected_outcomes={
            "general_effects_evaluation.contract_legally_effective": True,
            "general_effects_evaluation.contractual_claims_enforceable": True,
            "general_effects_evaluation.institute_conclusions_displaced": False,
            "general_consistency_evaluation.contradictions_detected": False,
            "requires_human_resolution": False,
        },
    ),
    CaseScenario(
        id="scenario-limitation-barred",
        title_ru="Истёкшая исковая давность заявлена ответчиком",
        fabula_ru=(
            "Нарушение установлено, но ответчик до вынесения решения заявил о применении "
            "исковой давности; общий трёхлетний срок истёк."
        ),
        legal_basis_ru=(
            "Истечение срока исковой давности, о применении которой заявлено стороной, — "
            "самостоятельное основание к отказу в иске (статья 199 ГК РФ). Договор при этом "
            "остаётся действительным."
        ),
        evidence_overrides={"limitation_evidence": _LIMITATION_ELAPSED},
        expected_outcomes={
            "general_effects_evaluation.contract_legally_effective": True,
            "general_effects_evaluation.claims_barred_by_limitation": True,
            "general_effects_evaluation.contractual_claims_enforceable": False,
            "general_effects_evaluation.breach_findings_without_effect": True,
            "requires_human_resolution": True,
        },
    ),
    CaseScenario(
        id="scenario-limitation-defective-calculation",
        title_ru="Давность заявлена, но срок исчислен с нарушением главы 11",
        fabula_ru=(
            "Ответчик заявил о давности, однако начало течения срока и его окончание "
            "определены с нарушением правил об исчислении сроков."
        ),
        legal_basis_ru=(
            "Срок исковой давности исчисляется по общим правилам главы 11 ГК РФ "
            "(статьи 190–194), поэтому при пороке исчисления истечение срока не считается "
            "установленным и не может обосновать отказ в иске (статья 199 ГК РФ)."
        ),
        evidence_overrides={
            "limitation_evidence": _LIMITATION_ELAPSED,
            "terms_evidence": {
                "term_asserted": True,
                "limitation_term_calculation_breached": True,
            },
        },
        expected_outcomes={
            "general_effects_evaluation.claims_barred_by_limitation": False,
            "general_effects_evaluation.limitation_conclusion_unreliable": True,
            "general_effects_evaluation.contractual_claims_enforceable": True,
            "requires_human_resolution": True,
        },
    ),
    CaseScenario(
        id="scenario-abuse-of-right",
        title_ru="Установлено злоупотребление правом",
        fabula_ru=(
            "Требование заявлено исключительно с намерением причинить вред контрагенту; "
            "злоупотребление правом установлено."
        ),
        legal_basis_ru=(
            "При злоупотреблении правом суд отказывает лицу в защите принадлежащего ему "
            "права (статья 10 ГК РФ). Сделка при этом не порочится: договор сохраняет силу."
        ),
        evidence_overrides={
            "civil_principles_evidence": {
                "civil_rights_exercise_asserted": True,
                "abuse_of_right_established": True,
            }
        },
        expected_outcomes={
            "general_effects_evaluation.contract_legally_effective": True,
            "general_effects_evaluation.protection_refused_for_abuse": True,
            "general_effects_evaluation.contractual_claims_enforceable": False,
            "requires_human_resolution": True,
        },
    ),
    CaseScenario(
        id="scenario-missing-statutory-consent",
        title_ru="Сделка совершена без необходимого в силу закона согласия",
        fabula_ru=(
            "На совершение сделки требовалось согласие третьего лица; согласие получено не "
            "было, и это отражено как основание оспоримости."
        ),
        legal_basis_ru=(
            "Сделка без необходимого согласия оспорима (статья 173.1 ГК РФ) и недействительна "
            "только в силу признания её таковой судом (пункт 1 статьи 166 ГК РФ). До решения "
            "суда договор действует и требования исполнимы."
        ),
        evidence_overrides={
            "transactions_evidence": {
                "transaction_asserted": True,
                "statutory_consent_not_obtained": True,
            },
            "invalidity_evidence": {"transaction_concluded": True, "required_consent_absent": True},
        },
        expected_outcomes={
            "general_effects_evaluation.transaction_challengeable_for_missing_consent": True,
            "general_effects_evaluation.contract_legally_effective": True,
            "general_effects_evaluation.contractual_claims_enforceable": True,
            "general_consistency_evaluation.consent_invalidity_conflict": False,
            "requires_human_resolution": True,
        },
    ),
    CaseScenario(
        id="scenario-party-incapacity",
        title_ru="Сторона признана судом недееспособной",
        fabula_ru=(
            "Одна из сторон на момент совершения сделки была признана судом недееспособной; "
            "сделка совершена ею самой, а не опекуном."
        ),
        legal_basis_ru=(
            "Сделка, совершённая гражданином, признанным недееспособным, ничтожна "
            "(статья 171 ГК РФ) и не влечёт юридических последствий (статья 167 ГК РФ). "
            "Выводы специальных институтов о нарушении договора лишаются эффекта."
        ),
        evidence_overrides=_merge(
            {
                "persons_evidence": {
                    "party_capacity_asserted": True,
                    "incapacity_declared_by_court": True,
                },
                "invalidity_evidence": {
                    "transaction_concluded": True,
                    "incapacitated_person_transaction": True,
                },
            },
            _NO_DUTY,
        ),
        expected_outcomes={
            "general_effects_evaluation.incapacity_voids_transaction": True,
            "general_effects_evaluation.contract_legally_effective": False,
            "general_effects_evaluation.institute_conclusions_displaced": True,
            "general_effects_evaluation.contractual_claims_enforceable": False,
            "general_consistency_evaluation.capacity_invalidity_conflict": False,
            "requires_human_resolution": True,
        },
    ),
    CaseScenario(
        id="scenario-object-out-of-circulation",
        title_ru="Предметом сделки является объект, изъятый из оборота",
        fabula_ru=(
            "Предмет договора изъят из оборота; отчуждение такого объекта нарушает закон и "
            "посягает на публичные интересы."
        ),
        legal_basis_ru=(
            "Объекты гражданских прав свободно отчуждаются, если они не ограничены в обороте "
            "(статья 129 ГК РФ); сделка, нарушающая требование закона и посягающая на "
            "публичные интересы, ничтожна (пункт 2 статьи 168 ГК РФ)."
        ),
        evidence_overrides=_merge(
            {
                "objects_evidence": {
                    "object_of_rights_asserted": True,
                    "object_not_in_civil_circulation": True,
                },
                "invalidity_evidence": {
                    "transaction_concluded": True,
                    "violates_law": True,
                    "public_interests_or_third_rights_affected": True,
                },
            },
            _NO_DUTY,
        ),
        expected_outcomes={
            "general_effects_evaluation.restricted_object_voids_transaction": True,
            "general_effects_evaluation.contract_legally_effective": False,
            "general_effects_evaluation.institute_conclusions_displaced": True,
            "general_consistency_evaluation.circulation_lawfulness_conflict": False,
            "requires_human_resolution": True,
        },
    ),
    CaseScenario(
        id="scenario-unauthorized-representation",
        title_ru="Сделка совершена неуполномоченным лицом и не одобрена",
        fabula_ru=("Договор подписан лицом без полномочий; представляемый сделку не одобрил."),
        legal_basis_ru=(
            "При отсутствии полномочий сделка считается заключённой от имени совершившего её "
            "лица и не связывает представляемого, пока он её не одобрит (статья 183 ГК РФ)."
        ),
        # Прежняя проверка входов выводит существование обязанности только из
        # заключения и недействительности, поэтому здесь `duty_exists` остаётся
        # истинным, хотя слой заключает, что договор представляемого не связывает.
        evidence_overrides={
            "representation_evidence": {
                "representation_relation_established": True,
                "unauthorized_act_without_ratification": True,
            }
        },
        expected_outcomes={
            "general_effects_evaluation.unauthorized_representation_displaces_contract": True,
            "general_effects_evaluation.contract_legally_effective": False,
            "general_effects_evaluation.institute_conclusions_displaced": True,
            "requires_human_resolution": True,
        },
    ),
    CaseScenario(
        id="scenario-disposal-by-non-owner",
        title_ru="Продана вещь, принадлежащая другому лицу",
        fabula_ru=(
            "Имуществом распорядилось лицо, не управомоченное на его отчуждение; покупатель "
            "требует признания за собой права собственности."
        ),
        legal_basis_ru=(
            "Распоряжение имуществом принадлежит собственнику (статья 209 ГК РФ), поэтому "
            "право к приобретателю по общему правилу не перешло. Сам договор при этом "
            "действителен: продажа чужой вещи не влечёт недействительности."
        ),
        evidence_overrides={
            "property_rights_evidence": {
                "property_right_asserted": True,
                "disposal_by_non_owner_detected": True,
            }
        },
        expected_outcomes={
            "general_effects_evaluation.title_transfer_defeated": True,
            "general_effects_evaluation.contract_legally_effective": True,
            "general_effects_evaluation.contractual_claims_enforceable": True,
            "requires_human_resolution": True,
        },
    ),
    CaseScenario(
        id="scenario-simple-written-form-defect",
        title_ru="Простая письменная форма не соблюдена",
        fabula_ru=(
            "Договор заключён устно там, где требовалась простая письменная форма; закон и "
            "соглашение сторон не связывают с этим недействительность."
        ),
        legal_basis_ru=(
            "Несоблюдение простой письменной формы лишает стороны права ссылаться на "
            "свидетельские показания, но не влечёт недействительности сделки, кроме прямо "
            "указанных в законе или соглашении случаев (пункт 1 статьи 162 ГК РФ). Система "
            "не должна объявлять договор ничтожным."
        ),
        evidence_overrides={
            "form_evidence": {
                "simple_written_form_required": True,
                "simple_written_form_observed": False,
                "written_noncompliance_invalidates_by_law_or_agreement": False,
            }
        },
        expected_outcomes={
            "general_effects_evaluation.form_defect_displaces_contract": False,
            "general_effects_evaluation.contract_legally_effective": True,
            "general_effects_evaluation.institute_conclusions_displaced": False,
            "general_consistency_evaluation.formation_form_observance_conflict": False,
        },
    ),
    CaseScenario(
        id="scenario-invalidity-with-restitution",
        title_ru="Сделка недействительна, стороны успели исполнить",
        fabula_ru=(
            "Сделка совершена с целью, противной основам правопорядка и нравственности; "
            "обе стороны действовали умышленно и успели произвести исполнение."
        ),
        legal_basis_ru=(
            "Недействительная сделка не влечёт последствий, кроме связанных с её "
            "недействительностью; каждая сторона обязана возвратить полученное "
            "(статья 167 ГК РФ), а к требованиям о возврате применяются правила о "
            "неосновательном обогащении (статья 1103 ГК РФ)."
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
            "general_effects_evaluation.contract_legally_effective": False,
            "general_effects_evaluation.restitution_regime_applies": True,
            "requires_human_resolution": True,
        },
    ),
    CaseScenario(
        id="scenario-contradictory-review-data",
        title_ru="Рецензент внёс несогласованные факты о недееспособности",
        fabula_ru=(
            "В модели лиц недееспособность стороны утверждена, в модели недействительности "
            "тот же факт отрицается. Дело подготовлено с ошибкой."
        ),
        legal_basis_ru=(
            "Одно и то же обстоятельство — недееспособность стороны (статьи 29 и 171 ГК РФ) — "
            "описано в двух институтах по-разному. Формальная модель не вправе выбрать версию "
            "за рецензента: противоречие называется и выносится на экспертизу."
        ),
        evidence_overrides={
            "persons_evidence": {
                "party_capacity_asserted": True,
                "incapacity_declared_by_court": True,
            },
            "invalidity_evidence": {
                "transaction_concluded": True,
                "incapacitated_person_transaction": False,
            },
        },
        expected_outcomes={
            "general_consistency_evaluation.capacity_invalidity_conflict": True,
            "general_consistency_evaluation.contradictions_detected": True,
            "requires_human_resolution": True,
        },
    ),
)


def _flip(evidence, updates: dict[str, bool]):
    known = {assertion.predicate.value for assertion in evidence.assertions}
    unknown = set(updates) - known
    if unknown:
        raise ValueError(f"Unknown predicates for scenario override: {sorted(unknown)}")
    return evidence.model_copy(
        update={
            "assertions": tuple(
                assertion.model_copy(update={"value": updates[assertion.predicate.value]})
                if assertion.predicate.value in updates
                else assertion
                for assertion in evidence.assertions
            )
        }
    )


def run_case_scenario(scenario: CaseScenario) -> ReviewedContractAnalysisResult:
    """Прогнать фабулу через весь анализ."""
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


def run_case_scenario_suite() -> CaseScenarioReport:
    results = []
    for scenario in CASE_SCENARIOS:
        result = run_case_scenario(scenario)
        observed = {name: _read(result, name) for name in scenario.expected_outcomes}
        mismatched = sorted(
            name for name, value in scenario.expected_outcomes.items() if observed[name] != value
        )
        results.append(
            CaseScenarioResult(
                scenario_id=scenario.id,
                title_ru=scenario.title_ru,
                passed=not mismatched,
                expected_outcomes=scenario.expected_outcomes,
                observed_outcomes=observed,
                mismatched=mismatched,
                reasons_ru=result.general_effects_evaluation.reasons_ru,
            )
        )
    passed = sum(item.passed for item in results)
    return CaseScenarioReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )
