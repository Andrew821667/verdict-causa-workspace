from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.games import (
    GAMES_EVIDENCE_SCHEMA_VERSION,
    GAMES_MAPPING_VERSION,
    GAMES_MODEL_VERSION,
    GamesFactSet,
    ReviewedGamesEvidence,
)
from causa.institutional.contracts.games_evaluation import (
    SYNTHETIC_GAMES_BENCHMARKS,
    SYNTHETIC_GAMES_RED_TEAM_CASES,
    run_games_benchmark_suite,
    run_games_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_games import (
    SyntheticGamesEvaluationArtifact,
    build_synthetic_games_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_games_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.games_evidence_mapping
    assert mapping.schema_version == GAMES_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == GAMES_MAPPING_VERSION
    assert result.games_constraint_set.model_version == GAMES_MODEL_VERSION
    evaluation = result.games_evaluation
    # В демонстрационном деле игры и пари не проводились.
    assert evaluation.games_qualified is False
    assert evaluation.requires_human_games_assessment is False


def test_games_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.games_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedGamesEvidence(
            id=evidence.id,
            case_id=evidence.case_id,
            assertions=(*evidence.assertions, evidence.assertions[0]),
            legal_source_refs=evidence.legal_source_refs,
            review_status=evidence.review_status,
            reviewer_id=evidence.reviewer_id,
        )

    incomplete = evidence.model_copy(update={"assertions": evidence.assertions[:-1]})
    with pytest.raises(ValueError, match="missing predicates"):
        run_reviewed_contract_analysis(
            request.model_copy(update={"games_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_games_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.games_evidence

    with pytest.raises(ValueError, match="Games evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "games_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Games evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"games_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "games_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-games-evidence",
                                "synthetic-ru-gk1063-organization-of-lotteries-and-payment-of-winnings-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_games_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in GamesFactSet.model_fields}
    values.update(payment_refusal_damages_not_applied=True)
    with pytest.raises(ValidationError, match="срока выплаты выигрыша"):
        GamesFactSet(**values)

    scope = {field_name: False for field_name in GamesFactSet.model_fields}
    scope.update(judicial_protection_exclusion_breached=True)
    with pytest.raises(ValidationError, match="отказе в судебной защите"):
        GamesFactSet(**scope)


def test_games_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk1062-judicial-protection-of-claims-from-games-and-betting-v1",
        "synthetic-ru-gk1063-organization-of-lotteries-and-payment-of-winnings-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_games_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_games_benchmark_suite()
    red_team = run_games_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_GAMES_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_GAMES_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_games_artifact_is_reproducible() -> None:
    fixture = SyntheticGamesEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_games_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_games_evaluation_artifact()
