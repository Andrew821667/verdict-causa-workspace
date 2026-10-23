"""Тесты слоя применения общих положений ГК РФ к выводам специальных институтов."""

import pytest

from causa.institutional.contracts.general_effects import (
    GENERAL_EFFECTS_MODEL_VERSION,
    GeneralEffectsEvaluation,
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
from causa.institutional.contracts.fact_consistency import FactConsistencyError
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
        result.terms_evaluation,
        result.persons_evaluation,
        result.objects_evaluation,
        result.constraint_evaluation,
        result.termination_evaluation,
        result.attribution_delay_evaluation,
        result.obligation_dynamics_evaluation,
        result.meeting_decisions_evaluation,
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


def test_a_void_meeting_decision_reaches_the_final_conclusions() -> None:
    """Регрессия: вывод модели главы 9.1 не доходил до слоя до выпуска `1.2.0`.

    Ничтожность решения собрания подрывает условие договора, которое на этом
    решении держится (дело 45-КГ23-2-К7), но связь между решением и условием —
    факт дела, а не вывод института, поэтому она пришла отдельным предикатом.
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(request, sources)
    assert baseline.general_effects_evaluation.term_deprived_of_meeting_basis is False
    assert baseline.general_effects_evaluation.requires_human_general_effects_assessment is False

    void = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "meeting_decisions_evidence": _flip(
                    request.meeting_decisions_evidence,
                    meeting_decision_asserted=True,
                    meeting_decision_underpins_contract_term=True,
                    quorum_present=True,
                    required_majority_obtained=True,
                    contrary_to_public_order_or_morality=True,
                )
            }
        ),
        sources,
    )

    institute = void.meeting_decisions_evaluation
    assert institute.decision_void is True
    assert institute.contract_term_lacks_meeting_basis is True
    assert institute.contract_term_binds_all_participants is False

    evaluation = void.general_effects_evaluation
    # Порок условия — не порок договора: сам договор продолжает действовать.
    assert evaluation.contract_legally_effective is True
    assert evaluation.contractual_claims_enforceable is True
    assert evaluation.term_deprived_of_meeting_basis is True
    # Слой не знает, о каком именно условии идёт спор, поэтому вывод о нарушении
    # он не отменяет, а поднимает дело человеку.
    assert evaluation.breach_findings_without_effect is False
    assert evaluation.requires_human_general_effects_assessment is True
    assert any("181.5" in reason for reason in evaluation.reasons_ru)


def test_a_lawful_meeting_decision_binds_the_participants_who_voted_against() -> None:
    """Статья 181.1 работает и в положительную сторону, а не только на пороки."""
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()

    lawful = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "meeting_decisions_evidence": _flip(
                    request.meeting_decisions_evidence,
                    meeting_decision_asserted=True,
                    meeting_decision_underpins_contract_term=True,
                    quorum_present=True,
                    required_majority_obtained=True,
                )
            }
        ),
        sources,
    )

    evaluation = lawful.general_effects_evaluation
    assert evaluation.term_binding_on_all_participants is True
    assert evaluation.term_deprived_of_meeting_basis is False
    assert evaluation.term_meeting_basis_challengeable is False
    # Действительное основание условия — не повод поднимать дело человеку.
    assert evaluation.requires_human_general_effects_assessment is False


def test_general_effects_never_displaces_an_effective_contract() -> None:
    inputs = GeneralEffectsInputs(
        contract_concluded_prerequisites=True,
        non_conclusion_objection_barred=False,
        contractual_effect_displaced=False,
        partial_invalidity_only=False,
        disguised_transaction_rules_required=False,
        restitution_required=False,
        transaction_void_for_form=False,
        limitation_defense_available=False,
        claim_not_subject_to_limitation=False,
        unauthorized_representation_detected=False,
        unauthorized_disposal_detected=False,
        abuse_of_right_detected=False,
        consent_missing_for_transaction=False,
        term_calculation_defective=False,
        party_lacks_capacity=False,
        object_excluded_from_circulation=False,
        breach_issue=True,
        effective_termination=False,
        claims_accrued_before_termination=False,
        creditor_delay_excuses_debtor=False,
        liability_shifted_to_performer=False,
        obligation_discharged_full=False,
        accrued_claims_preserved=False,
        contract_term_lacks_meeting_basis=False,
        contract_term_basis_voidable=False,
        contract_term_binds_all_participants=False,
    )
    evaluation = evaluate_general_effects_constraints(
        build_general_effects_constraint_set(inputs, "case-effective"), inputs
    )

    assert evaluation.institute_conclusions_displaced is False
    assert evaluation.breach_findings_without_effect is False
    assert evaluation.contractual_claims_enforceable is True


def test_no_declared_layer_input_is_dead() -> None:
    """Вход, который ни на что не влияет, — не связь, а её видимость.

    `effective_termination` собирался из института расторжения, проверялся,
    воспроизводился в каждом артефакте и не читался ни одним выражением слоя с
    самого его появления в `0.86.0`. Аудит связности такого не ловит: он смотрит,
    какие институты питают слой, а не доходит ли вход хоть до одного вывода.

    Проверка ищет для каждого входа пару наборов, различающихся только им, при
    которых расходится хотя бы один вывод. Наборы подобраны, а не случайны:
    большинство входов срабатывает только при действующем договоре, и проба из
    одних нулей и одних единиц пропустила бы почти все.
    """
    fields = list(GeneralEffectsInputs.model_fields)
    outcomes = [
        name
        for name in GeneralEffectsEvaluation.model_fields
        if name not in {"constraint_set_id", "satisfiable", "reasons_ru", "warnings_ru"}
    ]

    def evaluate(values: dict[str, bool]):
        inputs = GeneralEffectsInputs(**values)
        return evaluate_general_effects_constraints(
            build_general_effects_constraint_set(inputs, "case-liveness"), inputs
        )

    off_base = dict.fromkeys(fields, False)
    on_base = dict.fromkeys(fields, True)
    # Договор действует: без этого набора не оживает почти ни один вход.
    effective = {**off_base, "contract_concluded_prerequisites": True}
    bases = [
        off_base,
        on_base,
        effective,
        {**effective, "breach_issue": True},
        {**effective, "limitation_defense_available": True},
        {**effective, "effective_termination": True},
        {**effective, "obligation_discharged_full": True},
        # Договор недействителен: без этого набора реституция жива только при
        # единицах, где её гасит притворность (пункт 2 статьи 170).
        {**effective, "contractual_effect_displaced": True},
    ]

    dead = []
    for field in fields:
        alive = False
        for base in bases:
            without = evaluate({**base, field: False})
            with_it = evaluate({**base, field: True})
            if any(getattr(without, name) != getattr(with_it, name) for name in outcomes):
                alive = True
                break
        if not alive:
            dead.append(field)

    assert dead == [], "Входы слоя не влияют ни на один вывод: " + ", ".join(dead)


def test_the_liveness_check_would_notice_a_dead_input() -> None:
    """Проверка обязана уметь провалиться, иначе она ничего не стоит.

    Мёртвый вход подделывается моделью, в которой поле объявлено, но выражение
    его не использует: так и выглядел `effective_termination` до выпуска `1.3.0`.
    """
    inputs = GeneralEffectsInputs(**dict.fromkeys(GeneralEffectsInputs.model_fields, False))
    live = evaluate_general_effects_constraints(
        build_general_effects_constraint_set(inputs, "case-alive"), inputs
    )
    with_termination = GeneralEffectsInputs(
        **{
            **dict.fromkeys(GeneralEffectsInputs.model_fields, False),
            "contract_concluded_prerequisites": True,
            "effective_termination": True,
        }
    )
    terminated = evaluate_general_effects_constraints(
        build_general_effects_constraint_set(with_termination, "case-terminated"), with_termination
    )

    # До выпуска 1.3.0 эти два разбора не отличались ничем.
    assert live.termination_ends_future_performance is False
    assert terminated.termination_ends_future_performance is True


def test_the_article_403_exception_reaches_the_final_conclusions() -> None:
    """Исключение статьи 403 доходит до итоговых выводов, а не остаётся при институте.

    До выпуска 1.31.0 вывод `liability_shifted_to_performer` менял оценку
    института просрочки и поднимал его флаг, но слой общих положений о нём не
    знал: нарушение, за которое по закону отвечает непосредственный исполнитель,
    оставалось основанием присуждения против должника.
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(request, sources)
    assert baseline.general_effects_evaluation.breach_findings_without_effect is False

    shifted = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "attribution_delay_evidence": _flip(
                    request.attribution_delay_evidence,
                    performance_entrusted_to_third_party=True,
                    third_party_caused_breach=True,
                    law_assigns_liability_to_performer=True,
                )
            }
        ),
        sources,
    )

    assert shifted.attribution_delay_evaluation.liability_shifted_to_performer is True
    assert shifted.constraint_evaluation.breach_issue is True
    evaluation = shifted.general_effects_evaluation
    assert evaluation.debtor_not_liable_for_performer_breach is True
    assert evaluation.breach_findings_without_effect is True
    # Договор не теряет силы, и судебная защита остаётся доступной: ответственность
    # просто лежит на другом лице.
    assert evaluation.contract_legally_effective is True
    assert evaluation.contractual_claims_enforceable is True
    assert any("статья 403" in reason for reason in evaluation.reasons_ru)


def test_the_general_rule_of_article_403_changes_nothing_in_the_layer() -> None:
    """«Должник отвечает за третье лицо» — умолчание слоя, а не новый вход."""
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    baseline = run_reviewed_contract_analysis(request, sources)
    answerable = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "attribution_delay_evidence": _flip(
                    request.attribution_delay_evidence,
                    performance_entrusted_to_third_party=True,
                    third_party_caused_breach=True,
                )
            }
        ),
        sources,
    )

    assert answerable.attribution_delay_evaluation.debtor_answerable_for_third_party is True
    assert answerable.general_effects_inputs == baseline.general_effects_inputs
    assert answerable.general_effects_evaluation == baseline.general_effects_evaluation


def test_a_barred_non_conclusion_objection_keeps_the_contract_in_force() -> None:
    """Пункт 3 статьи 432: принявший исполнение не вправе ссылаться на незаключённость.

    До выпуска 1.32.0 слой при несогласованных условиях снимал действие договора и
    все выводы институтов, даже когда возражение о незаключённости было отклонено.
    А сверка фактов требовала от институтов купли-продажи, поставки, обеспечения и
    расторжения считать договор несуществующим. Пленум ВС № 49 (пункт 6) говорит
    обратное: между сторонами возникают соответствующие обязательства.
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()
    not_agreed = {"acceptance_by_conduct": False, "performance_conduct_started_in_time": False}

    barred = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "formation_evidence": _flip(
                    request.formation_evidence,
                    **not_agreed,
                    bad_faith_non_conclusion_objection=True,
                )
            }
        ),
        sources,
    )

    assert barred.formation_evaluation.contract_concluded_prerequisites is False
    assert barred.formation_evaluation.non_conclusion_objection_barred is True
    evaluation = barred.general_effects_evaluation
    assert evaluation.non_conclusion_objection_disregarded is True
    assert evaluation.formation_defect_displaces_contract is False
    assert evaluation.contract_legally_effective is True
    assert evaluation.institute_conclusions_displaced is False
    assert evaluation.requires_human_general_effects_assessment is True
    assert not any("существенные условия согласованы" in reason for reason in evaluation.reasons_ru)


def test_without_the_bar_a_non_concluded_contract_still_stops_the_analysis() -> None:
    """Обратная сторона: без отклонённого возражения институты не могут считать договор."""
    request = build_synthetic_supply_analysis_request()
    forged = request.model_copy(
        update={
            "formation_evidence": _flip(
                request.formation_evidence,
                acceptance_by_conduct=False,
                performance_conduct_started_in_time=False,
            )
        }
    )

    with pytest.raises(FactConsistencyError) as failure:
        run_reviewed_contract_analysis(forged, build_synthetic_supply_analysis_sources())

    assert "sale_contract_status" in failure.value.keys
    assert "contractual_duty" in failure.value.keys


def test_partial_invalidity_keeps_the_rest_of_the_contract_in_force() -> None:
    """Статья 180: недействительность части не влечёт недействительности прочих частей.

    До выпуска 1.33.0 слой читал любое вытеснение договорного эффекта как
    вытеснение договора целиком и снимал все выводы институтов, а сверка фактов
    требовала от институтов считать недействительным и основное обязательство.
    """
    request = build_synthetic_supply_analysis_request()
    sources = build_synthetic_supply_analysis_sources()

    partial = run_reviewed_contract_analysis(
        request.model_copy(
            update={
                "invalidity_evidence": _flip(
                    request.invalidity_evidence,
                    transaction_concluded=True,
                    violates_law=True,
                    law_expressly_makes_void=True,
                    invalid_part_separable=True,
                    remainder_preserves_transaction_purpose=True,
                )
            }
        ),
        sources,
    )

    assert partial.invalidity_evaluation.partial_invalidity_only is True
    evaluation = partial.general_effects_evaluation
    assert evaluation.invalid_part_only is True
    assert evaluation.invalidity_displaces_contract is False
    assert evaluation.contract_legally_effective is True
    assert evaluation.institute_conclusions_displaced is False
    assert evaluation.requires_human_general_effects_assessment is True
    assert any("статья 180" in reason for reason in evaluation.reasons_ru)


def test_a_feigned_transaction_hands_the_analysis_to_the_disguised_one() -> None:
    """Пункт 2 статьи 170: притворная сделка ничтожна, к прикрываемой применяются её правила.

    До выпуска 1.34.0 слой снимал выводы и называл реституцию по статье 167 —
    так, будто сторонам остаётся вернуть полученное. Но отношения сторон определяет
    прикрываемая сделка (пункт 87 постановления Пленума ВС РФ № 25).
    """
    result = build_synthetic_supply_analysis_artifact().result
    invalidity = result.invalidity_evaluation.model_copy(
        update={
            "contractual_effect_displaced": True,
            "restitution_required": True,
            "disguised_transaction_rules_required": True,
        }
    )
    inputs = build_general_effects_inputs(
        result.formation_evaluation,
        invalidity,
        result.form_evaluation,
        result.limitation_evaluation,
        result.representation_evaluation,
        result.property_rights_evaluation,
        result.civil_principles_evaluation,
        result.transactions_evaluation,
        result.terms_evaluation,
        result.persons_evaluation,
        result.objects_evaluation,
        result.constraint_evaluation,
        result.termination_evaluation,
        result.attribution_delay_evaluation,
        result.obligation_dynamics_evaluation,
        result.meeting_decisions_evaluation,
    )
    assert inputs.disguised_transaction_rules_required is True

    evaluation = evaluate_general_effects_constraints(
        build_general_effects_constraint_set(inputs, "case-feigned"), inputs
    )
    assert evaluation.disguised_transaction_governs is True
    assert evaluation.institute_conclusions_displaced is True
    assert evaluation.restitution_regime_applies is False
    assert evaluation.requires_human_general_effects_assessment is True
    assert any("статьи 170" in reason for reason in evaluation.reasons_ru)
    assert not any("каждая из сторон обязана возвратить" in r for r in evaluation.reasons_ru)


def test_general_effects_benchmark_and_red_team_cover_boundaries() -> None:
    benchmark = run_general_effects_benchmark_suite()
    red_team = run_general_effects_red_team_suite()

    assert benchmark.total == len(SYNTHETIC_GENERAL_EFFECTS_BENCHMARKS) == 19
    assert benchmark.passed == benchmark.total
    assert red_team.total == len(SYNTHETIC_GENERAL_EFFECTS_RED_TEAM_CASES) == 20
    assert red_team.blocked == red_team.total
