import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from causa.governance.synthetic_lifecycle import build_synthetic_gap_governance_record
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
)
from causa.institutional.contracts.synthetic_translation import (
    SYNTHETIC_TRANSLATION_TRACE_ID,
    build_synthetic_translation_bundle_artifact,
)
from causa.management.policy_registry import active_policy_snapshot
from causa.management.synthetic_registry import (
    SYNTHETIC_POLICY_FAMILY_ID,
    build_synthetic_management_policy_registry_artifact,
)
from causa.translation import TranslationLevel
from causa.translation_pipeline import (
    TranslationBundle,
    TranslationBundleArtifact,
    evaluate_translation_faithfulness,
    evaluate_translation_usability,
)
from causa.translation_templates import (
    TranslationTemplateSet,
    build_russian_translation_template_set,
)


def _evaluation_context():
    analysis = build_synthetic_supply_analysis_artifact()
    registry = build_synthetic_management_policy_registry_artifact().registry
    policy = active_policy_snapshot(registry, SYNTHETIC_POLICY_FAMILY_ID)
    governance = build_synthetic_gap_governance_record(
        "candidate-supply-excuse-scope",
        policy_version=policy.id,
        policy_content_hash=policy.content_hash,
    )
    return analysis, policy, governance


def test_russian_template_set_is_complete_deterministic_and_tamper_evident() -> None:
    templates = build_russian_translation_template_set()

    assert {template.level for template in templates.templates} == set(TranslationLevel)
    assert templates == build_russian_translation_template_set()
    assert templates.content_hash.startswith("sha256:")

    payload = templates.model_dump(mode="json")
    payload["templates"][0]["title_ru"] = "Подмененный заголовок"
    with pytest.raises(ValidationError, match="Hash набора шаблонов"):
        TranslationTemplateSet.model_validate(payload)


def test_bundle_has_three_increasing_russian_levels_with_identical_assertions() -> None:
    bundle = build_synthetic_translation_bundle_artifact().bundle
    artifacts = {artifact.level: artifact for artifact in bundle.artifacts}

    assert set(artifacts) == set(TranslationLevel)
    assert (
        len(artifacts[TranslationLevel.EXECUTIVE].text)
        < len(artifacts[TranslationLevel.PROFESSIONAL].text)
        < len(artifacts[TranslationLevel.FORENSIC].text)
    )
    assert artifacts[TranslationLevel.EXECUTIVE].text.startswith("КРАТКОЕ ПРАВОВОЕ РЕЗЮМЕ")
    assert (
        artifacts[TranslationLevel.PROFESSIONAL].assertions
        == artifacts[TranslationLevel.FORENSIC].assertions
    )
    assert (
        artifacts[TranslationLevel.EXECUTIVE].assertions
        == artifacts[TranslationLevel.PROFESSIONAL].assertions
    )


def test_bundle_passes_faithfulness_and_structural_usability_checks() -> None:
    bundle = build_synthetic_translation_bundle_artifact().bundle

    assert bundle.faithfulness_report.passed is True
    assert bundle.usability_report.structural_checks_passed is True
    assert bundle.usability_report.requires_human_pilot is True
    assert bundle.ready_for_human_review is True
    assert all(artifact.faithfulness_passed for artifact in bundle.artifacts)
    assert all(artifact.usability_passed for artifact in bundle.artifacts)


def test_bundle_contract_rejects_inconsistent_template_coordinates() -> None:
    bundle = build_synthetic_translation_bundle_artifact().bundle
    payload = bundle.model_dump(mode="json")
    payload["artifacts"][0]["template_content_hash"] = "sha256:tampered"

    with pytest.raises(ValidationError, match="Координаты шаблонов"):
        TranslationBundle.model_validate(payload)


def test_faithfulness_detects_text_and_assertion_distortion() -> None:
    bundle = build_synthetic_translation_bundle_artifact().bundle
    analysis, policy, governance = _evaluation_context()
    professional = bundle.artifact_for(TranslationLevel.PROFESSIONAL)
    changed_assertion = professional.assertions[0].model_copy(update={"value": False})
    tampered = professional.model_copy(
        update={
            "text": professional.text + "\nПодмена.",
            "assertions": [changed_assertion, *professional.assertions[1:]],
        }
    )
    artifacts = [
        tampered if artifact.level == TranslationLevel.PROFESSIONAL else artifact
        for artifact in bundle.artifacts
    ]

    report = evaluate_translation_faithfulness(
        trace_id=SYNTHETIC_TRANSLATION_TRACE_ID,
        artifacts=artifacts,
        request=analysis.request,
        result=analysis.result,
        governance=governance,
        policy_snapshot=policy,
        template_set=build_russian_translation_template_set(),
    )

    assert report.passed is False
    assert {issue.code for issue in report.issues} >= {
        "text_distortion",
        "assertion_distortion",
    }


def test_faithfulness_detects_missing_level_and_policy_coordinates() -> None:
    bundle = build_synthetic_translation_bundle_artifact().bundle
    analysis, policy, governance = _evaluation_context()
    executive = bundle.artifact_for(TranslationLevel.EXECUTIVE).model_copy(
        update={"policy_content_hash": "sha256:tampered"}
    )
    artifacts = [
        executive,
        bundle.artifact_for(TranslationLevel.PROFESSIONAL),
    ]

    report = evaluate_translation_faithfulness(
        trace_id=SYNTHETIC_TRANSLATION_TRACE_ID,
        artifacts=artifacts,
        request=analysis.request,
        result=analysis.result,
        governance=governance,
        policy_snapshot=policy,
        template_set=build_russian_translation_template_set(),
    )

    assert report.passed is False
    assert {issue.code for issue in report.issues} >= {"missing_level", "policy_mismatch"}


def test_usability_detects_machine_detail_leak_outside_forensic_level() -> None:
    bundle = build_synthetic_translation_bundle_artifact().bundle
    executive = bundle.artifact_for(TranslationLevel.EXECUTIVE)
    tampered = executive.model_copy(update={"text": executive.text + "\nsha256:unsafe"})

    report = evaluate_translation_usability(
        trace_id=bundle.trace_id,
        artifacts=[
            tampered if artifact.level == TranslationLevel.EXECUTIVE else artifact
            for artifact in bundle.artifacts
        ],
        template_set=build_russian_translation_template_set(),
    )

    assert report.structural_checks_passed is False
    assert "machine_detail_leak" in {issue.code for issue in report.issues}


def test_forensic_level_contains_reproduction_governance_and_path_comparison() -> None:
    bundle = build_synthetic_translation_bundle_artifact().bundle
    forensic = bundle.artifact_for(TranslationLevel.FORENSIC).text

    assert bundle.policy_snapshot_id in forensic
    assert bundle.policy_content_hash in forensic
    assert bundle.template_content_hash in forensic
    assert "Constraint set:" in forensic
    assert "Governance-журнал кандидата" in forensic
    assert "Отклоненный путь" in forensic
    assert "Bounded counterfactual-анализ" in forensic
    assert "contracts-legal-operators-ru-v1" in forensic
    professional = bundle.artifact_for(TranslationLevel.PROFESSIONAL).text
    assert "Контрфактическая чувствительность" in professional
    assert "Ответственность и неустойка" in professional
    assert "Заключение договора" in professional
    assert "Действительность сделки" in professional
    assert "Обеспечение исполнения обязательств" in professional
    assert "Изменение и расторжение договора" in professional
    assert "Модель заключения договора (статьи 432, 435, 438 и 443 ГК РФ)" in forensic
    assert "Модель недействительности сделки (статьи 166–181 ГК РФ)" in forensic
    assert "Модель обеспечения исполнения (статьи 329–381.2 ГК РФ)" in forensic
    assert "Модель изменения и расторжения договора (статьи 450–453 ГК РФ)" in forensic
    assert "Модель ответственности (статьи 333 и 401 ГК РФ)" in forensic
    assert bundle.path_comparisons[0].selected_path == "active_reviewed_path"


def test_exported_translation_bundle_fixture_is_valid_and_reproducible() -> None:
    fixture_path = Path("examples/synthetic_translation_bundle_report.json")
    fixture = TranslationBundleArtifact.model_validate_json(
        fixture_path.read_text(encoding="utf-8")
    )
    regenerated = build_synthetic_translation_bundle_artifact()

    assert fixture == regenerated
    assert json.loads(fixture_path.read_text(encoding="utf-8"))["locale"] == "ru-RU"
