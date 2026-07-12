import json
from pathlib import Path

from causa.phase0.pipeline import (
    Phase0ReadinessReport,
    PipelineStepStatus,
    build_phase0_readiness_report,
    run_supply_dispute_pipeline,
)


def test_supply_dispute_pipeline_has_no_failed_steps() -> None:
    result = run_supply_dispute_pipeline()

    assert result.passed is True
    assert {step.id for step in result.steps} >= {
        "select-source",
        "review-bootstrap-json",
        "translate-structured-formal-output",
        "validate-reviewed-analysis-inputs",
        "map-reviewed-evidence",
        "resolve-reviewed-authority",
        "evaluate-contract-formation",
        "evaluate-obligation-constraints",
        "evaluate-contract-change-and-termination",
        "evaluate-counterfactual-sensitivity",
        "evaluate-liability-prerequisites",
        "build-case-graph",
        "ground-claim",
        "classify-candidate",
        "execute-governance-lifecycle",
        "record-policy",
        "attach-red-team",
        "produce-translation",
        "export-decision-trace",
    }


def test_supply_dispute_pipeline_passes_translation_layer() -> None:
    result = run_supply_dispute_pipeline()
    warning_steps = {step.id for step in result.steps if step.status == PipelineStepStatus.WARNING}

    assert "produce-translation" not in warning_steps
    translation_step = next(step for step in result.steps if step.id == "produce-translation")
    assert translation_step.status == PipelineStepStatus.PASSED


def test_phase0_readiness_report_is_not_production_ready() -> None:
    report = build_phase0_readiness_report()

    assert report.ready_for_production is False
    assert report.project_stage == "architectural_prototype"
    assert report.project_stage_label_ru == "Архитектурный прототип"
    assert report.locale == "ru-RU"
    assert report.warning_count > 0
    assert report.failed_count == 0
    bootstrap_item = next(item for item in report.items if item.id == "ws3-bootstrap")
    governance_item = next(item for item in report.items if item.id == "ws6-governance")
    translation_item = next(item for item in report.items if item.id == "ws7-translation")
    assert bootstrap_item.status == PipelineStepStatus.PASSED
    assert governance_item.status == PipelineStepStatus.PASSED
    assert translation_item.status == PipelineStepStatus.PASSED


def test_exported_phase0_readiness_report_fixture_is_valid() -> None:
    fixture_path = Path("examples/phase0_readiness_report.json")
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    report = Phase0ReadinessReport.model_validate(data)

    assert report.id == "phase0-readiness-report-v0"
    assert report.ready_for_production is False
    assert {item.id for item in report.items} >= {
        "ws1-universal-core",
        "ws3-bootstrap",
        "ws7-translation",
        "ws9-zero-to-value",
    }
