from causa.evaluation import RedTeamScenario, RedTeamScenarioResult, RedTeamSuiteReport
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST
from causa.institutional.contracts.red_team import SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS


DEFAULT_SUPPLY_CANDIDATE_GUARDRAIL = (
    "Late delivery can raise a breach issue only when source support exists, "
    "the due date was missed, and no valid excuse applies. Payment issues, "
    "defects, and penalty reduction require separate analysis. Penalty reduction "
    "does not erase liability automatically."
)


def run_red_team_scenario(
    scenario: RedTeamScenario,
    candidate_guardrail: str = DEFAULT_SUPPLY_CANDIDATE_GUARDRAIL,
) -> RedTeamScenarioResult:
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

    return RedTeamScenarioResult(
        scenario_id=scenario.id,
        blocked=blocked,
        target_failure_type=scenario.target_failure_type,
        reasons=reasons,
        reconstructed_attack=scenario.attack_vector,
    )


def run_synthetic_supply_red_team_suite(
    scenarios: list[RedTeamScenario] | None = None,
    candidate_guardrail: str = DEFAULT_SUPPLY_CANDIDATE_GUARDRAIL,
) -> RedTeamSuiteReport:
    selected_scenarios = scenarios or SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS
    results = [
        run_red_team_scenario(scenario, candidate_guardrail)
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
