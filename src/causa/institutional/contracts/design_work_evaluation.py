from pydantic import BaseModel, Field

from causa.institutional.contracts.design_work import (
    DesignWorkConstraintSet,
    DesignWorkEvaluation,
    DesignWorkEvidenceMappingResult,
    DesignWorkFactSet,
    build_design_work_constraint_set,
    evaluate_design_work_constraints,
)


class DesignWorkEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: DesignWorkFactSet
    expected_outcomes: dict[str, bool]


class DesignWorkEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class DesignWorkBenchmarkReport(BaseModel):
    id: str = "design-work-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[DesignWorkEvaluationResult] = Field(default_factory=list)


class DesignWorkRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: DesignWorkFactSet
    forbidden_outcomes: dict[str, bool]


class DesignWorkRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class DesignWorkRedTeamReport(BaseModel):
    id: str = "design-work-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[DesignWorkRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> DesignWorkFactSet:
    values = {field_name: False for field_name in DesignWorkFactSet.model_fields}
    values.update(updates)
    return DesignWorkFactSet(**values)


SYNTHETIC_DESIGN_WORK_BENCHMARKS = (
    DesignWorkEvaluationTask(
        id="design-work-bench-not-qualified",
        title_ru="Проектные и изыскательские работы по заданию заказчика не выполняются",
        facts=_facts(documentation_or_survey_defective=True),
        expected_outcomes={"design_work_qualified": False},
    ),
    DesignWorkEvaluationTask(
        id="design-work-bench-qualified-clean",
        title_ru="Договор на проектные и изыскательские работы без нарушений",
        facts=_facts(design_or_survey_work_performed_for_fee=True),
        expected_outcomes={
            "design_work_qualified": True,
            "requires_human_design_work_assessment": False,
        },
    ),
    DesignWorkEvaluationTask(
        id="design-work-bench-initial-data",
        title_ru="Заказчик не передал задание и исходные данные",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            assignment_or_initial_data_not_provided=True,
        ),
        expected_outcomes={
            "initial_data_duty_breached": True,
            "requires_human_design_work_assessment": True,
        },
    ),
    DesignWorkEvaluationTask(
        id="design-work-bench-assignment-deviation",
        title_ru="Подрядчик отступил от требований задания без согласия заказчика",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            assignment_requirements_deviated_without_consent=True,
        ),
        expected_outcomes={
            "assignment_deviation_unauthorized": True,
            "requires_human_design_work_assessment": True,
        },
    ),
    DesignWorkEvaluationTask(
        id="design-work-bench-approval",
        title_ru="Документация не согласована с заказчиком и компетентными органами",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            documentation_not_agreed_with_authorities=True,
        ),
        expected_outcomes={
            "approval_duty_breached": True,
            "requires_human_design_work_assessment": True,
        },
    ),
    DesignWorkEvaluationTask(
        id="design-work-bench-disclosure",
        title_ru="Документация передана третьим лицам без согласия другой стороны",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            documentation_disclosed_to_third_party_without_consent=True,
        ),
        expected_outcomes={
            "documentation_confidentiality_breached": True,
            "requires_human_design_work_assessment": True,
        },
    ),
    DesignWorkEvaluationTask(
        id="design-work-bench-third-party-right",
        title_ru="Третьи лица вправе воспрепятствовать выполнению работ",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            third_party_right_obstructs_work=True,
        ),
        expected_outcomes={
            "third_party_obstruction_risk": True,
            "requires_human_design_work_assessment": True,
        },
    ),
    DesignWorkEvaluationTask(
        id="design-work-bench-later-defect",
        title_ru="Недостаток документации выявлен в ходе строительства объекта",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            documentation_or_survey_defective=True,
            defect_revealed_during_construction_or_use=True,
        ),
        expected_outcomes={
            "designer_liable_for_defects": True,
            "later_discovered_defect_claim": True,
            "requires_human_design_work_assessment": True,
        },
    ),
    DesignWorkEvaluationTask(
        id="design-work-bench-customer-duties",
        title_ru="Заказчик не оплатил работы и не оказал содействие",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            customer_payment_or_assistance_duty_unmet=True,
        ),
        expected_outcomes={
            "customer_payment_or_assistance_breached": True,
            "requires_human_design_work_assessment": True,
        },
    ),
    DesignWorkEvaluationTask(
        id="design-work-bench-extra-costs",
        title_ru="Не возмещены расходы, вызванные изменением исходных данных",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            extra_costs_from_changed_initial_data_not_compensated=True,
        ),
        expected_outcomes={
            "extra_costs_compensation_due": True,
            "requires_human_design_work_assessment": True,
        },
    ),
)


SYNTHETIC_DESIGN_WORK_RED_TEAM_CASES = (
    DesignWorkRedTeamCase(
        id="design-work-red-qualify-without-work",
        title_ru="Квалифицировать проектный подряд без выполнения работ по заданию заказчика",
        facts=_facts(documentation_or_survey_defective=True),
        forbidden_outcomes={"design_work_qualified": True},
    ),
    DesignWorkRedTeamCase(
        id="design-work-red-ignore-initial-data",
        title_ru="Игнорировать непередачу задания и исходных данных заказчиком",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            assignment_or_initial_data_not_provided=True,
        ),
        forbidden_outcomes={"initial_data_duty_breached": False},
    ),
    DesignWorkRedTeamCase(
        id="design-work-red-allow-deviation",
        title_ru="Признать допустимым отступление от задания без согласия заказчика",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            assignment_requirements_deviated_without_consent=True,
        ),
        forbidden_outcomes={"assignment_deviation_unauthorized": False},
    ),
    DesignWorkRedTeamCase(
        id="design-work-red-ignore-approval",
        title_ru="Игнорировать отсутствие согласования документации с органами",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            documentation_not_agreed_with_authorities=True,
        ),
        forbidden_outcomes={"approval_duty_breached": False},
    ),
    DesignWorkRedTeamCase(
        id="design-work-red-allow-disclosure",
        title_ru="Признать правомерной передачу документации третьим лицам без согласия",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            documentation_disclosed_to_third_party_without_consent=True,
        ),
        forbidden_outcomes={"documentation_confidentiality_breached": False},
    ),
    DesignWorkRedTeamCase(
        id="design-work-red-ignore-third-party-right",
        title_ru="Игнорировать право третьих лиц воспрепятствовать выполнению работ",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            third_party_right_obstructs_work=True,
        ),
        forbidden_outcomes={"third_party_obstruction_risk": False},
    ),
    DesignWorkRedTeamCase(
        id="design-work-red-excuse-defects",
        title_ru="Освободить подрядчика от ответственности за недостатки документации",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            documentation_or_survey_defective=True,
        ),
        forbidden_outcomes={"designer_liable_for_defects": False},
    ),
    DesignWorkRedTeamCase(
        id="design-work-red-claim-without-defect",
        title_ru="Признать требование по недостаткам, выявленным позднее, без самого недостатка",
        facts=_facts(design_or_survey_work_performed_for_fee=True),
        forbidden_outcomes={"later_discovered_defect_claim": True},
    ),
    DesignWorkRedTeamCase(
        id="design-work-red-ignore-customer-duties",
        title_ru="Игнорировать неоплату работ и отсутствие содействия заказчика",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            customer_payment_or_assistance_duty_unmet=True,
        ),
        forbidden_outcomes={"customer_payment_or_assistance_breached": False},
    ),
    DesignWorkRedTeamCase(
        id="design-work-red-skip-human-on-extra-costs",
        title_ru="Пропустить экспертизу при невозмещении расходов из-за изменения данных",
        facts=_facts(
            design_or_survey_work_performed_for_fee=True,
            extra_costs_from_changed_initial_data_not_compensated=True,
        ),
        forbidden_outcomes={"requires_human_design_work_assessment": False},
    ),
)


def _evaluate(facts: DesignWorkFactSet, artifact_id: str) -> DesignWorkEvaluation:
    mapping = DesignWorkEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-design-work-law"],
    )
    constraints: DesignWorkConstraintSet = build_design_work_constraint_set(mapping)
    return evaluate_design_work_constraints(constraints, facts)


def _outcomes(evaluation: DesignWorkEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_design_work_benchmark_suite() -> DesignWorkBenchmarkReport:
    results = []
    for task in SYNTHETIC_DESIGN_WORK_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            DesignWorkEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return DesignWorkBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_design_work_red_team_suite() -> DesignWorkRedTeamReport:
    results = []
    for case in SYNTHETIC_DESIGN_WORK_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            DesignWorkRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return DesignWorkRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
