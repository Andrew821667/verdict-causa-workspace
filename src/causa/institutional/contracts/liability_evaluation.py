from pydantic import BaseModel, ConfigDict, Field, model_validator

from causa.institutional.contracts.liability import (
    LIABILITY_EVIDENCE_SCHEMA_VERSION,
    LIABILITY_MAPPING_VERSION,
    LiabilityEvaluation,
    LiabilityConstraintSet,
    LiabilityEvidenceMappingResult,
    LiabilityFactSet,
    build_liability_constraint_set,
    evaluate_liability_constraints,
)
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST


class LiabilityBenchmarkTask(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title_ru: str
    facts: LiabilityFactSet
    expected_outcomes: dict[str, bool]


class LiabilityBenchmarkResult(BaseModel):
    task_id: str
    passed: bool
    observed_outcomes: dict[str, bool] = Field(default_factory=dict)
    reasons_ru: list[str] = Field(default_factory=list)


class LiabilityBenchmarkReport(BaseModel):
    id: str = "synthetic-contract-liability-benchmark-suite-v0"
    locale: str = "ru-RU"
    institutional_package_id: str = CONTRACTS_PACKAGE_MANIFEST.id
    total: int
    passed: int
    failed: int
    results: list[LiabilityBenchmarkResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_counts(self) -> "LiabilityBenchmarkReport":
        if self.total != len(self.results) or self.passed + self.failed != self.total:
            raise ValueError("Счетчики liability benchmark не согласованы.")
        if self.passed != sum(result.passed for result in self.results):
            raise ValueError("Число пройденных liability benchmark неверно.")
        return self


class LiabilityRedTeamCase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title_ru: str
    facts: LiabilityFactSet
    forbidden_outcomes: dict[str, bool]


class LiabilityRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    observed_outcomes: dict[str, bool] = Field(default_factory=dict)
    reasons_ru: list[str] = Field(default_factory=list)


class LiabilityRedTeamReport(BaseModel):
    id: str = "synthetic-contract-liability-red-team-suite-v0"
    locale: str = "ru-RU"
    institutional_package_id: str = CONTRACTS_PACKAGE_MANIFEST.id
    total: int
    blocked: int
    unblocked: int
    results: list[LiabilityRedTeamResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_counts(self) -> "LiabilityRedTeamReport":
        if self.total != len(self.results) or self.blocked + self.unblocked != self.total:
            raise ValueError("Счетчики liability Red Team не согласованы.")
        if self.blocked != sum(result.blocked for result in self.results):
            raise ValueError("Число заблокированных liability-атак неверно.")
        return self


class SyntheticLiabilityEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    title_ru: str = "Синтетическая оценка ответственности и снижения неустойки"
    disclaimer_ru: str = (
        "Модель проверяет только формальные предпосылки статей 333 и 401 ГК РФ, "
        "не определяет размер ответственности и требует проверки юристом."
    )
    reviewed_mapping: LiabilityEvidenceMappingResult
    reviewed_constraint_set: LiabilityConstraintSet
    reviewed_evaluation: LiabilityEvaluation
    benchmark_report: LiabilityBenchmarkReport
    red_team_report: LiabilityRedTeamReport

    @model_validator(mode="after")
    def validate_reviewed_replay(self) -> "SyntheticLiabilityEvaluationArtifact":
        expected_set = build_liability_constraint_set(self.reviewed_mapping)
        if self.reviewed_constraint_set != expected_set:
            raise ValueError("Liability artifact constraint set is not reproducible.")
        expected_evaluation = evaluate_liability_constraints(
            expected_set,
            self.reviewed_mapping.facts,
        )
        if self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Liability artifact evaluation is not reproducible.")
        return self


def _facts(**updates: bool) -> LiabilityFactSet:
    values = {
        "breach_established": True,
        "debtor_acting_in_business": True,
        "fault_rebuttal_asserted": False,
        "reasonable_care_proven": False,
        "all_reasonable_measures_proven": False,
        "force_majeure_claimed": False,
        "extraordinary_event_proven": False,
        "unavoidable_event_proven": False,
        "beyond_debtor_control_proven": False,
        "force_majeure_causal_link_proven": False,
        "excluded_commercial_risk_only": False,
        "notice_and_mitigation_proven": False,
        "intentional_breach": False,
        "advance_liability_exclusion_clause": False,
        "penalty_claimed": False,
        "contractual_penalty": False,
        "penalty_reduction_requested": False,
        "manifest_disproportionality_proven": False,
        "unjustified_benefit_risk_proven": False,
        "only_excluded_reduction_reasons": False,
    }
    values.update(updates)
    return LiabilityFactSet(**values)


SYNTHETIC_LIABILITY_BENCHMARKS = (
    LiabilityBenchmarkTask(
        id="liability-bench-general-fault-not-rebutted",
        title_ru="Обычный должник не опроверг презумпцию вины",
        facts=_facts(debtor_acting_in_business=False, fault_rebuttal_asserted=True),
        expected_outcomes={"fault_rebutted": False, "liability_issue": True},
    ),
    LiabilityBenchmarkTask(
        id="liability-bench-general-fault-rebutted",
        title_ru="Обычный должник доказал заботливость и все разумные меры",
        facts=_facts(
            debtor_acting_in_business=False,
            fault_rebuttal_asserted=True,
            reasonable_care_proven=True,
            all_reasonable_measures_proven=True,
        ),
        expected_outcomes={
            "fault_rebutted": True,
            "exemption_prerequisites_satisfied": True,
            "liability_issue": False,
        },
    ),
    LiabilityBenchmarkTask(
        id="liability-bench-business-force-majeure",
        title_ru="Предприниматель доказал полный набор признаков непреодолимой силы",
        facts=_facts(
            force_majeure_claimed=True,
            extraordinary_event_proven=True,
            unavoidable_event_proven=True,
            beyond_debtor_control_proven=True,
            force_majeure_causal_link_proven=True,
            notice_and_mitigation_proven=True,
        ),
        expected_outcomes={
            "force_majeure_qualified": True,
            "exemption_prerequisites_satisfied": True,
            "liability_issue": False,
        },
    ),
    LiabilityBenchmarkTask(
        id="liability-bench-force-majeure-notice-gap",
        title_ru="Квалифицированная непреодолимая сила не устраняет обязанность уведомления",
        facts=_facts(
            force_majeure_claimed=True,
            extraordinary_event_proven=True,
            unavoidable_event_proven=True,
            beyond_debtor_control_proven=True,
            force_majeure_causal_link_proven=True,
            notice_and_mitigation_proven=False,
        ),
        expected_outcomes={
            "force_majeure_qualified": True,
            "force_majeure_notice_gap": True,
        },
    ),
    LiabilityBenchmarkTask(
        id="liability-bench-business-penalty-no-request",
        title_ru="Для предпринимателя отсутствует заявление о снижении неустойки",
        facts=_facts(
            penalty_claimed=True,
            contractual_penalty=True,
            manifest_disproportionality_proven=True,
            unjustified_benefit_risk_proven=True,
        ),
        expected_outcomes={
            "penalty_reduction_procedurally_available": False,
            "penalty_reduction_prerequisites_satisfied": False,
        },
    ),
    LiabilityBenchmarkTask(
        id="liability-bench-business-contractual-penalty",
        title_ru="Предприниматель доказал полный набор предпосылок снижения",
        facts=_facts(
            penalty_claimed=True,
            contractual_penalty=True,
            penalty_reduction_requested=True,
            manifest_disproportionality_proven=True,
            unjustified_benefit_risk_proven=True,
        ),
        expected_outcomes={
            "penalty_reduction_prerequisites_satisfied": True,
            "liability_survives_penalty_reduction": True,
            "requires_judicial_assessment": True,
        },
    ),
    LiabilityBenchmarkTask(
        id="liability-bench-no-unjustified-benefit",
        title_ru="Для договорной неустойки предпринимателя не доказан риск выгоды",
        facts=_facts(
            penalty_claimed=True,
            contractual_penalty=True,
            penalty_reduction_requested=True,
            manifest_disproportionality_proven=True,
            unjustified_benefit_risk_proven=False,
        ),
        expected_outcomes={
            "penalty_reduction_substantively_supported": False,
            "penalty_reduction_prerequisites_satisfied": False,
        },
    ),
    LiabilityBenchmarkTask(
        id="liability-bench-excluded-reduction-reasons",
        title_ru="Тяжелое финансовое положение само по себе не образует основание",
        facts=_facts(
            penalty_claimed=True,
            contractual_penalty=True,
            penalty_reduction_requested=True,
            only_excluded_reduction_reasons=True,
        ),
        expected_outcomes={
            "invalid_penalty_reduction_basis": True,
            "penalty_reduction_prerequisites_satisfied": False,
        },
    ),
    LiabilityBenchmarkTask(
        id="liability-bench-intentional-exclusion-invalid",
        title_ru="Заранее согласованное исключение умышленной ответственности недопустимо",
        facts=_facts(
            intentional_breach=True,
            advance_liability_exclusion_clause=True,
        ),
        expected_outcomes={"intentional_exclusion_invalid": True},
    ),
    LiabilityBenchmarkTask(
        id="liability-bench-no-breach",
        title_ru="Без установленного нарушения вопрос ответственности не формируется",
        facts=_facts(breach_established=False),
        expected_outcomes={"liability_issue": False},
    ),
)


SYNTHETIC_LIABILITY_RED_TEAM_CASES = (
    LiabilityRedTeamCase(
        id="liability-redteam-counterparty-default-force-majeure",
        title_ru="Подмена непреодолимой силы нарушением контрагента",
        facts=_facts(
            force_majeure_claimed=True,
            extraordinary_event_proven=True,
            unavoidable_event_proven=True,
            beyond_debtor_control_proven=True,
            force_majeure_causal_link_proven=True,
            excluded_commercial_risk_only=True,
        ),
        forbidden_outcomes={"force_majeure_qualified": True},
    ),
    LiabilityRedTeamCase(
        id="liability-redteam-ordinary-event",
        title_ru="Признание обычного события чрезвычайным",
        facts=_facts(
            force_majeure_claimed=True,
            extraordinary_event_proven=False,
            unavoidable_event_proven=True,
            beyond_debtor_control_proven=True,
            force_majeure_causal_link_proven=True,
        ),
        forbidden_outcomes={"force_majeure_qualified": True},
    ),
    LiabilityRedTeamCase(
        id="liability-redteam-avoidable-event",
        title_ru="Признание предотвратимого события непреодолимой силой",
        facts=_facts(
            force_majeure_claimed=True,
            extraordinary_event_proven=True,
            unavoidable_event_proven=False,
            beyond_debtor_control_proven=True,
            force_majeure_causal_link_proven=True,
        ),
        forbidden_outcomes={"force_majeure_qualified": True},
    ),
    LiabilityRedTeamCase(
        id="liability-redteam-no-causal-link",
        title_ru="Освобождение без связи события с нарушением",
        facts=_facts(
            force_majeure_claimed=True,
            extraordinary_event_proven=True,
            unavoidable_event_proven=True,
            beyond_debtor_control_proven=True,
            force_majeure_causal_link_proven=False,
        ),
        forbidden_outcomes={"exemption_prerequisites_satisfied": True},
    ),
    LiabilityRedTeamCase(
        id="liability-redteam-business-penalty-without-request",
        title_ru="Снижение неустойки предпринимателя без заявления",
        facts=_facts(
            penalty_claimed=True,
            contractual_penalty=True,
            manifest_disproportionality_proven=True,
            unjustified_benefit_risk_proven=True,
        ),
        forbidden_outcomes={"penalty_reduction_prerequisites_satisfied": True},
    ),
    LiabilityRedTeamCase(
        id="liability-redteam-financial-hardship-only",
        title_ru="Снижение только из-за финансовых трудностей",
        facts=_facts(
            penalty_claimed=True,
            contractual_penalty=True,
            penalty_reduction_requested=True,
            only_excluded_reduction_reasons=True,
        ),
        forbidden_outcomes={"penalty_reduction_prerequisites_satisfied": True},
    ),
    LiabilityRedTeamCase(
        id="liability-redteam-no-benefit-risk",
        title_ru="Снижение договорной неустойки без риска необоснованной выгоды",
        facts=_facts(
            penalty_claimed=True,
            contractual_penalty=True,
            penalty_reduction_requested=True,
            manifest_disproportionality_proven=True,
            unjustified_benefit_risk_proven=False,
        ),
        forbidden_outcomes={"penalty_reduction_prerequisites_satisfied": True},
    ),
    LiabilityRedTeamCase(
        id="liability-redteam-erase-liability",
        title_ru="Использование снижения неустойки для устранения ответственности",
        facts=_facts(
            penalty_claimed=True,
            contractual_penalty=True,
            penalty_reduction_requested=True,
            manifest_disproportionality_proven=True,
            unjustified_benefit_risk_proven=True,
        ),
        forbidden_outcomes={"liability_survives_penalty_reduction": False},
    ),
    LiabilityRedTeamCase(
        id="liability-redteam-intentional-exclusion",
        title_ru="Применение оговорки об исключении умышленной ответственности",
        facts=_facts(
            intentional_breach=True,
            advance_liability_exclusion_clause=True,
        ),
        forbidden_outcomes={"intentional_exclusion_invalid": False},
    ),
    LiabilityRedTeamCase(
        id="liability-redteam-presume-exemption",
        title_ru="Освобождение предпринимателя только по заявлению без доказательств",
        facts=_facts(force_majeure_claimed=True),
        forbidden_outcomes={"exemption_prerequisites_satisfied": True},
    ),
)


def _evaluate(label: str, facts: LiabilityFactSet) -> LiabilityEvaluation:
    mapping = LiabilityEvidenceMappingResult(
        evidence_id=f"liability-evaluation:{label}",
        schema_version=LIABILITY_EVIDENCE_SCHEMA_VERSION,
        mapping_version=LIABILITY_MAPPING_VERSION,
        facts=facts,
        legal_source_refs=[
            "synthetic-ru-gk401-liability-model-v1",
            "synthetic-ru-gk333-penalty-model-v1",
            "synthetic-ru-plenum7-liability-guidance-v1",
        ],
    )
    return evaluate_liability_constraints(build_liability_constraint_set(mapping), facts)


def run_liability_benchmark_suite() -> LiabilityBenchmarkReport:
    results = []
    for task in SYNTHETIC_LIABILITY_BENCHMARKS:
        evaluation = _evaluate(task.id, task.facts)
        observed = {
            field_name: getattr(evaluation, field_name)
            for field_name in task.expected_outcomes
        }
        passed = observed == task.expected_outcomes
        results.append(
            LiabilityBenchmarkResult(
                task_id=task.id,
                passed=passed,
                observed_outcomes=observed,
                reasons_ru=[
                    "Ожидаемые формальные предпосылки подтверждены."
                    if passed
                    else "Формальная модель не подтвердила ожидаемые предпосылки."
                ],
            )
        )
    passed = sum(result.passed for result in results)
    return LiabilityBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_liability_red_team_suite() -> LiabilityRedTeamReport:
    results = []
    for case in SYNTHETIC_LIABILITY_RED_TEAM_CASES:
        evaluation = _evaluate(case.id, case.facts)
        observed = {
            field_name: getattr(evaluation, field_name)
            for field_name in case.forbidden_outcomes
        }
        blocked = observed != case.forbidden_outcomes
        results.append(
            LiabilityRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                observed_outcomes=observed,
                reasons_ru=[
                    "Формальные ограничения отклонили требуемый атакой результат."
                    if blocked
                    else "Атакующий результат не был заблокирован."
                ],
            )
        )
    blocked = sum(result.blocked for result in results)
    return LiabilityRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
