from pydantic import BaseModel, Field

from causa.institutional.contracts.freedom import (
    FreedomConstraintSet,
    FreedomEvaluation,
    FreedomEvidenceMappingResult,
    FreedomFactSet,
    build_freedom_constraint_set,
    evaluate_freedom_constraints,
)


class FreedomEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: FreedomFactSet
    expected_outcomes: dict[str, bool]


class FreedomEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FreedomBenchmarkReport(BaseModel):
    id: str = "freedom-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[FreedomEvaluationResult] = Field(default_factory=list)


class FreedomRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: FreedomFactSet
    forbidden_outcomes: dict[str, bool]


class FreedomRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class FreedomRedTeamReport(BaseModel):
    id: str = "freedom-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[FreedomRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> FreedomFactSet:
    values = {field_name: False for field_name in FreedomFactSet.model_fields}
    values.update(updates)
    return FreedomFactSet(**values)


SYNTHETIC_FREEDOM_BENCHMARKS = (
    FreedomEvaluationTask(
        id="freedom-bench-free-conclusion",
        title_ru="Свободное заключение договора с согласованной ценой",
        facts=_facts(price_agreed_by_parties=True),
        expected_outcomes={
            "contract_conclusion_free": True,
            "terms_by_party_discretion": True,
            "requires_human_freedom_assessment": False,
        },
    ),
    FreedomEvaluationTask(
        id="freedom-bench-compelled",
        title_ru="Заключение договора обязательно в силу закона",
        facts=_facts(
            contract_conclusion_compelled_by_law=True,
            price_agreed_by_parties=True,
        ),
        expected_outcomes={"contract_conclusion_free": False},
    ),
    FreedomEvaluationTask(
        id="freedom-bench-mandatory-terms",
        title_ru="Содержание условия предписано императивной нормой",
        facts=_facts(
            terms_prescribed_by_mandatory_norm=True,
            price_agreed_by_parties=True,
        ),
        expected_outcomes={"terms_by_party_discretion": False},
    ),
    FreedomEvaluationTask(
        id="freedom-bench-mixed",
        title_ru="Смешанный договор с элементами различных договоров",
        facts=_facts(
            mixed_contract_elements=True,
            price_agreed_by_parties=True,
        ),
        expected_outcomes={
            "mixed_contract_rules_apply": True,
            "requires_human_freedom_assessment": True,
        },
    ),
    FreedomEvaluationTask(
        id="freedom-bench-unnamed",
        title_ru="Непоименованный договор, не предусмотренный законом",
        facts=_facts(
            contract_type_unnamed=True,
            price_agreed_by_parties=True,
        ),
        expected_outcomes={"requires_human_freedom_assessment": True},
    ),
    FreedomEvaluationTask(
        id="freedom-bench-conforms",
        title_ru="Договор соответствует императивным нормам на момент заключения",
        facts=_facts(
            contract_conforms_mandatory_rules=True,
            price_agreed_by_parties=True,
        ),
        expected_outcomes={"contract_valid_against_mandatory_rules": True},
    ),
    FreedomEvaluationTask(
        id="freedom-bench-prior-terms-survive",
        title_ru="Новый закон без обратной силы — условия сохраняются",
        facts=_facts(
            new_mandatory_law_after_conclusion=True,
            price_agreed_by_parties=True,
        ),
        expected_outcomes={
            "prior_terms_survive_new_law": True,
            "requires_human_freedom_assessment": False,
        },
    ),
    FreedomEvaluationTask(
        id="freedom-bench-retroactive",
        title_ru="Новому закону придана обратная сила",
        facts=_facts(
            new_mandatory_law_after_conclusion=True,
            new_law_given_retroactive_effect=True,
            price_agreed_by_parties=True,
        ),
        expected_outcomes={
            "prior_terms_survive_new_law": False,
            "requires_human_freedom_assessment": True,
        },
    ),
    FreedomEvaluationTask(
        id="freedom-bench-gratuitous",
        title_ru="Безвозмездный договор по существу отношений",
        facts=_facts(contract_gratuitous_by_nature=True),
        expected_outcomes={
            "contract_presumed_onerous": False,
            "price_determined": False,
            "requires_human_freedom_assessment": False,
        },
    ),
    FreedomEvaluationTask(
        id="freedom-bench-price-comparable",
        title_ru="Возмездный договор без согласованной цены — цена по сопоставимым",
        facts=_facts(comparable_price_available=True),
        expected_outcomes={
            "price_determined": True,
            "requires_human_freedom_assessment": True,
        },
    ),
)


SYNTHETIC_FREEDOM_RED_TEAM_CASES = (
    FreedomRedTeamCase(
        id="freedom-red-free-when-compelled",
        title_ru="Считать заключение свободным при обязанности заключить договор",
        facts=_facts(contract_conclusion_compelled_by_law=True),
        forbidden_outcomes={"contract_conclusion_free": True},
    ),
    FreedomRedTeamCase(
        id="freedom-red-discretion-when-mandatory",
        title_ru="Считать условия усмотрением сторон при императивной норме",
        facts=_facts(terms_prescribed_by_mandatory_norm=True),
        forbidden_outcomes={"terms_by_party_discretion": True},
    ),
    FreedomRedTeamCase(
        id="freedom-red-valid-without-conformance",
        title_ru="Признать действительность без соответствия императивным нормам",
        facts=_facts(price_agreed_by_parties=True),
        forbidden_outcomes={"contract_valid_against_mandatory_rules": True},
    ),
    FreedomRedTeamCase(
        id="freedom-red-survive-when-retroactive",
        title_ru="Сохранять прежние условия при обратной силе нового закона",
        facts=_facts(
            new_mandatory_law_after_conclusion=True,
            new_law_given_retroactive_effect=True,
        ),
        forbidden_outcomes={"prior_terms_survive_new_law": True},
    ),
    FreedomRedTeamCase(
        id="freedom-red-onerous-when-gratuitous",
        title_ru="Предполагать возмездность при безвозмездности по существу",
        facts=_facts(contract_gratuitous_by_nature=True),
        forbidden_outcomes={"contract_presumed_onerous": True},
    ),
    FreedomRedTeamCase(
        id="freedom-red-price-without-basis",
        title_ru="Считать цену определённой без согласования, регулирования и сопоставимой",
        facts=_facts(contract_gratuitous_by_nature=True),
        forbidden_outcomes={"price_determined": True},
    ),
    FreedomRedTeamCase(
        id="freedom-red-skip-mixed-rules",
        title_ru="Игнорировать правила о смешанном договоре",
        facts=_facts(
            mixed_contract_elements=True,
            price_agreed_by_parties=True,
        ),
        forbidden_outcomes={"mixed_contract_rules_apply": False},
    ),
    FreedomRedTeamCase(
        id="freedom-red-skip-human-on-unnamed",
        title_ru="Пропустить экспертную проверку для непоименованного договора",
        facts=_facts(
            contract_type_unnamed=True,
            price_agreed_by_parties=True,
        ),
        forbidden_outcomes={"requires_human_freedom_assessment": False},
    ),
    FreedomRedTeamCase(
        id="freedom-red-skip-human-on-price-gap",
        title_ru="Пропустить экспертизу при определении цены по сопоставимым",
        facts=_facts(comparable_price_available=True),
        forbidden_outcomes={"requires_human_freedom_assessment": False},
    ),
    FreedomRedTeamCase(
        id="freedom-red-compelled-without-basis",
        title_ru="Считать заключение несвободным при отсутствии понуждения",
        facts=_facts(price_agreed_by_parties=True),
        forbidden_outcomes={"contract_conclusion_free": False},
    ),
)


def _evaluate(facts: FreedomFactSet, artifact_id: str) -> FreedomEvaluation:
    mapping = FreedomEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-freedom-law"],
    )
    constraints: FreedomConstraintSet = build_freedom_constraint_set(mapping)
    return evaluate_freedom_constraints(constraints, facts)


def _outcomes(evaluation: FreedomEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_freedom_benchmark_suite() -> FreedomBenchmarkReport:
    results = []
    for task in SYNTHETIC_FREEDOM_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            FreedomEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return FreedomBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_freedom_red_team_suite() -> FreedomRedTeamReport:
    results = []
    for case in SYNTHETIC_FREEDOM_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            FreedomRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return FreedomRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
