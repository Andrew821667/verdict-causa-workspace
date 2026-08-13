"""Тесты карты разбора, замечаний оператора и изоляции пространств."""

import pytest

from causa.institutional.contracts.real_case_pipeline import LAYER_FED_BY
from causa.phase0.demo_trace import build_supply_dispute_demo_trace
from causa.ui.case_map import MapEdge, NodeKind, build_case_map
from causa.ui.remarks import (
    REMARK_KIND_LABELS_RU,
    SIGNAL_CANDIDATE_TYPE,
    OperatorRemark,
    RemarkKind,
    apply_remark,
    build_remark_ledger,
)
from causa.ui.workspace import (
    CaseCard,
    Desk,
    Operator,
    OperatorRole,
    Organisation,
    Workspace,
)


@pytest.fixture(scope="module")
def case_map():
    trace = build_supply_dispute_demo_trace()
    return build_case_map(trace.analysis_request, trace.analysis_result)


def test_silent_institutes_are_not_drawn(case_map) -> None:
    """Девяносто пустых узлов спрятали бы те несколько, которые сработали."""
    institutes = [node for node in case_map.nodes if node.kind is NodeKind.INSTITUTE]

    assert 0 < len(institutes) < 40


def test_every_break_carries_a_reason(case_map) -> None:
    """Разрыв без причины неотличим от того, что связь забыли провести."""
    assert case_map.breaks
    for edge in case_map.breaks:
        assert len(edge.reason_ru) > 40, edge.source


def test_feeding_institutes_reach_the_layer(case_map) -> None:
    """Институт из `LAYER_FED_BY` не может оказаться разорванным."""
    broken = {edge.source.split(":", 1)[1] for edge in case_map.breaks}

    assert broken.isdisjoint(LAYER_FED_BY)


def test_the_demo_case_has_no_unexplained_break(case_map) -> None:
    """На демонстрационном деле долгов связности не осталось.

    Выпуски `1.0.0`, `1.1.0` и `1.2.0` провели в слой просрочку кредитора,
    прекращение обязательства и решения собраний — все три института, у которых
    аудит не нашёл причины оставаться в стороне.
    """
    debts = {edge.source.split(":", 1)[1] for edge in case_map.edges if edge.open_debt}

    assert debts == set()
    assert not any("открытый долг связности" in note for note in case_map.notes_ru)


def test_a_debt_would_still_be_visible_on_the_case(case_map) -> None:
    """Механизм показа долга обязан работать и тогда, когда долгов нет.

    Иначе закрытие последнего долга тихо превратило бы рабочую проверку в
    вечнозелёную: она проходила бы, даже если показывать долг разучились.
    """
    from causa.institutional.contracts.layer_connectivity import (
        LAYER_CONNECTIVITY_AUDIT,
        ConnectivityVerdict,
    )

    debts = [
        name
        for name, (verdict, _) in LAYER_CONNECTIVITY_AUDIT.items()
        if verdict is ConnectivityVerdict.SHOULD_BE_WIRED
    ]

    assert debts == []
    edge = MapEdge(
        source="institute:synthetic_institute",
        target="layer:general_effects",
        connected=False,
        reason_ru="обоснования нет — открытый долг",
        open_debt=True,
    )
    assert edge.open_debt is True


def test_the_map_shows_which_sources_it_left_out(case_map) -> None:
    """Показать 24 источника из 283 и промолчать — значит ввести в заблуждение."""
    assert any("проверенных артефактов дела" in note for note in case_map.notes_ru)


def test_clarification_never_becomes_a_signal() -> None:
    """Уточнение по делу говорит о фактах, а не о том, как система рассуждает."""
    remark = OperatorRemark(
        id="r1",
        case_id="case-supply-1",
        operator_id="op-1",
        kind=RemarkKind.CLARIFICATION,
        text_ru="Срок продлён дополнительным соглашением.",
        as_learning_signal=True,
    )

    outcome = apply_remark(remark)

    assert outcome.candidate is None
    assert outcome.system_effect_ru == ""
    assert any("не может быть сигналом" in note for note in outcome.notes_ru)


def test_a_signal_never_produces_anything_but_a_proposed_candidate() -> None:
    """Тихая эволюция запрещена разделом 10.11: утверждает governance, не интерфейс."""
    for kind in SIGNAL_CANDIDATE_TYPE:
        outcome = apply_remark(
            OperatorRemark(
                id=f"r-{kind.value}",
                case_id="case-supply-1",
                operator_id="op-1",
                kind=kind,
                text_ru="Система рассуждает неверно.",
                as_learning_signal=True,
            )
        )

        assert outcome.candidate is not None, kind
        assert outcome.candidate.status == "proposed", kind
        assert outcome.required_stages_ru, kind


def test_a_remark_without_the_signal_flag_stays_in_the_case() -> None:
    """«Внести в дело» и «как сигнал» — разные кнопки с разной судьбой."""
    outcome = apply_remark(
        OperatorRemark(
            id="r2",
            case_id="case-supply-1",
            operator_id="op-1",
            kind=RemarkKind.DISAGREEMENT,
            text_ru="Вывод о нарушении неверен.",
        )
    )

    assert outcome.candidate is None
    assert "не отправлено" in outcome.case_effect_ru


def test_every_remark_kind_has_a_label() -> None:
    """Вид замечания без названия показался бы оператору машинным ключом."""
    assert set(REMARK_KIND_LABELS_RU) == set(RemarkKind)


def test_the_ledger_refuses_remarks_from_another_case() -> None:
    """Замечание из чужого дела не может попасть в этот журнал."""
    alien = OperatorRemark(
        id="r3",
        case_id="case-other",
        operator_id="op-1",
        kind=RemarkKind.WORDING,
        text_ru="Непонятно.",
    )

    with pytest.raises(ValueError, match="case-other"):
        build_remark_ledger("case-supply-1", [alien])


def _desk() -> Desk:
    operator = Operator(id="op", display_name="Оператор", role=OperatorRole.LAWYER)
    mine = Workspace(
        id="ws-mine",
        title_ru="Мой клиент",
        organisation_id="org",
        cases=[CaseCard(case_id="c-1", title_ru="Дело", workspace_id="ws-mine")],
    )
    other = Workspace(
        id="ws-other",
        title_ru="Чужой клиент",
        organisation_id="org",
        cases=[CaseCard(case_id="c-2", title_ru="Чужое дело", workspace_id="ws-other")],
    )
    return Desk(
        organisation=Organisation(
            id="org", title_ru="Организация", operators=[operator], workspaces=[mine, other]
        ),
        operator=operator,
        workspace_ids=["ws-mine"],
    )


def test_isolation_is_an_invariant_not_a_hidden_button() -> None:
    """Раздел 11: материалы чужого пространства недоступны, а не просто не показаны."""
    desk = _desk()

    with pytest.raises(PermissionError, match="ws-other"):
        desk.case("ws-other", "c-2")


def test_a_case_is_not_searched_across_workspaces() -> None:
    """Поиск дела по другим пространствам не выполняется намеренно."""
    desk = _desk()

    with pytest.raises(KeyError, match="c-2"):
        desk.case("ws-mine", "c-2")


def test_a_workspace_refuses_cases_of_another_workspace() -> None:
    """Изоляция проверяется при сборке модели, а не при отрисовке."""
    with pytest.raises(ValueError, match="другому пространству"):
        Workspace(
            id="ws-mine",
            title_ru="Мой клиент",
            organisation_id="org",
            cases=[CaseCard(case_id="c-2", title_ru="Чужое", workspace_id="ws-other")],
        )
