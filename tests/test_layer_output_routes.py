"""Аудит связности по выводам: маршрут каждого вывода питающих институтов."""

import pytest

from causa.institutional.contracts.general_effects import GeneralEffectsInputs
from causa.institutional.contracts.layer_output_routes import (
    LAYER_OUTPUT_ROUTES,
    OutputRoute,
    measure_layer_outputs,
    open_output_debt,
)
from causa.institutional.contracts.real_case_pipeline import LAYER_FED_BY

MEASURED = measure_layer_outputs()


def _unrecorded(institute: str, record: dict) -> tuple[set[str], set[str]]:
    measured = MEASURED[institute]
    expected = measured["outputs"] - measured["wired"] - measured["components"]
    return expected - set(record), set(record) - expected


def test_every_layer_feeding_institute_has_a_record() -> None:
    assert set(LAYER_OUTPUT_ROUTES) == set(LAYER_FED_BY) == set(MEASURED)


@pytest.mark.parametrize("institute", sorted(LAYER_FED_BY))
def test_the_record_covers_exactly_the_unwired_outputs(institute: str) -> None:
    """Ни одного вывода без маршрута — и ни одной записи о проведённом выводе."""
    missing, extra = _unrecorded(institute, LAYER_OUTPUT_ROUTES[institute])

    assert missing == set(), f"{institute}: выводы без маршрута: {sorted(missing)}"
    assert extra == set(), f"{institute}: записаны проведённые или несуществующие: {sorted(extra)}"


def test_the_check_would_notice_an_unrecorded_output() -> None:
    """Проверка обязана уметь провалиться: удалённая запись обнаруживается."""
    record = dict(LAYER_OUTPUT_ROUTES["formation"])
    record.pop("counteroffer_detected")

    missing, _ = _unrecorded("formation", record)

    assert missing == {"counteroffer_detected"}


def test_a_route_through_another_input_names_a_real_layer_input() -> None:
    """«Через другой вход» без названного входа — это не маршрут, а его видимость."""
    inputs = set(GeneralEffectsInputs.model_fields)
    for institute, routes in LAYER_OUTPUT_ROUTES.items():
        for name, (route, reason) in routes.items():
            assert len(reason) > 40, (institute, name)
            if route is OutputRoute.VIA_INPUT:
                assert any(field in reason for field in inputs), (institute, name)


def test_the_open_debt_is_pinned() -> None:
    """Открытый долг виден в тесте, а не только в модуле, и обязан уменьшаться."""
    assert open_output_debt() == {
        "limitation": ["limitation_restorable"],
        "obligation_dynamics": ["debtor_original_performance_discharges"],
        "property_rights": ["good_faith_purchaser_breached"],
        "terms": [
            "non_working_day_duty_breached",
            "organisation_operating_hours_duty_breached",
            "performance_deadline_duty_breached",
            "term_definition_duty_breached",
            "term_end_duty_breached",
            "term_event_certainty_duty_breached",
            "term_start_duty_breached",
            "written_notice_dispatch_duty_breached",
        ],
        "transactions": [
            "condition_interference_duty_breached",
            "conditional_transaction_duty_breached",
        ],
    }


def test_the_measurement_counts_what_the_audit_counts() -> None:
    """Сколько выводов, сколько в слое, сколько составляющих — закреплено числом."""
    outputs = sum(len(item["outputs"]) for item in MEASURED.values())
    wired = sum(len(item["wired"]) for item in MEASURED.values())
    components = sum(len(item["components"]) for item in MEASURED.values())
    recorded = sum(len(routes) for routes in LAYER_OUTPUT_ROUTES.values())

    assert (outputs, wired, components, recorded) == (236, 26, 86, 124)
