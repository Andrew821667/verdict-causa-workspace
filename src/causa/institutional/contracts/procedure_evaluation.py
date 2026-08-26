from pydantic import BaseModel, Field

from causa.institutional.contracts.procedure import (
    ProcedureConstraintSet,
    ProcedureEvaluation,
    ProcedureEvidenceMappingResult,
    ProcedureFactSet,
    build_procedure_constraint_set,
    evaluate_procedure_constraints,
)


class ProcedureEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ProcedureFactSet
    expected_outcomes: dict[str, bool]


class ProcedureEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ProcedureBenchmarkReport(BaseModel):
    id: str = "procedure-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ProcedureEvaluationResult] = Field(default_factory=list)


class ProcedureRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ProcedureFactSet
    forbidden_outcomes: dict[str, bool]


class ProcedureRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ProcedureRedTeamReport(BaseModel):
    id: str = "procedure-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ProcedureRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ProcedureFactSet:
    values = {field_name: False for field_name in ProcedureFactSet.model_fields}
    values.update(updates)
    return ProcedureFactSet(**values)


SYNTHETIC_PROCEDURE_BENCHMARKS = (
    ProcedureEvaluationTask(
        id="procedure-bench-compel",
        title_ru="Обязанная сторона уклоняется — понуждение и убытки",
        facts=_facts(
            conclusion_mandatory_for_party=True,
            offer_or_draft_sent=True,
            obliged_party_evaded=True,
        ),
        expected_outcomes={
            "conclusion_compellable": True,
            "damages_for_mandatory_evasion": True,
            "requires_human_procedure_assessment": True,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-no-evasion",
        title_ru="Обязанная сторона заключает договор без уклонения",
        facts=_facts(
            conclusion_mandatory_for_party=True,
            offer_or_draft_sent=True,
        ),
        expected_outcomes={
            "conclusion_compellable": False,
            "damages_for_mandatory_evasion": False,
            "requires_human_procedure_assessment": False,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-court-terms",
        title_ru="Разногласия переданы на рассмотрение суда",
        facts=_facts(
            conclusion_mandatory_for_party=True,
            offer_or_draft_sent=True,
            precontractual_dispute_submitted_to_court=True,
        ),
        expected_outcomes={
            "precontractual_terms_set_by_court": True,
            "requires_human_procedure_assessment": True,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-not-mandatory-evasion",
        title_ru="Уклонение стороны, для которой заключение необязательно",
        facts=_facts(
            offer_or_draft_sent=True,
            obliged_party_evaded=True,
        ),
        expected_outcomes={
            "conclusion_compellable": False,
            "damages_for_mandatory_evasion": False,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-auction-formed",
        title_ru="Договор на торгах заключён подписанием протокола",
        facts=_facts(
            contract_concluded_at_auction=True,
            auction_notice_timely=True,
            winner_determined=True,
            results_protocol_signed=True,
        ),
        expected_outcomes={
            "auction_contract_formed": True,
            "winner_liable_for_evasion": False,
            "requires_human_procedure_assessment": False,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-winner-evaded",
        title_ru="Победитель уклонился от подписания протокола",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            winner_evaded_signing=True,
        ),
        expected_outcomes={
            "winner_liable_for_evasion": True,
            "auction_contract_formed": False,
            "requires_human_procedure_assessment": True,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-auction-no-protocol",
        title_ru="Победитель определён, но протокол не подписан",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
        ),
        expected_outcomes={"auction_contract_formed": False},
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-auction-voidable",
        title_ru="Торги проведены с нарушением правил и оспорены",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
            auction_rules_violated=True,
            interested_party_challenge=True,
        ),
        expected_outcomes={
            "auction_voidable": True,
            "auction_contract_invalid": True,
            "requires_human_procedure_assessment": True,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-violation-without-challenge",
        title_ru="Нарушение правил торгов без иска заинтересованного лица",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
            auction_rules_violated=True,
        ),
        expected_outcomes={
            "auction_voidable": False,
            "auction_contract_invalid": False,
            "requires_human_procedure_assessment": False,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-empty",
        title_ru="Обычное заключение без обязательного порядка и торгов",
        facts=_facts(),
        expected_outcomes={
            "conclusion_compellable": False,
            "auction_contract_formed": False,
            "requires_human_procedure_assessment": False,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-public-auction-clean",
        title_ru="Публичные торги проведены с соблюдением статьи 449.1",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
            public_auction_asserted=True,
            public_auction_organiser_authorised=True,
            public_auction_notice_names_owner=True,
            public_auction_protocol_lists_bids=True,
        ),
        expected_outcomes={
            "public_auction_qualified": True,
            "public_auction_rules_violated": False,
            "auction_voidable": False,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-public-auction-barred-person",
        title_ru="В публичных торгах участвовал должник",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
            public_auction_asserted=True,
            public_auction_organiser_authorised=True,
            public_auction_notice_names_owner=True,
            public_auction_protocol_lists_bids=True,
            barred_person_participated=True,
            interested_party_challenge=True,
        ),
        expected_outcomes={
            "public_auction_participation_ban_breached": True,
            "public_auction_rules_violated": True,
            "auction_voidable": True,
            "auction_contract_invalid": True,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-public-auction-organiser-defect",
        title_ru="Организатор публичных торгов не уполномочен законом",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
            public_auction_asserted=True,
            public_auction_notice_names_owner=True,
            public_auction_protocol_lists_bids=True,
            interested_party_challenge=True,
        ),
        expected_outcomes={
            "public_auction_organiser_defect": True,
            "public_auction_rules_violated": True,
            "auction_voidable": True,
        },
    ),
    ProcedureEvaluationTask(
        id="procedure-bench-public-auction-defect-without-challenge",
        title_ru="Нарушение правил публичных торгов без иска заинтересованного лица",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
            public_auction_asserted=True,
            public_auction_organiser_authorised=True,
            public_auction_notice_names_owner=True,
            public_auction_protocol_lists_bids=True,
            barred_person_participated=True,
        ),
        expected_outcomes={
            "public_auction_rules_violated": True,
            "auction_voidable": False,
            "auction_contract_invalid": False,
        },
    ),
)


SYNTHETIC_PROCEDURE_RED_TEAM_CASES = (
    ProcedureRedTeamCase(
        id="procedure-red-compel-without-mandatory",
        title_ru="Понуждать сторону, для которой заключение необязательно",
        facts=_facts(
            offer_or_draft_sent=True,
            obliged_party_evaded=True,
        ),
        forbidden_outcomes={"conclusion_compellable": True},
    ),
    ProcedureRedTeamCase(
        id="procedure-red-compel-without-evasion",
        title_ru="Понуждать к заключению при отсутствии уклонения",
        facts=_facts(
            conclusion_mandatory_for_party=True,
            offer_or_draft_sent=True,
        ),
        forbidden_outcomes={"conclusion_compellable": True},
    ),
    ProcedureRedTeamCase(
        id="procedure-red-damages-without-mandatory",
        title_ru="Взыскивать убытки без обязательности заключения",
        facts=_facts(obliged_party_evaded=True),
        forbidden_outcomes={"damages_for_mandatory_evasion": True},
    ),
    ProcedureRedTeamCase(
        id="procedure-red-auction-formed-without-protocol",
        title_ru="Считать договор на торгах заключённым без протокола",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
        ),
        forbidden_outcomes={"auction_contract_formed": True},
    ),
    ProcedureRedTeamCase(
        id="procedure-red-winner-liable-without-evasion",
        title_ru="Считать победителя ответственным без уклонения от подписания",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
        ),
        forbidden_outcomes={"winner_liable_for_evasion": True},
    ),
    ProcedureRedTeamCase(
        id="procedure-red-void-without-challenge",
        title_ru="Признавать торги недействительными без иска заинтересованного лица",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
            auction_rules_violated=True,
        ),
        forbidden_outcomes={"auction_voidable": True},
    ),
    ProcedureRedTeamCase(
        id="procedure-red-invalidate-without-void",
        title_ru="Признавать договор недействительным без недействительности торгов",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
            auction_rules_violated=True,
        ),
        forbidden_outcomes={"auction_contract_invalid": True},
    ),
    ProcedureRedTeamCase(
        id="procedure-red-skip-court-terms",
        title_ru="Игнорировать определение условий судом при передаче спора",
        facts=_facts(precontractual_dispute_submitted_to_court=True),
        forbidden_outcomes={"precontractual_terms_set_by_court": False},
    ),
    ProcedureRedTeamCase(
        id="procedure-red-skip-human-on-winner-evasion",
        title_ru="Пропустить экспертную проверку при уклонении победителя",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            winner_evaded_signing=True,
        ),
        forbidden_outcomes={"requires_human_procedure_assessment": False},
    ),
    ProcedureRedTeamCase(
        id="procedure-red-skip-human-on-voidable",
        title_ru="Пропустить экспертизу при оспаривании торгов",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
            auction_rules_violated=True,
            interested_party_challenge=True,
        ),
        forbidden_outcomes={"requires_human_procedure_assessment": False},
    ),
    ProcedureRedTeamCase(
        id="procedure-red-public-rules-on-ordinary-auction",
        title_ru="Применить требования статьи 449.1 к обычным торгам",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
            interested_party_challenge=True,
        ),
        forbidden_outcomes={"public_auction_rules_violated": True},
    ),
    ProcedureRedTeamCase(
        id="procedure-red-public-auction-voidable-without-challenge",
        title_ru="Признать публичные торги оспоримыми без иска заинтересованного лица",
        facts=_facts(
            contract_concluded_at_auction=True,
            winner_determined=True,
            results_protocol_signed=True,
            public_auction_asserted=True,
            public_auction_organiser_authorised=True,
            public_auction_notice_names_owner=True,
            public_auction_protocol_lists_bids=True,
            barred_person_participated=True,
        ),
        forbidden_outcomes={"auction_voidable": True},
    ),
)


def _evaluate(facts: ProcedureFactSet, artifact_id: str) -> ProcedureEvaluation:
    mapping = ProcedureEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-procedure-law"],
    )
    constraints: ProcedureConstraintSet = build_procedure_constraint_set(mapping)
    return evaluate_procedure_constraints(constraints, facts)


def _outcomes(evaluation: ProcedureEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_procedure_benchmark_suite() -> ProcedureBenchmarkReport:
    results = []
    for task in SYNTHETIC_PROCEDURE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ProcedureEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ProcedureBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_procedure_red_team_suite() -> ProcedureRedTeamReport:
    results = []
    for case in SYNTHETIC_PROCEDURE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            ProcedureRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return ProcedureRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
