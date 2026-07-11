import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.reasoning.counterfactual import (
    CounterfactualBudget,
    CounterfactualFactDelta,
    CounterfactualOutcomeDelta,
    LegalOperatorKind,
)
from causa.reasoning.formal_checks import (
    ConstraintEvaluation,
    ConstraintSet,
    ObligationFactSet,
    evaluate_obligation_constraints,
)


CONTRACT_LEGAL_OPERATOR_LIBRARY_VERSION = "contracts-legal-operators-ru-v1"
COUNTERFACTUAL_ENGINE_VERSION = "bounded-counterfactual-engine-v0"
COUNTERFACTUAL_DISCLAIMER_RU = (
    "Контрфактические сценарии являются гипотезами чувствительности формальной модели, "
    "не устанавливают факты и требуют проверки юристом."
)


class ContractLegalOperatorCode(str, Enum):
    CORRECT_PERFORMANCE_DATE = "correct_performance_date"
    ACTIVATE_VALID_EXCEPTION = "activate_valid_exception"
    CONFIRM_NONCONFORMING_PERFORMANCE = "confirm_nonconforming_performance"
    ESTABLISH_PAYMENT_DEFAULT = "establish_payment_default"
    REQUEST_DAMAGES_WITH_CAUSATION = "request_damages_with_causation"
    REQUEST_DAMAGES_WITHOUT_CAUSATION = "request_damages_without_causation"
    TEST_LIMITATION_BAR = "test_limitation_bar"


FACT_LABELS_RU = {
    "duty_exists": "Наличие обязанности",
    "due_date_missed": "Пропуск срока",
    "valid_exception_applies": "Применимое основание освобождения",
    "performance_completed": "Завершение исполнения",
    "performance_nonconforming": "Ненадлежащее исполнение",
    "payment_duty_exists": "Наличие обязанности по оплате",
    "payment_due": "Наступление срока оплаты",
    "payment_missed": "Пропуск платежа",
    "payment_defense_applies": "Применимое возражение против платежа",
    "loss_claimed": "Заявление об убытках",
    "causation_established": "Установленная причинная связь",
    "remedy_requested": "Заявленный способ защиты",
    "limitation_period_expired": "Истечение срока исковой давности",
}

OUTCOME_LABELS_RU = {
    "breach_issue": "Вопрос о нарушении обязательства",
    "late_performance_issue": "Просрочка исполнения",
    "defect_issue": "Ненадлежащее исполнение",
    "payment_default_issue": "Просрочка платежа",
    "damages_remedy_available": "Формальная доступность требования убытков",
    "causation_evidence_gap": "Пробел причинной связи",
    "limitation_bar": "Барьер исковой давности",
}


class ContractLegalOperator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    code: ContractLegalOperatorCode
    kind: LegalOperatorKind
    title_ru: str
    legal_question_ru: str
    preconditions: dict[str, bool] = Field(default_factory=dict)
    fact_patch: dict[str, bool] = Field(min_length=1)
    required_evidence_ru: tuple[str, ...] = Field(min_length=1)
    requires_human_review: bool = True

    @model_validator(mode="after")
    def validate_operator(self) -> "ContractLegalOperator":
        allowed_fields = set(ObligationFactSet.model_fields)
        supplied_fields = set(self.preconditions) | set(self.fact_patch)
        unknown_fields = supplied_fields - allowed_fields
        if unknown_fields:
            raise ValueError(
                "Оператор пытается изменить неразрешенные поля: "
                + ", ".join(sorted(unknown_fields))
            )
        if not self.requires_human_review:
            raise ValueError("Договорный контрфактический оператор требует проверки юристом.")
        if self.id != f"contract-operator:{self.code.value}":
            raise ValueError("ID договорного оператора не соответствует его коду.")
        return self


class ContractLegalOperatorLibrary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    version: str
    locale: str = "ru-RU"
    operators: tuple[ContractLegalOperator, ...]
    content_hash: str

    @model_validator(mode="after")
    def validate_library(self) -> "ContractLegalOperatorLibrary":
        codes = [operator.code for operator in self.operators]
        if set(codes) != set(ContractLegalOperatorCode) or len(codes) != len(set(codes)):
            raise ValueError("Библиотека должна содержать ровно по одному оператору каждого типа.")
        expected_hash = compute_contract_operator_library_hash(
            self.version,
            self.locale,
            self.operators,
        )
        if self.content_hash != expected_hash:
            raise ValueError("Hash библиотеки legal operators не соответствует содержимому.")
        return self

    def operator_for(self, code: ContractLegalOperatorCode) -> ContractLegalOperator:
        return next(operator for operator in self.operators if operator.code == code)


class CounterfactualSkippedOperator(BaseModel):
    operator_id: str
    reason_code: str
    reason_ru: str


class ContractCounterfactualScenario(BaseModel):
    id: str
    operator_id: str
    operator_code: ContractLegalOperatorCode
    operator_kind: LegalOperatorKind
    title_ru: str
    legal_question_ru: str
    baseline_fact_hash: str
    hypothetical_fact_hash: str
    fact_deltas: list[CounterfactualFactDelta] = Field(min_length=1)
    outcome_deltas: list[CounterfactualOutcomeDelta] = Field(default_factory=list)
    hypothetical_facts: ObligationFactSet
    hypothetical_evaluation: ConstraintEvaluation
    material: bool
    requires_human_review: bool = True
    warning_ru: str = COUNTERFACTUAL_DISCLAIMER_RU

    @model_validator(mode="after")
    def validate_scenario(self) -> "ContractCounterfactualScenario":
        if self.baseline_fact_hash == self.hypothetical_fact_hash:
            raise ValueError("Контрфактический сценарий должен изменять hash фактов.")
        if self.hypothetical_fact_hash != _fact_hash(self.hypothetical_facts):
            raise ValueError("Hash гипотетических фактов не соответствует содержимому.")
        if self.material != bool(self.outcome_deltas):
            raise ValueError("Материальность сценария не соответствует изменениям результата.")
        for delta in self.fact_deltas:
            if getattr(self.hypothetical_facts, delta.field_name) != delta.after:
                raise ValueError("Изменение факта не соответствует гипотетической конфигурации.")
        return self


class ContractCounterfactualSensitivityReport(BaseModel):
    id: str
    trace_id: str
    locale: str = "ru-RU"
    engine_version: str = COUNTERFACTUAL_ENGINE_VERSION
    institutional_package_version: str
    operator_library_id: str
    operator_library_version: str
    operator_library_hash: str
    budget: CounterfactualBudget
    baseline_fact_hash: str
    baseline_facts: ObligationFactSet
    baseline_evaluation: ConstraintEvaluation
    scenarios: list[ContractCounterfactualScenario] = Field(default_factory=list)
    skipped_operators: list[CounterfactualSkippedOperator] = Field(default_factory=list)
    critical_scenario_ids: list[str] = Field(default_factory=list)
    budget_exhausted: bool
    summary_ru: list[str] = Field(default_factory=list)
    disclaimer_ru: str = COUNTERFACTUAL_DISCLAIMER_RU

    @model_validator(mode="after")
    def validate_report(self) -> "ContractCounterfactualSensitivityReport":
        if self.baseline_fact_hash != _fact_hash(self.baseline_facts):
            raise ValueError("Hash исходных фактов не соответствует содержимому.")
        scenario_operator_ids = [scenario.operator_id for scenario in self.scenarios]
        skipped_operator_ids = [item.operator_id for item in self.skipped_operators]
        if len(scenario_operator_ids) != len(set(scenario_operator_ids)):
            raise ValueError("Один legal operator вычислен более одного раза.")
        if set(scenario_operator_ids) & set(skipped_operator_ids):
            raise ValueError("Legal operator не может быть одновременно вычислен и пропущен.")
        for scenario in self.scenarios:
            if scenario.baseline_fact_hash != self.baseline_fact_hash:
                raise ValueError("Сценарий относится к другой исходной конфигурации.")
            expected_deltas = _outcome_deltas(
                self.baseline_evaluation,
                scenario.hypothetical_evaluation,
            )
            if scenario.outcome_deltas != expected_deltas:
                raise ValueError("Изменения результата не воспроизводятся из evaluations.")
        expected_critical = [
            scenario.id
            for scenario in sorted(
                (scenario for scenario in self.scenarios if scenario.material),
                key=lambda scenario: (len(scenario.fact_deltas), scenario.operator_id),
            )
        ]
        if self.critical_scenario_ids != expected_critical:
            raise ValueError("Критические сценарии не соответствуют материальным изменениям.")
        if len(self.scenarios) > self.budget.max_scenarios:
            raise ValueError("Отчет превышает установленный бюджет сценариев.")
        return self


def compute_contract_operator_library_hash(
    version: str,
    locale: str,
    operators: tuple[ContractLegalOperator, ...],
) -> str:
    canonical = json.dumps(
        {
            "version": version,
            "locale": locale,
            "operators": [
                operator.model_dump(mode="json")
                for operator in sorted(operators, key=lambda item: item.code.value)
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _operator(
    code: ContractLegalOperatorCode,
    kind: LegalOperatorKind,
    title_ru: str,
    legal_question_ru: str,
    preconditions: dict[str, bool],
    fact_patch: dict[str, bool],
    required_evidence_ru: tuple[str, ...],
) -> ContractLegalOperator:
    return ContractLegalOperator(
        id=f"contract-operator:{code.value}",
        code=code,
        kind=kind,
        title_ru=title_ru,
        legal_question_ru=legal_question_ru,
        preconditions=preconditions,
        fact_patch=fact_patch,
        required_evidence_ru=required_evidence_ru,
    )


def build_contract_legal_operator_library() -> ContractLegalOperatorLibrary:
    version = CONTRACT_LEGAL_OPERATOR_LIBRARY_VERSION
    operators = (
        _operator(
            ContractLegalOperatorCode.CORRECT_PERFORMANCE_DATE,
            LegalOperatorKind.CHANGE_TEMPORAL_ANCHOR,
            "Изменить временную привязку исполнения",
            "Изменится ли вывод, если исполнение считать совершенным в согласованный срок?",
            {"due_date_missed": True},
            {"due_date_missed": False},
            ("Документ о согласованном сроке", "Документ о фактической дате исполнения"),
        ),
        _operator(
            ContractLegalOperatorCode.ACTIVATE_VALID_EXCEPTION,
            LegalOperatorKind.ACTIVATE_EXCEPTION,
            "Активировать основание освобождения",
            "Изменится ли вывод при подтвержденном применимом основании освобождения?",
            {"due_date_missed": True, "valid_exception_applies": False},
            {"valid_exception_applies": True},
            ("Текст договорного или нормативного основания", "Факты его применимости"),
        ),
        _operator(
            ContractLegalOperatorCode.CONFIRM_NONCONFORMING_PERFORMANCE,
            LegalOperatorKind.CHANGE_QUALIFICATION,
            "Квалифицировать исполнение как ненадлежащее",
            "Изменится ли набор нарушений при подтвержденном несоответствии исполнения?",
            {"performance_completed": True, "performance_nonconforming": False},
            {"performance_nonconforming": True},
            ("Документы о приемке", "Доказательства конкретного несоответствия"),
        ),
        _operator(
            ContractLegalOperatorCode.ESTABLISH_PAYMENT_DEFAULT,
            LegalOperatorKind.ADD_OR_REMOVE_FACT,
            "Добавить подтвержденную просрочку платежа",
            "Возникнет ли самостоятельный вопрос о просрочке подтвержденного платежа?",
            {"payment_duty_exists": False},
            {"payment_duty_exists": True, "payment_due": True, "payment_missed": True},
            ("Основание обязанности по оплате", "Срок оплаты", "Подтверждение неплатежа"),
        ),
        _operator(
            ContractLegalOperatorCode.REQUEST_DAMAGES_WITH_CAUSATION,
            LegalOperatorKind.CHANGE_REMEDY_PATH,
            "Проверить требование убытков с причинной связью",
            "Станет ли требование убытков формально доступным при подтвержденной связи?",
            {"loss_claimed": False, "remedy_requested": False},
            {"loss_claimed": True, "causation_established": True, "remedy_requested": True},
            ("Расчет убытков", "Доказательства причинной связи", "Формулировка требования"),
        ),
        _operator(
            ContractLegalOperatorCode.REQUEST_DAMAGES_WITHOUT_CAUSATION,
            LegalOperatorKind.CHANGE_CAUSAL_LINK,
            "Проверить требование убытков без причинной связи",
            "Выявит ли модель доказательственный пробел при отсутствии причинной связи?",
            {"loss_claimed": False, "remedy_requested": False},
            {"loss_claimed": True, "remedy_requested": True},
            ("Расчет убытков", "Формулировка требования", "Проверка причинной связи"),
        ),
        _operator(
            ContractLegalOperatorCode.TEST_LIMITATION_BAR,
            LegalOperatorKind.CHANGE_REMEDY_PATH,
            "Проверить влияние исковой давности",
            "Заблокирует ли указанное истечение срока иначе доступное требование убытков?",
            {"remedy_requested": False, "limitation_period_expired": False},
            {
                "loss_claimed": True,
                "causation_established": True,
                "remedy_requested": True,
                "limitation_period_expired": True,
            },
            ("Дата начала течения срока", "Расчет срока", "Заявление стороны о давности"),
        ),
    )
    return ContractLegalOperatorLibrary(
        id=f"contract-legal-operator-library:{version}",
        version=version,
        operators=operators,
        content_hash=compute_contract_operator_library_hash(version, "ru-RU", operators),
    )


def _fact_hash(facts: ObligationFactSet) -> str:
    canonical = json.dumps(
        facts.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _outcome_deltas(
    baseline: ConstraintEvaluation,
    hypothetical: ConstraintEvaluation,
) -> list[CounterfactualOutcomeDelta]:
    return [
        CounterfactualOutcomeDelta(
            field_name=field_name,
            field_label_ru=field_label_ru,
            before=getattr(baseline, field_name),
            after=getattr(hypothetical, field_name),
        )
        for field_name, field_label_ru in OUTCOME_LABELS_RU.items()
        if getattr(baseline, field_name) != getattr(hypothetical, field_name)
    ]


def run_contract_counterfactual_sensitivity(
    *,
    trace_id: str,
    constraint_set: ConstraintSet,
    baseline_facts: ObligationFactSet,
    operator_codes: list[ContractLegalOperatorCode] | None = None,
    budget: CounterfactualBudget | None = None,
    library: ContractLegalOperatorLibrary | None = None,
) -> ContractCounterfactualSensitivityReport:
    selected_library = library or build_contract_legal_operator_library()
    selected_budget = budget or CounterfactualBudget()
    selected_codes = (
        [operator.code for operator in selected_library.operators]
        if operator_codes is None
        else operator_codes
    )
    if len(selected_codes) != len(set(selected_codes)):
        raise ValueError("Запрос содержит повторяющиеся legal operators.")
    library_codes = {operator.code for operator in selected_library.operators}
    unknown_codes = set(selected_codes) - library_codes
    if unknown_codes:
        raise ValueError(
            "Запрошены отсутствующие legal operators: "
            + ", ".join(sorted(code.value for code in unknown_codes))
        )

    baseline_evaluation = evaluate_obligation_constraints(constraint_set, baseline_facts)
    baseline_hash = _fact_hash(baseline_facts)
    scenarios: list[ContractCounterfactualScenario] = []
    skipped: list[CounterfactualSkippedOperator] = []
    budget_exhausted = False
    for code in selected_codes:
        operator = selected_library.operator_for(code)
        unmet = [
            field_name
            for field_name, expected in operator.preconditions.items()
            if getattr(baseline_facts, field_name) != expected
        ]
        if unmet:
            skipped.append(
                CounterfactualSkippedOperator(
                    operator_id=operator.id,
                    reason_code="precondition_not_met",
                    reason_ru=(
                        "Не выполнены исходные условия: "
                        + ", ".join(FACT_LABELS_RU[field] for field in unmet)
                        + "."
                    ),
                )
            )
            continue
        fact_deltas = [
            CounterfactualFactDelta(
                field_name=field_name,
                field_label_ru=FACT_LABELS_RU[field_name],
                before=getattr(baseline_facts, field_name),
                after=after,
            )
            for field_name, after in operator.fact_patch.items()
            if getattr(baseline_facts, field_name) != after
        ]
        if not fact_deltas:
            skipped.append(
                CounterfactualSkippedOperator(
                    operator_id=operator.id,
                    reason_code="no_change",
                    reason_ru="Оператор не изменяет текущую конфигурацию фактов.",
                )
            )
            continue
        if len(fact_deltas) > selected_budget.max_changed_facts_per_scenario:
            skipped.append(
                CounterfactualSkippedOperator(
                    operator_id=operator.id,
                    reason_code="fact_budget_exceeded",
                    reason_ru="Оператор превышает бюджет изменений фактов.",
                )
            )
            continue
        if len(scenarios) >= selected_budget.max_scenarios:
            budget_exhausted = True
            skipped.append(
                CounterfactualSkippedOperator(
                    operator_id=operator.id,
                    reason_code="scenario_budget_exceeded",
                    reason_ru="Оператор не вычислен: исчерпан бюджет сценариев.",
                )
            )
            continue

        hypothetical_facts = baseline_facts.model_copy(update=operator.fact_patch)
        hypothetical_evaluation = evaluate_obligation_constraints(
            constraint_set,
            hypothetical_facts,
        )
        outcome_deltas = _outcome_deltas(baseline_evaluation, hypothetical_evaluation)
        scenarios.append(
            ContractCounterfactualScenario(
                id=f"counterfactual:{trace_id}:{operator.code.value}",
                operator_id=operator.id,
                operator_code=operator.code,
                operator_kind=operator.kind,
                title_ru=operator.title_ru,
                legal_question_ru=operator.legal_question_ru,
                baseline_fact_hash=baseline_hash,
                hypothetical_fact_hash=_fact_hash(hypothetical_facts),
                fact_deltas=fact_deltas,
                outcome_deltas=outcome_deltas,
                hypothetical_facts=hypothetical_facts,
                hypothetical_evaluation=hypothetical_evaluation,
                material=bool(outcome_deltas),
            )
        )

    critical_scenario_ids = [
        scenario.id
        for scenario in sorted(
            (scenario for scenario in scenarios if scenario.material),
            key=lambda scenario: (len(scenario.fact_deltas), scenario.operator_id),
        )
    ]
    return ContractCounterfactualSensitivityReport(
        id=f"counterfactual-sensitivity:{trace_id}",
        trace_id=trace_id,
        institutional_package_version=(
            f"{CONTRACTS_PACKAGE_MANIFEST.id}@{CONTRACTS_PACKAGE_MANIFEST.version}"
        ),
        operator_library_id=selected_library.id,
        operator_library_version=selected_library.version,
        operator_library_hash=selected_library.content_hash,
        budget=selected_budget,
        baseline_fact_hash=baseline_hash,
        baseline_facts=baseline_facts,
        baseline_evaluation=baseline_evaluation,
        scenarios=scenarios,
        skipped_operators=skipped,
        critical_scenario_ids=critical_scenario_ids,
        budget_exhausted=budget_exhausted,
        summary_ru=[
            f"Вычислено гипотетических сценариев: {len(scenarios)}.",
            f"Материально изменяют формальный результат: {len(critical_scenario_ids)}.",
            f"Пропущено операторов по ограничениям: {len(skipped)}.",
        ],
    )
