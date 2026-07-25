from pydantic import BaseModel, Field

from causa.institutional.contracts.option import (
    OptionConstraintSet,
    OptionEvaluation,
    OptionEvidenceMappingResult,
    OptionFactSet,
    build_option_constraint_set,
    evaluate_option_constraints,
)


class OptionEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: OptionFactSet
    expected_outcomes: dict[str, bool]


class OptionEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class OptionBenchmarkReport(BaseModel):
    id: str = "option-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[OptionEvaluationResult] = Field(default_factory=list)


class OptionRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: OptionFactSet
    forbidden_outcomes: dict[str, bool]


class OptionRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class OptionRedTeamReport(BaseModel):
    id: str = "option-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[OptionRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> OptionFactSet:
    values = {field_name: False for field_name in OptionFactSet.model_fields}
    values.update(updates)
    return OptionFactSet(**values)


SYNTHETIC_OPTION_BENCHMARKS = (
    OptionEvaluationTask(
        id="option-bench-exercised",
        title_ru="Опцион на заключение договора акцептован в срок",
        facts=_facts(
            option_to_conclude_granted=True,
            option_essential_terms_defined=True,
            option_consideration_valid=True,
            option_acceptance_within_term=True,
        ),
        expected_outcomes={
            "option_offer_valid": True,
            "main_contract_formed_by_option": True,
            "option_lapsed_unexercised": False,
        },
    ),
    OptionEvaluationTask(
        id="option-bench-lapsed",
        title_ru="Опцион не акцептован в установленный срок",
        facts=_facts(
            option_to_conclude_granted=True,
            option_essential_terms_defined=True,
            option_consideration_valid=True,
        ),
        expected_outcomes={
            "option_lapsed_unexercised": True,
            "main_contract_formed_by_option": False,
            "requires_human_option_assessment": True,
        },
    ),
    OptionEvaluationTask(
        id="option-bench-no-consideration",
        title_ru="Опцион без действительного встречного предоставления",
        facts=_facts(
            option_to_conclude_granted=True,
            option_essential_terms_defined=True,
            option_acceptance_within_term=True,
        ),
        expected_outcomes={
            "option_offer_valid": False,
            "main_contract_formed_by_option": False,
        },
    ),
    OptionEvaluationTask(
        id="option-bench-terms-undefined",
        title_ru="Опцион без определённых существенных условий",
        facts=_facts(
            option_to_conclude_granted=True,
            option_consideration_valid=True,
            option_acceptance_within_term=True,
        ),
        expected_outcomes={"option_offer_valid": False},
    ),
    OptionEvaluationTask(
        id="option-bench-contract-enforceable",
        title_ru="Опционный договор: требование заявлено в срок",
        facts=_facts(
            option_contract_concluded=True,
            option_contract_demand_within_term=True,
        ),
        expected_outcomes={
            "option_contract_demand_enforceable": True,
            "option_contract_terminated_by_expiry": False,
        },
    ),
    OptionEvaluationTask(
        id="option-bench-contract-terminated",
        title_ru="Опционный договор прекращён истечением срока без требования",
        facts=_facts(option_contract_concluded=True),
        expected_outcomes={
            "option_contract_terminated_by_expiry": True,
            "requires_human_option_assessment": True,
        },
    ),
    OptionEvaluationTask(
        id="option-bench-payment-nonrefundable",
        title_ru="Платёж по опционному договору не возвращается при прекращении",
        facts=_facts(
            option_contract_concluded=True,
            option_contract_payment_made=True,
        ),
        expected_outcomes={
            "option_payment_non_refundable": True,
            "option_contract_terminated_by_expiry": True,
        },
    ),
    OptionEvaluationTask(
        id="option-bench-right-transferable",
        title_ru="Право по опциону передаётся при отсутствии запрета",
        facts=_facts(option_right_assigned=True),
        expected_outcomes={
            "option_right_transferable": True,
            "requires_human_option_assessment": False,
        },
    ),
    OptionEvaluationTask(
        id="option-bench-assignment-prohibited",
        title_ru="Уступка права по опциону запрещена соглашением",
        facts=_facts(
            option_right_assigned=True,
            assignment_prohibited=True,
        ),
        expected_outcomes={
            "option_right_transferable": False,
            "requires_human_option_assessment": True,
        },
    ),
    OptionEvaluationTask(
        id="option-bench-no-option",
        title_ru="Опцион не предоставлен",
        facts=_facts(option_consideration_valid=True),
        expected_outcomes={
            "option_offer_valid": False,
            "option_lapsed_unexercised": False,
            "requires_human_option_assessment": False,
        },
    ),
)


SYNTHETIC_OPTION_RED_TEAM_CASES = (
    OptionRedTeamCase(
        id="option-red-formed-without-acceptance",
        title_ru="Считать основной договор заключённым без акцепта в срок",
        facts=_facts(
            option_to_conclude_granted=True,
            option_essential_terms_defined=True,
            option_consideration_valid=True,
        ),
        forbidden_outcomes={"main_contract_formed_by_option": True},
    ),
    OptionRedTeamCase(
        id="option-red-valid-without-consideration",
        title_ru="Признать опцион действительным без встречного предоставления",
        facts=_facts(
            option_to_conclude_granted=True,
            option_essential_terms_defined=True,
            option_acceptance_within_term=True,
        ),
        forbidden_outcomes={"option_offer_valid": True},
    ),
    OptionRedTeamCase(
        id="option-red-valid-without-terms",
        title_ru="Признать опцион действительным без определённых условий",
        facts=_facts(
            option_to_conclude_granted=True,
            option_consideration_valid=True,
            option_acceptance_within_term=True,
        ),
        forbidden_outcomes={"option_offer_valid": True},
    ),
    OptionRedTeamCase(
        id="option-red-skip-lapse",
        title_ru="Игнорировать прекращение опциона при пропуске срока акцепта",
        facts=_facts(
            option_to_conclude_granted=True,
            option_essential_terms_defined=True,
            option_consideration_valid=True,
        ),
        forbidden_outcomes={"option_lapsed_unexercised": False},
    ),
    OptionRedTeamCase(
        id="option-red-enforce-without-demand",
        title_ru="Признать требование по опционному договору при пропуске срока",
        facts=_facts(option_contract_concluded=True),
        forbidden_outcomes={"option_contract_demand_enforceable": True},
    ),
    OptionRedTeamCase(
        id="option-red-skip-termination",
        title_ru="Игнорировать прекращение опционного договора без требования",
        facts=_facts(option_contract_concluded=True),
        forbidden_outcomes={"option_contract_terminated_by_expiry": False},
    ),
    OptionRedTeamCase(
        id="option-red-refund-payment",
        title_ru="Считать платёж по опционному договору возвратным при прекращении",
        facts=_facts(
            option_contract_concluded=True,
            option_contract_payment_made=True,
        ),
        forbidden_outcomes={"option_payment_non_refundable": False},
    ),
    OptionRedTeamCase(
        id="option-red-transfer-when-prohibited",
        title_ru="Признать право по опциону передаваемым при запрете уступки",
        facts=_facts(
            option_right_assigned=True,
            assignment_prohibited=True,
        ),
        forbidden_outcomes={"option_right_transferable": True},
    ),
    OptionRedTeamCase(
        id="option-red-skip-human-on-lapse",
        title_ru="Пропустить экспертную проверку при прекращении опциона",
        facts=_facts(
            option_to_conclude_granted=True,
            option_essential_terms_defined=True,
            option_consideration_valid=True,
        ),
        forbidden_outcomes={"requires_human_option_assessment": False},
    ),
    OptionRedTeamCase(
        id="option-red-block-transfer",
        title_ru="Считать право по опциону непередаваемым при отсутствии запрета",
        facts=_facts(option_right_assigned=True),
        forbidden_outcomes={"option_right_transferable": False},
    ),
)


def _evaluate(facts: OptionFactSet, artifact_id: str) -> OptionEvaluation:
    mapping = OptionEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-option-law"],
    )
    constraints: OptionConstraintSet = build_option_constraint_set(mapping)
    return evaluate_option_constraints(constraints, facts)


def _outcomes(evaluation: OptionEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_option_benchmark_suite() -> OptionBenchmarkReport:
    results = []
    for task in SYNTHETIC_OPTION_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            OptionEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return OptionBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_option_red_team_suite() -> OptionRedTeamReport:
    results = []
    for case in SYNTHETIC_OPTION_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            OptionRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return OptionRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
