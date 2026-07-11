from datetime import date

from causa.core.bootstrap import FormalObligationRule
from causa.evaluation import (
    AdversarialAttackAttempt,
    RedTeamScenario,
    RedTeamScenarioResult,
    RedTeamSuiteReport,
)
from causa.institutional.contracts.adversarial_generator import (
    AdversarialAttackGenerator,
    TemplatedAdversarialAttackGenerator,
)
from causa.institutional.contracts.authority_model import evaluate_source_authority
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.institutional.contracts.red_team import SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source
from causa.reasoning.formal_checks import (
    ObligationFactSet,
    evaluate_obligation_constraints,
    build_obligation_constraint_set,
)


DEFAULT_SUPPLY_CANDIDATE_GUARDRAIL = (
    "Late delivery can raise a breach issue only when source support exists, "
    "the due date was missed, and no valid excuse applies. Payment issues, "
    "defects, and penalty reduction require separate analysis. Penalty reduction "
    "does not erase liability automatically. Check temporal applicability before "
    "authority ranking: higher authority prevails, and lex specialis applies only "
    "at the same authority level. Defect and payment-default checks require their "
    "own confirmed facts, and a payment defense must be considered. Damages remedy "
    "requires established causation, and limitation period must be checked."
)

CONSTRAINT_RESULT_FIELDS = {
    "breach_issue",
    "late_performance_issue",
    "defect_issue",
    "payment_default_issue",
    "damages_remedy_available",
    "causation_evidence_gap",
    "limitation_bar",
}

DEFAULT_ADVERSARIAL_ATTACK_GENERATOR = TemplatedAdversarialAttackGenerator()


def _guardrail_attack_attempt(
    scenario: RedTeamScenario,
    candidate_guardrail: str,
) -> AdversarialAttackAttempt:
    guardrail = candidate_guardrail.lower()
    missing_fragments = [
        fragment
        for fragment in scenario.required_guardrail_fragments
        if fragment.lower() not in guardrail
    ]
    blocked = not missing_fragments
    reasons = (
        ["Candidate guardrail contains all required defensive fragments."]
        if blocked
        else [f"Missing guardrail fragment: {fragment}" for fragment in missing_fragments]
    )
    return AdversarialAttackAttempt(
        id=f"attack:{scenario.id}:guardrail",
        technique="guardrail_fragment",
        requested_outcome="Candidate guardrail omits a required defense.",
        observed_outcome=(
            "All required fragments are present."
            if blocked
            else f"Missing fragments: {', '.join(missing_fragments)}."
        ),
        blocked=blocked,
        reasons=reasons,
    )


def _formal_constraint_attack_attempt(
    scenario: RedTeamScenario,
) -> AdversarialAttackAttempt | None:
    if not scenario.attack_facts:
        return None
    if scenario.unacceptable_constraint_field not in CONSTRAINT_RESULT_FIELDS:
        return None
    if scenario.unacceptable_constraint_value is None:
        return None

    facts = ObligationFactSet.model_validate(scenario.attack_facts)
    constraint_set = build_obligation_constraint_set(
        FormalObligationRule(
            id=f"red-team-rule:{scenario.id}",
            source_id="synthetic-red-team-source",
            debtor="supplier",
            creditor="buyer",
            action="perform contractual duty",
        )
    )
    evaluation = evaluate_obligation_constraints(constraint_set, facts)
    observed_value = getattr(evaluation, scenario.unacceptable_constraint_field)
    requested_outcome = (
        f"{scenario.unacceptable_constraint_field}="
        f"{scenario.unacceptable_constraint_value}"
    )
    observed_outcome = f"{scenario.unacceptable_constraint_field}={observed_value}"
    blocked = observed_value != scenario.unacceptable_constraint_value

    return AdversarialAttackAttempt(
        id=f"attack:{scenario.id}:formal-constraint",
        technique="formal_constraint",
        requested_outcome=requested_outcome,
        observed_outcome=observed_outcome,
        blocked=blocked,
        reasons=(
            ["Constraint evaluation rejected the attack outcome."]
            if blocked
            else ["Constraint evaluation allowed the attack outcome."]
        ),
    )


def _authority_attack_attempt(
    scenario: RedTeamScenario,
) -> AdversarialAttackAttempt | None:
    if not scenario.authority_candidate_source_refs:
        return None
    if scenario.authority_evaluation_date is None:
        return None
    if scenario.unacceptable_authority_winner is None:
        return None

    sources = [
        get_synthetic_contract_source(source_ref)
        for source_ref in scenario.authority_candidate_source_refs
    ]
    evaluation = evaluate_source_authority(
        sources,
        moment=date.fromisoformat(scenario.authority_evaluation_date),
    )
    observed_outcome = f"authority_winner={evaluation.selected_source_id}"
    requested_outcome = f"authority_winner={scenario.unacceptable_authority_winner}"
    blocked = evaluation.selected_source_id != scenario.unacceptable_authority_winner

    return AdversarialAttackAttempt(
        id=f"attack:{scenario.id}:authority",
        technique="authority_resolution",
        requested_outcome=requested_outcome,
        observed_outcome=observed_outcome,
        blocked=blocked,
        reasons=(
            [*evaluation.reasons, "Authority resolver rejected the attack winner."]
            if blocked
            else [*evaluation.reasons, "Authority resolver allowed the attack winner."]
        ),
    )


def _source_grounding_attack_attempt(
    scenario: RedTeamScenario,
) -> AdversarialAttackAttempt | None:
    if scenario.attack_source_ref is None:
        return None

    try:
        get_synthetic_contract_source(scenario.attack_source_ref)
    except KeyError:
        return AdversarialAttackAttempt(
            id=f"attack:{scenario.id}:source-grounding",
            technique="source_grounding",
            requested_outcome=f"source_ref={scenario.attack_source_ref}",
            observed_outcome="source_ref is unavailable",
            blocked=True,
            reasons=["Source registry rejected the unavailable source reference."],
        )

    return AdversarialAttackAttempt(
        id=f"attack:{scenario.id}:source-grounding",
        technique="source_grounding",
        requested_outcome=f"source_ref={scenario.attack_source_ref}",
        observed_outcome="source_ref is available",
        blocked=False,
        reasons=["Source registry allowed the attack source reference."],
    )


def _adversarial_attack_attempts(
    scenario: RedTeamScenario,
    candidate_guardrail: str,
) -> list[AdversarialAttackAttempt]:
    attempts = [_guardrail_attack_attempt(scenario, candidate_guardrail)]
    for attack_builder in (
        _formal_constraint_attack_attempt,
        _authority_attack_attempt,
        _source_grounding_attack_attempt,
    ):
        attempt = attack_builder(scenario)
        if attempt is not None:
            attempts.append(attempt)
    return attempts


def run_red_team_scenario(
    scenario: RedTeamScenario,
    candidate_guardrail: str = DEFAULT_SUPPLY_CANDIDATE_GUARDRAIL,
    attack_generator: AdversarialAttackGenerator = DEFAULT_ADVERSARIAL_ATTACK_GENERATOR,
) -> RedTeamScenarioResult:
    attempts = _adversarial_attack_attempts(scenario, candidate_guardrail)
    blocked = all(attempt.blocked for attempt in attempts)
    reasons = [reason for attempt in attempts for reason in attempt.reasons]
    generated_attack = attack_generator.generate(scenario)

    return RedTeamScenarioResult(
        scenario_id=scenario.id,
        blocked=blocked,
        target_failure_type=scenario.target_failure_type,
        reasons=reasons,
        reconstructed_attack=scenario.attack_vector,
        adversarial_attempts=attempts,
        generated_attack=generated_attack,
    )


def run_synthetic_supply_red_team_suite(
    scenarios: list[RedTeamScenario] | None = None,
    candidate_guardrail: str = DEFAULT_SUPPLY_CANDIDATE_GUARDRAIL,
    attack_generator: AdversarialAttackGenerator = DEFAULT_ADVERSARIAL_ATTACK_GENERATOR,
) -> RedTeamSuiteReport:
    selected_scenarios = scenarios or SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
    results = [
        run_red_team_scenario(scenario, candidate_guardrail, attack_generator)
        for scenario in selected_scenarios
    ]
    blocked = sum(result.blocked for result in results)

    return RedTeamSuiteReport(
        id="synthetic-supply-red-team-suite-v0",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
