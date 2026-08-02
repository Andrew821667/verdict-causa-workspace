from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.core.bootstrap import BootstrapReviewStatus
from causa.institutional.contracts.research_work import (
    RESEARCH_WORK_EVIDENCE_SCHEMA_VERSION,
    RESEARCH_WORK_MAPPING_VERSION,
    RESEARCH_WORK_MODEL_VERSION,
    ResearchWorkFactSet,
    ReviewedResearchWorkEvidence,
)
from causa.institutional.contracts.research_work_evaluation import (
    SYNTHETIC_RESEARCH_WORK_BENCHMARKS,
    SYNTHETIC_RESEARCH_WORK_RED_TEAM_CASES,
    run_research_work_benchmark_suite,
    run_research_work_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_research_work import (
    SyntheticResearchWorkEvaluationArtifact,
    build_synthetic_research_work_evaluation_artifact,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)
from causa.institutional.contracts.synthetic_sources import get_synthetic_contract_source


def test_reviewed_research_work_is_replayed_in_analysis() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    mapping = result.research_work_evidence_mapping
    assert mapping.schema_version == RESEARCH_WORK_EVIDENCE_SCHEMA_VERSION
    assert mapping.mapping_version == RESEARCH_WORK_MAPPING_VERSION
    assert result.research_work_constraint_set.model_version == RESEARCH_WORK_MODEL_VERSION
    evaluation = result.research_work_evaluation
    # В демонстрационном деле спор о поставке товаров, а не о НИР и ОКР.
    assert evaluation.research_work_qualified is False
    assert evaluation.performer_liability_established is False
    assert evaluation.requires_human_research_work_assessment is False


def test_research_work_evidence_rejects_duplicates_and_incomplete_mapping() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.research_work_evidence

    with pytest.raises(ValidationError, match="duplicate predicates"):
        ReviewedResearchWorkEvidence(
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
            request.model_copy(update={"research_work_evidence": incomplete}),
            build_synthetic_supply_analysis_sources(),
        )


def test_analysis_rejects_unreviewed_and_factual_research_work_legal_source() -> None:
    request = build_synthetic_supply_analysis_request()
    evidence = request.research_work_evidence

    with pytest.raises(ValueError, match="Research-work evidence must be reviewed"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "research_work_evidence": evidence.model_copy(
                        update={"review_status": BootstrapReviewStatus.DRAFT}
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="Research-work evidence case_id"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={"research_work_evidence": evidence.model_copy(update={"case_id": "other"})}
            ),
            build_synthetic_supply_analysis_sources(),
        )
    with pytest.raises(ValueError, match="reviewed legal models"):
        run_reviewed_contract_analysis(
            request.model_copy(
                update={
                    "research_work_evidence": evidence.model_copy(
                        update={
                            "legal_source_refs": (
                                "synthetic-case-supply-1-research-work-evidence",
                                "synthetic-ru-gk775-778-research-work-impossibility-and-liability-v1",
                            )
                        }
                    )
                }
            ),
            build_synthetic_supply_analysis_sources(),
        )


def test_research_work_fact_consistency_is_enforced() -> None:
    values = {field_name: False for field_name in ResearchWorkFactSet.model_fields}
    values.update(pre_impossibility_costs_not_paid=True)
    with pytest.raises(ValidationError, match="Неоплата работ и затрат"):
        ResearchWorkFactSet(**values)


def test_research_work_sources_are_synthetic_review_models_with_official_basis() -> None:
    source_ids = (
        "synthetic-ru-gk769-774-research-work-concept-confidentiality-and-duties-v1",
        "synthetic-ru-gk775-778-research-work-impossibility-and-liability-v1",
    )
    sources = [get_synthetic_contract_source(source_id) for source_id in source_ids]

    assert all(source.metadata["synthetic"] is True for source in sources)
    assert all(source.metadata["review_required"] is True for source in sources)
    assert all(source.metadata["basis_url"].startswith("https://") for source in sources)


def test_research_work_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_research_work_benchmark_suite()
    red_team = run_research_work_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_RESEARCH_WORK_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_RESEARCH_WORK_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total


def test_exported_research_work_artifact_is_reproducible() -> None:
    fixture = SyntheticResearchWorkEvaluationArtifact.model_validate_json(
        Path("examples/synthetic_research_work_evaluation_report.json").read_text(encoding="utf-8")
    )
    assert fixture == build_synthetic_research_work_evaluation_artifact()
