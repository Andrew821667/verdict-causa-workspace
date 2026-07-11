from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from causa.core.bootstrap import FormalObligationRule
from causa.institutional.contracts.legal_operators import (
    ContractLegalOperator,
    ContractLegalOperatorCode,
    ContractCounterfactualSensitivityReport,
    run_contract_counterfactual_sensitivity,
)
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.reasoning.counterfactual import CounterfactualBudget, LegalOperatorKind
from causa.reasoning.formal_checks import (
    ObligationFactSet,
    build_obligation_constraint_set,
)


class CounterfactualBenchmarkTask(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title_ru: str
    baseline_facts: ObligationFactSet
    operator_code: ContractLegalOperatorCode
    expected_outcomes: dict[str, bool]


class CounterfactualBenchmarkResult(BaseModel):
    task_id: str
    passed: bool
    scenario_id: str | None = None
    observed_outcomes: dict[str, bool] = Field(default_factory=dict)
    reasons_ru: list[str] = Field(default_factory=list)


class CounterfactualBenchmarkReport(BaseModel):
    id: str = "synthetic-contract-counterfactual-benchmark-suite-v0"
    locale: str = "ru-RU"
    institutional_package_id: str = CONTRACTS_PACKAGE_MANIFEST.id
    total: int
    passed: int
    failed: int
    results: list[CounterfactualBenchmarkResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_counts(self) -> "CounterfactualBenchmarkReport":
        if self.total != len(self.results) or self.passed + self.failed != self.total:
            raise ValueError("Счетчики counterfactual benchmark не согласованы.")
        if self.passed != sum(result.passed for result in self.results):
            raise ValueError("Число пройденных counterfactual benchmark неверно.")
        return self


class CounterfactualAttackKind(str, Enum):
    DIRECT_OUTCOME_MUTATION = "direct_outcome_mutation"
    UNKNOWN_FACT_MUTATION = "unknown_fact_mutation"
    UNREVIEWED_OPERATOR = "unreviewed_operator"
    FACT_BUDGET_BYPASS = "fact_budget_bypass"
    SCENARIO_BUDGET_BYPASS = "scenario_budget_bypass"
    PRECONDITION_BYPASS = "precondition_bypass"
    DUPLICATE_OPERATOR = "duplicate_operator"


class CounterfactualRedTeamResult(BaseModel):
    attack_kind: CounterfactualAttackKind
    blocked: bool
    reasons_ru: list[str] = Field(default_factory=list)


class CounterfactualRedTeamReport(BaseModel):
    id: str = "synthetic-contract-counterfactual-red-team-suite-v0"
    locale: str = "ru-RU"
    institutional_package_id: str = CONTRACTS_PACKAGE_MANIFEST.id
    total: int
    blocked: int
    unblocked: int
    results: list[CounterfactualRedTeamResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_counts(self) -> "CounterfactualRedTeamReport":
        if self.total != len(self.results) or self.blocked + self.unblocked != self.total:
            raise ValueError("Счетчики counterfactual Red Team не согласованы.")
        if self.blocked != sum(result.blocked for result in self.results):
            raise ValueError("Число заблокированных counterfactual-атак неверно.")
        return self


class SyntheticCounterfactualEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    title_ru: str = "Синтетическая оценка legal operators договорного пакета"
    disclaimer_ru: str = (
        "Сценарии гипотетические, не устанавливают факты, не являются юридической "
        "консультацией и требуют проверки юристом."
    )
    sensitivity_report: ContractCounterfactualSensitivityReport
    benchmark_report: CounterfactualBenchmarkReport
    red_team_report: CounterfactualRedTeamReport


BASELINE_LATE_DELIVERY_FACTS = ObligationFactSet(
    duty_exists=True,
    due_date_missed=True,
    performance_completed=True,
)


SYNTHETIC_COUNTERFACTUAL_BENCHMARKS = (
    CounterfactualBenchmarkTask(
        id="counterfactual-bench-correct-date",
        title_ru="Изменение даты устраняет единственный паттерн просрочки",
        baseline_facts=BASELINE_LATE_DELIVERY_FACTS,
        operator_code=ContractLegalOperatorCode.CORRECT_PERFORMANCE_DATE,
        expected_outcomes={"breach_issue": False, "late_performance_issue": False},
    ),
    CounterfactualBenchmarkTask(
        id="counterfactual-bench-valid-exception",
        title_ru="Применимое исключение устраняет вывод о просрочке",
        baseline_facts=BASELINE_LATE_DELIVERY_FACTS,
        operator_code=ContractLegalOperatorCode.ACTIVATE_VALID_EXCEPTION,
        expected_outcomes={"breach_issue": False, "late_performance_issue": False},
    ),
    CounterfactualBenchmarkTask(
        id="counterfactual-bench-nonconforming",
        title_ru="Подтвержденное несоответствие добавляет самостоятельный вид нарушения",
        baseline_facts=BASELINE_LATE_DELIVERY_FACTS,
        operator_code=ContractLegalOperatorCode.CONFIRM_NONCONFORMING_PERFORMANCE,
        expected_outcomes={"defect_issue": True},
    ),
    CounterfactualBenchmarkTask(
        id="counterfactual-bench-payment-default",
        title_ru="Подтвержденные платежные факты добавляют просрочку оплаты",
        baseline_facts=BASELINE_LATE_DELIVERY_FACTS,
        operator_code=ContractLegalOperatorCode.ESTABLISH_PAYMENT_DEFAULT,
        expected_outcomes={"payment_default_issue": True},
    ),
    CounterfactualBenchmarkTask(
        id="counterfactual-bench-damages",
        title_ru="Требование, убытки и причинная связь открывают путь к убыткам",
        baseline_facts=BASELINE_LATE_DELIVERY_FACTS,
        operator_code=ContractLegalOperatorCode.REQUEST_DAMAGES_WITH_CAUSATION,
        expected_outcomes={"damages_remedy_available": True},
    ),
    CounterfactualBenchmarkTask(
        id="counterfactual-bench-causation-gap",
        title_ru="Требование без причинной связи выявляет доказательственный пробел",
        baseline_facts=BASELINE_LATE_DELIVERY_FACTS,
        operator_code=ContractLegalOperatorCode.REQUEST_DAMAGES_WITHOUT_CAUSATION,
        expected_outcomes={"causation_evidence_gap": True},
    ),
    CounterfactualBenchmarkTask(
        id="counterfactual-bench-limitation",
        title_ru="Истечение указанного срока формирует барьер исковой давности",
        baseline_facts=BASELINE_LATE_DELIVERY_FACTS,
        operator_code=ContractLegalOperatorCode.TEST_LIMITATION_BAR,
        expected_outcomes={"limitation_bar": True},
    ),
)


def _constraint_set(label: str):
    return build_obligation_constraint_set(
        FormalObligationRule(
            id=f"counterfactual-evaluation-rule:{label}",
            source_id="synthetic-counterfactual-evaluation-source",
            debtor="поставщик",
            creditor="покупатель",
            action="исполнить договорное обязательство",
        )
    )


def run_counterfactual_benchmark_suite() -> CounterfactualBenchmarkReport:
    results: list[CounterfactualBenchmarkResult] = []
    for task in SYNTHETIC_COUNTERFACTUAL_BENCHMARKS:
        report = run_contract_counterfactual_sensitivity(
            trace_id=task.id,
            constraint_set=_constraint_set(task.id),
            baseline_facts=task.baseline_facts,
            operator_codes=[task.operator_code],
        )
        scenario = report.scenarios[0] if report.scenarios else None
        observed = (
            {
                field_name: getattr(scenario.hypothetical_evaluation, field_name)
                for field_name in task.expected_outcomes
            }
            if scenario
            else {}
        )
        passed = scenario is not None and observed == task.expected_outcomes
        results.append(
            CounterfactualBenchmarkResult(
                task_id=task.id,
                passed=passed,
                scenario_id=scenario.id if scenario else None,
                observed_outcomes=observed,
                reasons_ru=[
                    "Ожидаемое изменение формального результата подтверждено."
                    if passed
                    else "Ожидаемое изменение формального результата не подтверждено."
                ],
            )
        )
    passed = sum(result.passed for result in results)
    return CounterfactualBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def _invalid_operator_result(
    attack_kind: CounterfactualAttackKind,
    *,
    fact_patch: dict[str, bool],
    requires_human_review: bool = True,
) -> CounterfactualRedTeamResult:
    try:
        ContractLegalOperator(
            id="contract-operator:correct_performance_date",
            code=ContractLegalOperatorCode.CORRECT_PERFORMANCE_DATE,
            kind=LegalOperatorKind.CHANGE_TEMPORAL_ANCHOR,
            title_ru="Атакующий оператор",
            legal_question_ru="Может ли атака изменить защищенное поле?",
            fact_patch=fact_patch,
            required_evidence_ru=("Синтетическое требование",),
            requires_human_review=requires_human_review,
        )
    except ValidationError as error:
        return CounterfactualRedTeamResult(
            attack_kind=attack_kind,
            blocked=True,
            reasons_ru=[f"Контракт оператора отклонил атаку: {error.errors()[0]['msg']}."],
        )
    return CounterfactualRedTeamResult(
        attack_kind=attack_kind,
        blocked=False,
        reasons_ru=["Атакующий оператор был ошибочно принят."],
    )


def run_counterfactual_red_team_suite() -> CounterfactualRedTeamReport:
    constraint_set = _constraint_set("red-team")
    results = [
        _invalid_operator_result(
            CounterfactualAttackKind.DIRECT_OUTCOME_MUTATION,
            fact_patch={"breach_issue": False},
        ),
        _invalid_operator_result(
            CounterfactualAttackKind.UNKNOWN_FACT_MUTATION,
            fact_patch={"invented_legal_fact": True},
        ),
        _invalid_operator_result(
            CounterfactualAttackKind.UNREVIEWED_OPERATOR,
            fact_patch={"due_date_missed": False},
            requires_human_review=False,
        ),
    ]

    fact_budget = run_contract_counterfactual_sensitivity(
        trace_id="red-team-fact-budget",
        constraint_set=constraint_set,
        baseline_facts=BASELINE_LATE_DELIVERY_FACTS,
        operator_codes=[ContractLegalOperatorCode.ESTABLISH_PAYMENT_DEFAULT],
        budget=CounterfactualBudget(max_changed_facts_per_scenario=1),
    )
    results.append(
        CounterfactualRedTeamResult(
            attack_kind=CounterfactualAttackKind.FACT_BUDGET_BYPASS,
            blocked=not fact_budget.scenarios
            and fact_budget.skipped_operators[0].reason_code == "fact_budget_exceeded",
            reasons_ru=["Оператор с превышением числа изменений не вычислен."],
        )
    )

    scenario_budget = run_contract_counterfactual_sensitivity(
        trace_id="red-team-scenario-budget",
        constraint_set=constraint_set,
        baseline_facts=BASELINE_LATE_DELIVERY_FACTS,
        operator_codes=[
            ContractLegalOperatorCode.CORRECT_PERFORMANCE_DATE,
            ContractLegalOperatorCode.ACTIVATE_VALID_EXCEPTION,
        ],
        budget=CounterfactualBudget(max_scenarios=1),
    )
    results.append(
        CounterfactualRedTeamResult(
            attack_kind=CounterfactualAttackKind.SCENARIO_BUDGET_BYPASS,
            blocked=scenario_budget.budget_exhausted and len(scenario_budget.scenarios) == 1,
            reasons_ru=["Вычисление остановлено на установленном бюджете сценариев."],
        )
    )

    unmet_precondition = run_contract_counterfactual_sensitivity(
        trace_id="red-team-precondition",
        constraint_set=constraint_set,
        baseline_facts=BASELINE_LATE_DELIVERY_FACTS.model_copy(
            update={"due_date_missed": False}
        ),
        operator_codes=[ContractLegalOperatorCode.ACTIVATE_VALID_EXCEPTION],
    )
    results.append(
        CounterfactualRedTeamResult(
            attack_kind=CounterfactualAttackKind.PRECONDITION_BYPASS,
            blocked=not unmet_precondition.scenarios
            and unmet_precondition.skipped_operators[0].reason_code
            == "precondition_not_met",
            reasons_ru=["Оператор не применен при невыполненных исходных условиях."],
        )
    )

    try:
        run_contract_counterfactual_sensitivity(
            trace_id="red-team-duplicate",
            constraint_set=constraint_set,
            baseline_facts=BASELINE_LATE_DELIVERY_FACTS,
            operator_codes=[
                ContractLegalOperatorCode.CORRECT_PERFORMANCE_DATE,
                ContractLegalOperatorCode.CORRECT_PERFORMANCE_DATE,
            ],
        )
    except ValueError:
        duplicate_blocked = True
    else:
        duplicate_blocked = False
    results.append(
        CounterfactualRedTeamResult(
            attack_kind=CounterfactualAttackKind.DUPLICATE_OPERATOR,
            blocked=duplicate_blocked,
            reasons_ru=["Повторяющийся оператор отклонен до вычисления."],
        )
    )

    blocked = sum(result.blocked for result in results)
    return CounterfactualRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
