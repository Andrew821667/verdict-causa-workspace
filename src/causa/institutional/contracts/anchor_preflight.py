"""Предварительная сверка входов с якорными выводами: все расхождения сразу.

Существование договорной обязанности выводится из двух якорей — заключения
договора (статьи 432–443 ГК РФ) и недействительности сделки (статьи 166–181) —
и должно быть одинаково отражено во всех институтах, которые от него зависят.
Проверки в `reviewed_analysis` следят за этим строго, но каждая отвергает анализ
на первом же расхождении.

Практическое следствие измерено при подготовке фабул: чтобы собрать дело с
вытеснённым договорным эффектом, о расхождениях приходится узнавать по одному за
прогон — около двадцати предикатов в семи контрактах данных, каждый следующий
виден только после исправления предыдущего.

Этот модуль ничего не решает за рецензента и не меняет поведения анализа. Он
лишь собирает **все** расхождения разом и объясняет по-русски, чем определяется
ожидаемое значение и как его привести в согласие.

Сверки, требующие вывода о нарушении обязательства (`breach_issue`), сюда не
входят: он вычисляется после перевода нормы в формальный вид, и повторять этот
путь здесь значило бы дублировать половину анализа. Это отражено в поле
`not_covered_ru`.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.formation import (
    build_formation_constraint_set,
    evaluate_formation_constraints,
    map_reviewed_formation_evidence,
)
from causa.institutional.contracts.invalidity import (
    build_invalidity_constraint_set,
    evaluate_invalidity_constraints,
    map_reviewed_invalidity_evidence,
)

ANCHOR_PREFLIGHT_VERSION = "contracts-anchor-preflight-v0"


class AnchorMismatch(BaseModel):
    """Одно расхождение входа с якорным выводом."""

    evidence_field: str
    predicate: str
    expected: bool
    actual: bool
    anchor_ru: str
    fix_ru: str


class AnchorPreflightReport(BaseModel):
    version: str = ANCHOR_PREFLIGHT_VERSION
    consistent: bool
    checked: int
    mismatches: list[AnchorMismatch] = Field(default_factory=list)
    anchors_ru: dict[str, bool] = Field(default_factory=dict)
    not_covered_ru: list[str] = Field(default_factory=list)
    summary_ru: str = ""


def _facts(evidence) -> dict[str, bool]:
    return {assertion.predicate.value: assertion.value for assertion in evidence.assertions}


def check_anchor_consistency(request) -> AnchorPreflightReport:
    """Собрать все расхождения входов с якорными выводами за один проход."""
    formation_mapping = map_reviewed_formation_evidence(request.formation_evidence)
    formation = evaluate_formation_constraints(
        build_formation_constraint_set(formation_mapping), formation_mapping.facts
    )
    invalidity_mapping = map_reviewed_invalidity_evidence(request.invalidity_evidence)
    invalidity = evaluate_invalidity_constraints(
        build_invalidity_constraint_set(invalidity_mapping), invalidity_mapping.facts
    )

    concluded = formation.contract_concluded_prerequisites
    displaced = invalidity.contractual_effect_displaced
    duty_expected = concluded and not displaced

    case = _facts(request.case_evidence)
    performance_completed = case.get("performance_completed", False)
    loss_claimed = case.get("loss_claimed", False)
    causation = case.get("causation_established", False)
    payment_due = case.get("payment_due", False)

    concluded_ru = (
        "договор заключён (статья 432 ГК РФ)"
        if concluded
        else "договор не считается заключённым (статья 432 ГК РФ)"
    )
    duty_ru = (
        "договорная обязанность существует: договор заключён и не лишён силы недействительностью"
        if duty_expected
        else "договорной обязанности нет: договор не заключён либо его эффект вытеснен "
        "недействительностью (статья 167 ГК РФ)"
    )
    displaced_ru = (
        "договорный эффект вытеснен недействительностью (статьи 166–181 ГК РФ)"
        if displaced
        else "оснований недействительности не установлено (статьи 166–181 ГК РФ)"
    )

    # (поле запроса, предикат, ожидаемое, пояснение якоря)
    checks: list[tuple[str, str, bool, str]] = [
        ("case_evidence", "duty_exists", duty_expected, duty_ru),
        ("obligation_dynamics_evidence", "obligation_exists", duty_expected, duty_ru),
        ("performance_remedies_evidence", "obligation_exists", duty_expected, duty_ru),
        ("security_evidence", "main_obligation_exists", concluded, concluded_ru),
        ("security_evidence", "main_obligation_invalid", displaced, displaced_ru),
        ("invalidity_evidence", "transaction_concluded", concluded, concluded_ru),
        ("termination_evidence", "contract_formed", concluded, concluded_ru),
        ("sale_evidence", "contract_concluded", concluded, concluded_ru),
        ("supply_evidence", "contract_concluded", concluded, concluded_ru),
        (
            "obligation_dynamics_evidence",
            "performance_rendered",
            performance_completed,
            "исполнение по делу зафиксировано в case_evidence.performance_completed",
        ),
        (
            "sale_evidence",
            "goods_transfer_completed",
            performance_completed,
            "исполнение по делу зафиксировано в case_evidence.performance_completed",
        ),
        (
            "supply_evidence",
            "delivery_completed",
            performance_completed,
            "исполнение по делу зафиксировано в case_evidence.performance_completed",
        ),
        (
            "performance_remedies_evidence",
            "loss_claimed",
            loss_claimed,
            "требование убытков заявлено в case_evidence.loss_claimed",
        ),
        (
            "sale_evidence",
            "loss_claimed",
            loss_claimed,
            "требование убытков заявлено в case_evidence.loss_claimed",
        ),
        (
            "supply_evidence",
            "loss_claimed",
            loss_claimed,
            "требование убытков заявлено в case_evidence.loss_claimed",
        ),
        (
            "performance_remedies_evidence",
            "causation_proven",
            causation,
            "причинная связь установлена в case_evidence.causation_established",
        ),
        (
            "sale_evidence",
            "causation_proven",
            causation,
            "причинная связь установлена в case_evidence.causation_established",
        ),
        (
            "supply_evidence",
            "causation_proven",
            causation,
            "причинная связь установлена в case_evidence.causation_established",
        ),
        (
            "sale_evidence",
            "payment_due",
            payment_due,
            "срок платежа наступил по case_evidence.payment_due",
        ),
        (
            "supply_evidence",
            "payment_due",
            payment_due,
            "срок платежа наступил по case_evidence.payment_due",
        ),
    ]

    cache: dict[str, dict[str, bool]] = {}
    mismatches: list[AnchorMismatch] = []
    for field_name, predicate, expected, anchor_ru in checks:
        if field_name not in cache:
            cache[field_name] = _facts(getattr(request, field_name))
        actual = cache[field_name].get(predicate)
        if actual is None or actual == expected:
            continue
        mismatches.append(
            AnchorMismatch(
                evidence_field=field_name,
                predicate=predicate,
                expected=expected,
                actual=actual,
                anchor_ru=anchor_ru,
                fix_ru=(f"Установите {field_name}.{predicate} = {expected}: {anchor_ru}."),
            )
        )

    summary = (
        "Входы согласованы с якорными выводами."
        if not mismatches
        else (
            f"Расхождений с якорными выводами: {len(mismatches)}. "
            "Анализ отвергнет дело на первом из них, поэтому исправляйте все сразу."
        )
    )
    return AnchorPreflightReport(
        consistent=not mismatches,
        checked=len(checks),
        mismatches=mismatches,
        anchors_ru={
            "договор заключён": concluded,
            "договорный эффект вытеснен": displaced,
            "договорная обязанность существует": duty_expected,
        },
        not_covered_ru=[
            "Сверки, зависящие от вывода о нарушении обязательства (breach_issue), сюда не "
            "входят: он вычисляется после перевода нормы в формальный вид.",
            "Внутриинститутские зависимости предикатов проверяются самими моделями при "
            "разборе данных и здесь не дублируются.",
        ],
        summary_ru=summary,
    )
