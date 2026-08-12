"""Сборка рабочего стола: организация, пространства и полный разбор дела.

## Что здесь собирается

`build_case_view` — всё содержимое основного окна по одному делу: квалификация,
линия вывода и спор, три регистра изложения, очередь пробелов, карта разбора и
журнал замечаний.

`build_demo_desktop` — стенд для самостоятельного тестирования: организация с
двумя изолированными пространствами.

**Демонстрация** — синтетическое дело о поставке. На нём видно, как выглядит
разбор, дошедший до итоговых выводов.

**Реальная практика** — четыре дела Верховного Суда из `data/practice`. Факты
дела накладываются на демонстрационное дело: полностью собрать реальное дело
нельзя, выгрузка не содержит фактов для остальных институтов. Оговорка
записана в карточке каждого дела, а не спрятана в спецификации, — иначе стенд
внушал бы, что система «решила дело как суд».
"""

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.real_case_pipeline import build_real_case_request
from causa.institutional.contracts.real_case_scenarios import REAL_CASE_SCENARIOS
from causa.institutional.contracts.reviewed_analysis import (
    ReviewedContractAnalysisRequest,
    ReviewedContractAnalysisResult,
    run_reviewed_contract_analysis,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_sources,
)
from causa.phase0.demo_trace import build_supply_dispute_demo_trace
from causa.reasoning.counterfactual import CounterfactualBudget
from causa.translation_pipeline import TranslationBundle
from causa.ui.case_map import CaseMap, NodeKind, build_case_map
from causa.ui.gaps import GapQueue, build_gap_queue
from causa.ui.institute_titles import INSTITUTE_TITLES_RU
from causa.ui.labels import SourceLabel, source_labels
from causa.ui.qualification import CaseQualification, build_case_qualification
from causa.ui.reasoning import ReasoningView, build_reasoning_view
from causa.ui.remarks import OperatorRemark, RemarkLedger, build_remark_ledger
from causa.ui.verdict import CaseVerdict, build_case_verdict
from causa.ui.workspace import (
    CaseCard,
    Desk,
    Operator,
    OperatorRole,
    Organisation,
    Workspace,
)

DESKTOP_VERSION = "ui-desktop-v0"

DEMO_ORGANISATION_ID = "org-demo"
DEMO_WORKSPACE_ID = "ws-demo-supply"
PRACTICE_WORKSPACE_ID = "ws-practice-vs"


class CaseView(BaseModel):
    """Полное содержимое основного окна по одному делу."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = DESKTOP_VERSION
    case_id: str
    title_ru: str
    workspace_id: str
    #: Оговорка о том, чем этот разбор является. Пусто для демонстрационного дела.
    caveat_ru: str = ""
    #: Главный ответ по делу — то, что читается первым.
    verdict: CaseVerdict
    qualification: CaseQualification
    reasoning: ReasoningView
    gaps: GapQueue
    map: CaseMap
    remarks: RemarkLedger
    #: Подписи к идентификаторам источников, на которых держится линия вывода.
    sources: list[SourceLabel] = Field(default_factory=list)

    @property
    def open_debt_ru(self) -> list[str]:
        return [
            INSTITUTE_TITLES_RU[edge.source.split(":", 1)[1]]
            for edge in self.map.edges
            if edge.open_debt
        ]

    def card(self) -> CaseCard:
        primary = self.qualification.primary
        return CaseCard(
            case_id=self.case_id,
            title_ru=self.title_ru,
            workspace_id=self.workspace_id,
            cluster_ru=primary.title_ru if primary else "кластер не определён",
            blocking_gaps=self.gaps.blocking_count,
            open_debt_ru=self.open_debt_ru,
            needs_human=any(node.needs_human for node in self.map.nodes),
        )


def build_case_view(
    *,
    case_id: str,
    title_ru: str,
    workspace_id: str,
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
    bundle: TranslationBundle | None = None,
    remarks: list[OperatorRemark] | None = None,
    caveat_ru: str = "",
) -> CaseView:
    """Собрать окно дела из результата конвейера."""
    qualification = build_case_qualification(result)
    gaps = build_gap_queue(result)
    case_map = build_case_map(request, result)
    return CaseView(
        case_id=case_id,
        title_ru=title_ru,
        workspace_id=workspace_id,
        caveat_ru=caveat_ru,
        verdict=build_case_verdict(result, qualification, gaps),
        qualification=qualification,
        reasoning=build_reasoning_view(request, result, bundle),
        gaps=gaps,
        map=case_map,
        remarks=build_remark_ledger(case_id, remarks or []),
        sources=source_labels(
            [node.title_ru for node in case_map.nodes if node.kind is NodeKind.SOURCE]
        ),
    )


def build_demo_case_view() -> CaseView:
    """Демонстрационное дело о поставке — со всеми артефактами Этапа 0."""
    trace = build_supply_dispute_demo_trace()
    return build_case_view(
        case_id=trace.analysis_result.case_id,
        title_ru="Поставка: спор о просрочке передачи товара",
        workspace_id=DEMO_WORKSPACE_ID,
        request=trace.analysis_request,
        result=trace.analysis_result,
        bundle=trace.translation_bundle,
    )


_PRACTICE_CAVEAT = (
    "Факты этого дела наложены на демонстрационное дело о поставке: заменены "
    "факты одного института, остальные наборы фактов остались синтетическими. "
    "Проверяется, что правовая суть дела проходит конвейер и доходит до итога, "
    "а не то, что система решила дело так же, как суд."
)


def build_practice_case_views() -> list[CaseView]:
    """Четыре дела Верховного Суда, прогнанные через весь конвейер."""
    sources = build_synthetic_supply_analysis_sources()
    budget = CounterfactualBudget()
    views: list[CaseView] = []
    for scenario in REAL_CASE_SCENARIOS:
        request = build_real_case_request(scenario)
        result = run_reviewed_contract_analysis(request, sources, counterfactual_budget=budget)
        views.append(
            build_case_view(
                case_id=scenario.case_id,
                title_ru=(f"{scenario.case_number} — {INSTITUTE_TITLES_RU[scenario.institute]}"),
                workspace_id=PRACTICE_WORKSPACE_ID,
                request=request,
                result=result,
                caveat_ru=f"{_PRACTICE_CAVEAT} Позиция суда: {scenario.court_holding_ru}",
            )
        )
    return views


class DesktopState(BaseModel):
    """Всё, что нужно интерфейсу: стол оператора и разборы дел."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = DESKTOP_VERSION
    desk: Desk
    case_views: list[CaseView] = Field(default_factory=list)

    def view(self, workspace_id: str, case_id: str) -> CaseView:
        # Проверка доступа выполняется столом, а не интерфейсом.
        self.desk.case(workspace_id, case_id)
        return next(
            view
            for view in self.case_views
            if view.workspace_id == workspace_id and view.case_id == case_id
        )


def build_demo_desktop() -> DesktopState:
    """Собрать стенд целиком: организация, два пространства, пять дел."""
    demo_view = build_demo_case_view()
    practice_views = build_practice_case_views()

    demo_workspace = Workspace(
        id=DEMO_WORKSPACE_ID,
        title_ru="Демонстрация: поставка",
        organisation_id=DEMO_ORGANISATION_ID,
        sla_mode="standard",
        risk_tier="t2_internal_memo",
        cases=[demo_view.card()],
    )
    practice_workspace = Workspace(
        id=PRACTICE_WORKSPACE_ID,
        title_ru="Практика Верховного Суда",
        organisation_id=DEMO_ORGANISATION_ID,
        sla_mode="deep",
        risk_tier="t3_draft_letter",
        cases=[view.card() for view in practice_views],
    )
    operator = Operator(
        id="op-demo",
        display_name="Оператор стенда",
        role=OperatorRole.LAWYER,
    )
    organisation = Organisation(
        id=DEMO_ORGANISATION_ID,
        title_ru="Демонстрационная организация",
        operators=[
            operator,
            Operator(id="rev-demo", display_name="Проверяющий", role=OperatorRole.REVIEWER),
            Operator(
                id="own-demo",
                display_name="Владелец знания",
                role=OperatorRole.KNOWLEDGE_OWNER,
            ),
        ],
        workspaces=[demo_workspace, practice_workspace],
    )
    return DesktopState(
        desk=Desk(
            organisation=organisation,
            operator=operator,
            workspace_ids=[DEMO_WORKSPACE_ID, PRACTICE_WORKSPACE_ID],
        ),
        case_views=[demo_view, *practice_views],
    )
