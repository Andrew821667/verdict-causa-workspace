from pydantic import BaseModel, Field

from causa.institutional.contracts.research_work import (
    ResearchWorkConstraintSet,
    ResearchWorkEvaluation,
    ResearchWorkEvidenceMappingResult,
    ResearchWorkFactSet,
    build_research_work_constraint_set,
    evaluate_research_work_constraints,
)


class ResearchWorkEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ResearchWorkFactSet
    expected_outcomes: dict[str, bool]


class ResearchWorkEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ResearchWorkBenchmarkReport(BaseModel):
    id: str = "research-work-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ResearchWorkEvaluationResult] = Field(default_factory=list)


class ResearchWorkRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ResearchWorkFactSet
    forbidden_outcomes: dict[str, bool]


class ResearchWorkRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ResearchWorkRedTeamReport(BaseModel):
    id: str = "research-work-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ResearchWorkRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ResearchWorkFactSet:
    values = {field_name: False for field_name in ResearchWorkFactSet.model_fields}
    values.update(updates)
    return ResearchWorkFactSet(**values)


SYNTHETIC_RESEARCH_WORK_BENCHMARKS = (
    ResearchWorkEvaluationTask(
        id="research-work-bench-not-qualified",
        title_ru="Научно-исследовательские и опытно-конструкторские работы не выполняются",
        facts=_facts(confidentiality_or_publication_duty_breached=True),
        expected_outcomes={"research_work_qualified": False},
    ),
    ResearchWorkEvaluationTask(
        id="research-work-bench-qualified-clean",
        title_ru="Договор на выполнение НИР и ОКР без нарушений",
        facts=_facts(research_or_development_work_performed_for_fee=True),
        expected_outcomes={
            "research_work_qualified": True,
            "requires_human_research_work_assessment": False,
        },
    ),
    ResearchWorkEvaluationTask(
        id="research-work-bench-personal-performance",
        title_ru="Третьи лица привлечены к научным исследованиям без согласия заказчика",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            third_party_engaged_without_consent_in_research=True,
        ),
        expected_outcomes={
            "personal_performance_duty_breached": True,
            "requires_human_research_work_assessment": True,
        },
    ),
    ResearchWorkEvaluationTask(
        id="research-work-bench-confidentiality",
        title_ru="Нарушена конфиденциальность сведений о предмете договора",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            confidentiality_or_publication_duty_breached=True,
        ),
        expected_outcomes={
            "confidentiality_duty_breached": True,
            "requires_human_research_work_assessment": True,
        },
    ),
    ResearchWorkEvaluationTask(
        id="research-work-bench-result-use-rights",
        title_ru="Не определены пределы и условия использования результатов работ",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            result_use_rights_not_agreed=True,
        ),
        expected_outcomes={
            "result_use_rights_missing": True,
            "requires_human_research_work_assessment": True,
        },
    ),
    ResearchWorkEvaluationTask(
        id="research-work-bench-third-party-rights",
        title_ru="Переданные результаты нарушают исключительные права других лиц",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            third_party_exclusive_rights_infringed=True,
        ),
        expected_outcomes={
            "third_party_rights_guarantee_breached": True,
            "requires_human_research_work_assessment": True,
        },
    ),
    ResearchWorkEvaluationTask(
        id="research-work-bench-impossibility-notice",
        title_ru="Исполнитель не сообщил незамедлительно о невозможности получить результат",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            impossibility_not_reported_immediately=True,
        ),
        expected_outcomes={
            "impossibility_notice_duty_breached": True,
            "requires_human_research_work_assessment": True,
        },
    ),
    ResearchWorkEvaluationTask(
        id="research-work-bench-customer-duties",
        title_ru="Заказчик не передал информацию и не принял результаты работ",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            customer_information_or_acceptance_duty_unmet=True,
        ),
        expected_outcomes={
            "customer_duties_breached": True,
            "requires_human_research_work_assessment": True,
        },
    ),
    ResearchWorkEvaluationTask(
        id="research-work-bench-impossibility-payment",
        title_ru="Работы до выявления невозможности не оплачены",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            result_unachievable_without_performer_fault=True,
            pre_impossibility_costs_not_paid=True,
        ),
        expected_outcomes={
            "impossibility_without_fault_established": True,
            "pre_impossibility_payment_due": True,
            "requires_human_research_work_assessment": True,
        },
    ),
    ResearchWorkEvaluationTask(
        id="research-work-bench-performer-liability",
        title_ru="Исполнитель не доказал отсутствие своей вины в нарушении договора",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            performer_breach_without_proof_of_absent_fault=True,
        ),
        expected_outcomes={
            "performer_liability_established": True,
            "requires_human_research_work_assessment": True,
        },
    ),
)


SYNTHETIC_RESEARCH_WORK_RED_TEAM_CASES = (
    ResearchWorkRedTeamCase(
        id="research-work-red-qualify-without-work",
        title_ru="Квалифицировать договор на НИР и ОКР без выполнения таких работ",
        facts=_facts(confidentiality_or_publication_duty_breached=True),
        forbidden_outcomes={"research_work_qualified": True},
    ),
    ResearchWorkRedTeamCase(
        id="research-work-red-allow-third-party",
        title_ru="Признать допустимым привлечение третьих лиц к НИР без согласия заказчика",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            third_party_engaged_without_consent_in_research=True,
        ),
        forbidden_outcomes={"personal_performance_duty_breached": False},
    ),
    ResearchWorkRedTeamCase(
        id="research-work-red-ignore-confidentiality",
        title_ru="Игнорировать нарушение конфиденциальности сведений",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            confidentiality_or_publication_duty_breached=True,
        ),
        forbidden_outcomes={"confidentiality_duty_breached": False},
    ),
    ResearchWorkRedTeamCase(
        id="research-work-red-ignore-result-use-rights",
        title_ru="Игнорировать отсутствие условий об использовании результатов работ",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            result_use_rights_not_agreed=True,
        ),
        forbidden_outcomes={"result_use_rights_missing": False},
    ),
    ResearchWorkRedTeamCase(
        id="research-work-red-ignore-third-party-rights",
        title_ru="Игнорировать нарушение исключительных прав других лиц",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            third_party_exclusive_rights_infringed=True,
        ),
        forbidden_outcomes={"third_party_rights_guarantee_breached": False},
    ),
    ResearchWorkRedTeamCase(
        id="research-work-red-ignore-impossibility-notice",
        title_ru="Игнорировать несообщение о невозможности получить результат",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            impossibility_not_reported_immediately=True,
        ),
        forbidden_outcomes={"impossibility_notice_duty_breached": False},
    ),
    ResearchWorkRedTeamCase(
        id="research-work-red-ignore-customer-duties",
        title_ru="Игнорировать непередачу информации и отказ заказчика принять результаты",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            customer_information_or_acceptance_duty_unmet=True,
        ),
        forbidden_outcomes={"customer_duties_breached": False},
    ),
    ResearchWorkRedTeamCase(
        id="research-work-red-payment-without-impossibility",
        title_ru="Признать расчёты при невозможности без самой невозможности",
        facts=_facts(research_or_development_work_performed_for_fee=True),
        forbidden_outcomes={"pre_impossibility_payment_due": True},
    ),
    ResearchWorkRedTeamCase(
        id="research-work-red-excuse-performer",
        title_ru="Освободить исполнителя от ответственности без доказательства отсутствия вины",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            performer_breach_without_proof_of_absent_fault=True,
        ),
        forbidden_outcomes={"performer_liability_established": False},
    ),
    ResearchWorkRedTeamCase(
        id="research-work-red-skip-human-on-impossibility",
        title_ru="Пропустить экспертизу при невозможности достижения результата",
        facts=_facts(
            research_or_development_work_performed_for_fee=True,
            result_unachievable_without_performer_fault=True,
        ),
        forbidden_outcomes={"requires_human_research_work_assessment": False},
    ),
)


def _evaluate(facts: ResearchWorkFactSet, artifact_id: str) -> ResearchWorkEvaluation:
    mapping = ResearchWorkEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-research-work-law"],
    )
    constraints: ResearchWorkConstraintSet = build_research_work_constraint_set(mapping)
    return evaluate_research_work_constraints(constraints, facts)


def _outcomes(evaluation: ResearchWorkEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_research_work_benchmark_suite() -> ResearchWorkBenchmarkReport:
    results = []
    for task in SYNTHETIC_RESEARCH_WORK_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ResearchWorkEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ResearchWorkBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_research_work_red_team_suite() -> ResearchWorkRedTeamReport:
    results = []
    for case in SYNTHETIC_RESEARCH_WORK_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            ResearchWorkRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return ResearchWorkRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
