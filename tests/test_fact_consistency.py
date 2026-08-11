"""Тесты слоя сверки фактов рецензента с выводами модели."""

import pytest

from causa.institutional.contracts.case_scenarios import _flip
from causa.institutional.contracts.fact_consistency import (
    FACT_CONSISTENCY_VOCABULARY,
    FactConsistencyCollector,
    FactConsistencyError,
)
from causa.institutional.contracts.contradiction_taxonomy import (
    CROSS_INSTITUTE_CONTRADICTION_TYPES,
)
from causa.institutional.contracts.reviewed_analysis import run_reviewed_contract_analysis
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
    build_synthetic_supply_analysis_sources,
)


def test_agreeing_facts_produce_no_error() -> None:
    collector = FactConsistencyCollector()

    collector.equal("contractual_duty", True, True)
    collector.implies("termination_substantial_breach", False, False)

    assert collector.mismatches == []
    collector.raise_if_any()


def test_every_mismatch_speaks_russian_and_names_its_basis() -> None:
    collector = FactConsistencyCollector()
    collector.equal("sale_contract_status", actual=False, expected=True)

    with pytest.raises(FactConsistencyError) as failure:
        collector.raise_if_any()

    message = str(failure.value)
    assert "Данные рецензента противоречат выводам модели" in message
    assert "статей 432–443 ГК РФ" in message
    assert "указано «нет»" in message
    assert "следует «да»" in message
    # Ошибка типизирована: разбор доступен полями, а не разбором строки.
    assert failure.value.keys == ["sale_contract_status"]
    assert failure.value.mismatches[0].expected is True
    assert failure.value.mismatches[0].actual is False


def test_check_without_a_russian_description_is_rejected() -> None:
    """Объявить сверку и не описать её по-русски теперь нельзя."""
    collector = FactConsistencyCollector()

    with pytest.raises(KeyError, match="не описана по-русски"):
        collector.equal("сверка-которой-нет", actual=True, expected=False)


def test_analysis_reports_every_mismatch_at_once() -> None:
    """Главное, ради чего слой написан: расхождения выдаются разом.

    Прежде анализ падал на первом расхождении, и о следующем можно было узнать
    только после исправления предыдущего — по одному прогону на расхождение.
    """
    request = build_synthetic_supply_analysis_request()
    # Договорный эффект вытеснен недействительностью, но зависимые институты об
    # этом не знают.
    displaced = request.model_copy(
        update={
            "invalidity_evidence": _flip(
                request.invalidity_evidence,
                {
                    "transaction_concluded": True,
                    "violates_law": True,
                    "law_expressly_makes_void": True,
                },
            )
        }
    )

    with pytest.raises(FactConsistencyError) as failure:
        run_reviewed_contract_analysis(displaced, build_synthetic_supply_analysis_sources())

    assert len(failure.value.mismatches) > 1
    assert "contractual_duty" in failure.value.keys
    assert "security_invalidity_status" in failure.value.keys


def test_rejection_does_not_depend_on_check_order() -> None:
    """Набор расхождений определяется данными, а не порядком проверок."""
    request = build_synthetic_supply_analysis_request()
    displaced = request.model_copy(
        update={
            "invalidity_evidence": _flip(
                request.invalidity_evidence,
                {
                    "transaction_concluded": True,
                    "violates_law": True,
                    "law_expressly_makes_void": True,
                },
            )
        }
    )
    sources = build_synthetic_supply_analysis_sources()

    with pytest.raises(FactConsistencyError) as first:
        run_reviewed_contract_analysis(displaced, sources)
    with pytest.raises(FactConsistencyError) as second:
        run_reviewed_contract_analysis(displaced, sources)

    assert first.value.keys == second.value.keys
    assert first.value.keys == sorted(first.value.keys, key=first.value.keys.index)


def test_the_two_ways_of_handling_contradictions_do_not_overlap() -> None:
    """Граница между отвержением и флагом экспертизы закреплена, а не подразумевается.

    Отвергается расхождение, при котором решателю пришлось бы выбирать одну из
    версий факта; называется и помечается флагом расхождение, при котором обе
    версии уживаются в анализе. Пересечение означало бы, что один и тот же
    случай обрабатывается двумя способами сразу.
    """
    hard = set(FACT_CONSISTENCY_VOCABULARY)
    soft = set(CROSS_INSTITUTE_CONTRADICTION_TYPES)

    assert hard & soft == set()
    assert hard and soft


def test_every_declared_check_carries_a_basis() -> None:
    """Каждая сверка называет и факт, и то, из чего следует ожидаемое значение."""
    for key, (fact_ru, anchor_ru) in FACT_CONSISTENCY_VOCABULARY.items():
        assert fact_ru.strip(), key
        assert anchor_ru.strip(), key
        assert len(anchor_ru) > 30, key
