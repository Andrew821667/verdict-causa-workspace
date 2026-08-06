"""Тесты слоя применения общих положений ГК РФ к выводам специальных институтов."""

from causa.institutional.contracts.general_effects import (
    GENERAL_EFFECTS_MODEL_VERSION,
    GeneralEffectsInputs,
    build_general_effects_constraint_set,
    build_general_effects_inputs,
    evaluate_general_effects_constraints,
)
from causa.institutional.contracts.general_effects_evaluation import (
    SYNTHETIC_GENERAL_EFFECTS_BENCHMARKS,
    SYNTHETIC_GENERAL_EFFECTS_RED_TEAM_CASES,
    run_general_effects_benchmark_suite,
    run_general_effects_red_team_suite,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_artifact,
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)


def _flip(evidence, **updates: bool):
    """Копия проверенных данных с изменёнными значениями предикатов."""
    return evidence.model_copy(
        update={
            "assertions": tuple(
                assertion.model_copy(update={"value": updates[assertion.predicate.value]})
                if assertion.predicate.value in updates
                else assertion
                for assertion in evidence.assertions
            )
        }
    )


def test_general_effects_layer_is_derived_from_anchor_evaluations() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    assert result.general_effects_constraint_set.model_version == GENERAL_EFFECTS_MODEL_VERSION
    # Входы слоя выводятся из якорных моделей, а не утверждаются рецензентом.
    assert result.general_effects_inputs == build_general_effects_inputs(
        result.formation_evaluation,
        result.invalidity_evaluation,
        result.form_evaluation,
        result.limitation_evaluation,
        result.representation_evaluation,
        result.property_rights_evaluation,
        result.civil_principles_evaluation,
        result.transactions_evaluation,
        result.constraint_evaluation,
        result.termination_evaluation,
    )
    # В демонстрационном деле договор действует и требования исполнимы.
    evaluation = result.general_effects_evaluation
    assert evaluation.contract_legally_effective is True
    assert evaluation.contractual_claims_enforceable is True
    assert evaluation.institute_conclusions_displaced is False
    assert evaluation.requires_human_general_effects_assessment is False


def test_general_effects_replays_from_its_inputs() -> None:
    result = build_synthetic_supply_analysis_artifact().result

    expected_set = build_general_effects_constraint_set(
        result.general_effects_inputs, result.case_id
    )
    assert result.general_effects_constraint_set == expected_set
    assert result.general_effects_evaluation == evaluate_general_effects_constraints(
        expected_set, result.general_effects_inputs
    )


def test_limitation_defense_propagates_to_whole_analysis() -> None:
    """Регрессия: истёкшая и заявленная давность обесценивает договорные требования.

    До появления слоя общих положений вывод модели статей 195–208 не влиял ни на
    один другой институт и не поднимал флаг экспертизы.
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(request, sources)
    assert baseline.general_effects_evaluation.contractual_claims_enforceable is True
    assert baseline.requires_human_resolution is False

    barred = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "limitation_evidence": _flip(
                    request.limitation_evidence,
                    claim_subject_to_limitation=True,
                    right_violation_and_defendant_known=True,
                    general_three_year_term_elapsed=True,
                    limitation_pleaded_by_party_before_judgment=True,
                )
            }
        ),
        sources,
    )

    assert barred.limitation_evaluation.limitation_defense_available is True
    evaluation = barred.general_effects_evaluation
    # Договор действует, но в судебной защите отказано.
    assert evaluation.contract_legally_effective is True
    assert evaluation.judicial_protection_available is False
    assert evaluation.claims_barred_by_limitation is True
    assert evaluation.contractual_claims_enforceable is False
    # Установленное нарушение больше не может быть положено в основание присуждения.
    assert barred.constraint_evaluation.breach_issue is True
    assert evaluation.breach_findings_without_effect is True
    # И это отражается на итоге всего анализа.
    assert barred.requires_human_resolution is True


def test_general_effects_never_displaces_an_effective_contract() -> None:
    inputs = GeneralEffectsInputs(
        contract_concluded_prerequisites=True,
        contractual_effect_displaced=False,
        restitution_required=False,
        transaction_void_for_form=False,
        limitation_defense_available=False,
        claim_not_subject_to_limitation=False,
        unauthorized_representation_detected=False,
        unauthorized_disposal_detected=False,
        abuse_of_right_detected=False,
        consent_missing_for_transaction=False,
        breach_issue=True,
        effective_termination=False,
    )
    evaluation = evaluate_general_effects_constraints(
        build_general_effects_constraint_set(inputs, "case-effective"), inputs
    )

    assert evaluation.institute_conclusions_displaced is False
    assert evaluation.breach_findings_without_effect is False
    assert evaluation.contractual_claims_enforceable is True


def test_general_effects_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_general_effects_benchmark_suite()
    red_team = run_general_effects_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_GENERAL_EFFECTS_BENCHMARKS) == 10
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_GENERAL_EFFECTS_RED_TEAM_CASES) == 10
    assert red_team.blocked == red_team.total
