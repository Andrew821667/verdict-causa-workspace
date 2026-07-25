from pydantic import BaseModel, Field

from causa.institutional.contracts.precontractual import (
    PrecontractualConstraintSet,
    PrecontractualEvaluation,
    PrecontractualEvidenceMappingResult,
    PrecontractualFactSet,
    build_precontractual_constraint_set,
    evaluate_precontractual_constraints,
)


class PrecontractualEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: PrecontractualFactSet
    expected_outcomes: dict[str, bool]


class PrecontractualEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PrecontractualBenchmarkReport(BaseModel):
    id: str = "precontractual-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[PrecontractualEvaluationResult] = Field(default_factory=list)


class PrecontractualRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: PrecontractualFactSet
    forbidden_outcomes: dict[str, bool]


class PrecontractualRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class PrecontractualRedTeamReport(BaseModel):
    id: str = "precontractual-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[PrecontractualRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> PrecontractualFactSet:
    values = {field_name: False for field_name in PrecontractualFactSet.model_fields}
    values.update(updates)
    return PrecontractualFactSet(**values)


SYNTHETIC_PRECONTRACTUAL_BENCHMARKS = (
    PrecontractualEvaluationTask(
        id="precontractual-bench-clean",
        title_ru="Добросовестные переговоры без нарушений",
        facts=_facts(negotiations_entered=True),
        expected_outcomes={
            "bad_faith_negotiation": False,
            "precontractual_liability_present": False,
            "requires_human_precontractual_assessment": False,
        },
    ),
    PrecontractualEvaluationTask(
        id="precontractual-bench-false-information",
        title_ru="Предоставление недостоверной информации при переговорах",
        facts=_facts(
            negotiations_entered=True,
            incomplete_or_false_information_provided=True,
            losses_incurred=True,
            damages_claimed=True,
        ),
        expected_outcomes={
            "bad_faith_negotiation": True,
            "damages_available": True,
            "requires_human_precontractual_assessment": True,
        },
    ),
    PrecontractualEvaluationTask(
        id="precontractual-bench-expected-breakoff",
        title_ru="Прекращение переговоров, которое сторона могла разумно ожидать",
        facts=_facts(
            negotiations_entered=True,
            abrupt_unjustified_breakoff=True,
        ),
        expected_outcomes={"bad_faith_negotiation": False},
    ),
    PrecontractualEvaluationTask(
        id="precontractual-bench-sudden-breakoff",
        title_ru="Внезапное и неоправданное прекращение переговоров",
        facts=_facts(
            negotiations_entered=True,
            abrupt_unjustified_breakoff=True,
            counterparty_could_not_reasonably_expect_breakoff=True,
            losses_incurred=True,
            damages_claimed=True,
        ),
        expected_outcomes={
            "bad_faith_negotiation": True,
            "damages_available": True,
        },
    ),
    PrecontractualEvaluationTask(
        id="precontractual-bench-confidentiality",
        title_ru="Нарушение конфиденциальности сведений, полученных в переговорах",
        facts=_facts(
            negotiations_entered=True,
            confidential_information_received=True,
            confidential_information_misused=True,
            losses_incurred=True,
            damages_claimed=True,
        ),
        expected_outcomes={
            "confidentiality_breach": True,
            "precontractual_liability_present": True,
            "damages_available": True,
        },
    ),
    PrecontractualEvaluationTask(
        id="precontractual-bench-liability-no-claim",
        title_ru="Недобросовестность есть, но требование не заявлено",
        facts=_facts(
            negotiations_entered=True,
            incomplete_or_false_information_provided=True,
            losses_incurred=True,
        ),
        expected_outcomes={
            "precontractual_liability_present": True,
            "damages_available": False,
        },
    ),
    PrecontractualEvaluationTask(
        id="precontractual-bench-liability-no-loss",
        title_ru="Недобросовестность есть, но убытки не причинены",
        facts=_facts(
            negotiations_entered=True,
            incomplete_or_false_information_provided=True,
            damages_claimed=True,
        ),
        expected_outcomes={
            "precontractual_liability_present": True,
            "damages_available": False,
        },
    ),
    PrecontractualEvaluationTask(
        id="precontractual-bench-limitation-void",
        title_ru="Соглашение об ограничении ответственности ничтожно",
        facts=_facts(
            negotiations_entered=True,
            liability_limitation_agreement_present=True,
        ),
        expected_outcomes={
            "liability_limitation_void": True,
            "requires_human_precontractual_assessment": True,
        },
    ),
    PrecontractualEvaluationTask(
        id="precontractual-bench-confidential-not-misused",
        title_ru="Конфиденциальная информация получена, но не использована ненадлежаще",
        facts=_facts(
            negotiations_entered=True,
            confidential_information_received=True,
        ),
        expected_outcomes={
            "confidentiality_breach": False,
            "precontractual_liability_present": False,
        },
    ),
    PrecontractualEvaluationTask(
        id="precontractual-bench-no-negotiations",
        title_ru="Переговоры не велись",
        facts=_facts(
            confidential_information_received=True,
            confidential_information_misused=True,
            losses_incurred=True,
            damages_claimed=True,
        ),
        expected_outcomes={
            "bad_faith_negotiation": False,
            "confidentiality_breach": True,
        },
    ),
)


SYNTHETIC_PRECONTRACTUAL_RED_TEAM_CASES = (
    PrecontractualRedTeamCase(
        id="precontractual-red-liability-clean",
        title_ru="Возложить ответственность при добросовестных переговорах",
        facts=_facts(
            negotiations_entered=True,
            losses_incurred=True,
            damages_claimed=True,
        ),
        forbidden_outcomes={"precontractual_liability_present": True},
    ),
    PrecontractualRedTeamCase(
        id="precontractual-red-badfaith-expected-breakoff",
        title_ru="Признать недобросовестным ожидаемое прекращение переговоров",
        facts=_facts(
            negotiations_entered=True,
            abrupt_unjustified_breakoff=True,
        ),
        forbidden_outcomes={"bad_faith_negotiation": True},
    ),
    PrecontractualRedTeamCase(
        id="precontractual-red-damages-no-claim",
        title_ru="Присудить убытки без заявленного требования",
        facts=_facts(
            negotiations_entered=True,
            incomplete_or_false_information_provided=True,
            losses_incurred=True,
        ),
        forbidden_outcomes={"damages_available": True},
    ),
    PrecontractualRedTeamCase(
        id="precontractual-red-damages-no-loss",
        title_ru="Присудить убытки при отсутствии убытков",
        facts=_facts(
            negotiations_entered=True,
            incomplete_or_false_information_provided=True,
            damages_claimed=True,
        ),
        forbidden_outcomes={"damages_available": True},
    ),
    PrecontractualRedTeamCase(
        id="precontractual-red-breach-not-misused",
        title_ru="Признать нарушение конфиденциальности без ненадлежащего использования",
        facts=_facts(
            negotiations_entered=True,
            confidential_information_received=True,
        ),
        forbidden_outcomes={"confidentiality_breach": True},
    ),
    PrecontractualRedTeamCase(
        id="precontractual-red-uphold-limitation",
        title_ru="Признать действительным соглашение об ограничении ответственности",
        facts=_facts(
            negotiations_entered=True,
            liability_limitation_agreement_present=True,
        ),
        forbidden_outcomes={"liability_limitation_void": False},
    ),
    PrecontractualRedTeamCase(
        id="precontractual-red-skip-human-on-liability",
        title_ru="Пропустить экспертную проверку при недобросовестных переговорах",
        facts=_facts(
            negotiations_entered=True,
            incomplete_or_false_information_provided=True,
            losses_incurred=True,
            damages_claimed=True,
        ),
        forbidden_outcomes={"requires_human_precontractual_assessment": False},
    ),
    PrecontractualRedTeamCase(
        id="precontractual-red-skip-human-on-limitation",
        title_ru="Пропустить экспертную проверку при ничтожном ограничении ответственности",
        facts=_facts(
            negotiations_entered=True,
            liability_limitation_agreement_present=True,
        ),
        forbidden_outcomes={"requires_human_precontractual_assessment": False},
    ),
    PrecontractualRedTeamCase(
        id="precontractual-red-badfaith-without-negotiations",
        title_ru="Признать недобросовестность переговоров без их ведения",
        facts=_facts(
            confidential_information_received=True,
            confidential_information_misused=True,
        ),
        forbidden_outcomes={"bad_faith_negotiation": True},
    ),
    PrecontractualRedTeamCase(
        id="precontractual-red-ignore-confidentiality",
        title_ru="Игнорировать нарушение конфиденциальности как основание ответственности",
        facts=_facts(
            negotiations_entered=True,
            confidential_information_received=True,
            confidential_information_misused=True,
        ),
        forbidden_outcomes={"precontractual_liability_present": False},
    ),
)


def _evaluate(facts: PrecontractualFactSet, artifact_id: str) -> PrecontractualEvaluation:
    mapping = PrecontractualEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-precontractual-law"],
    )
    constraints: PrecontractualConstraintSet = build_precontractual_constraint_set(mapping)
    return evaluate_precontractual_constraints(constraints, facts)


def _outcomes(evaluation: PrecontractualEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_precontractual_benchmark_suite() -> PrecontractualBenchmarkReport:
    results = []
    for task in SYNTHETIC_PRECONTRACTUAL_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            PrecontractualEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return PrecontractualBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_precontractual_red_team_suite() -> PrecontractualRedTeamReport:
    results = []
    for case in SYNTHETIC_PRECONTRACTUAL_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            PrecontractualRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return PrecontractualRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
