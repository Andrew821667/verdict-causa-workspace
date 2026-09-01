"""Сборка рабочего стола: организация, пространства и полный разбор дела.

## Что здесь собирается

`build_case_view` — всё содержимое основного окна по одному делу: квалификация,
линия вывода и спор, три регистра изложения, очередь пробелов, карта разбора и
журнал замечаний.

`build_demo_desktop` — стенд для самостоятельного тестирования: организация с
двумя изолированными пространствами.

**Демонстрация** — синтетическое дело о поставке. На нём видно, как выглядит
разбор, дошедший до итоговых выводов.

**Реальная практика** — переведённые дела из `data/practice`: четыре определения
Верховного Суда и тридцать шесть постановлений арбитражных судов округов и
кассационных судов общей юрисдикции. Факты дела накладываются на
демонстрационное дело: полностью собрать реальное дело нельзя, выгрузка не
содержит фактов для остальных институтов. Оговорка
записана в карточке каждого дела, а не спрятана в спецификации, — иначе стенд
внушал бы, что система «решила дело как суд».
"""

from pydantic import BaseModel, ConfigDict, Field

from causa.institutional.contracts.bankruptcy_case_map import BankruptcyCaseMap
from causa.institutional.contracts.synthetic_bankruptcy_case_map import (
    build_synthetic_bankruptcy_case_map,
)
from causa.institutional.contracts.real_case_pipeline import build_real_case_request
from causa.institutional.contracts.real_case_pipeline_expectations import (
    PIPELINE_REJECTION_REASONS_RU,
)
from causa.institutional.contracts.real_case_scenarios import REAL_CASE_SCENARIOS
from causa.institutional.contracts.reviewed_analysis import (
    ReviewedContractAnalysisRequest,
    ReviewedContractAnalysisResult,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_sources,
)
from causa.phase0.demo_trace import build_supply_dispute_demo_trace
from causa.translation_pipeline import TranslationBundle
from causa.reasoning.adversarial import (
    TwoWorldDebate,
    build_two_world_debate,
    contested_without_documents,
)
from causa.reasoning.three_valued import ThreeValuedEvaluation, evaluate_with_unknowns
from causa.ui.case_map import CaseMap, NodeKind, build_case_map
from causa.ui.case_story import CaseStory, build_case_story
from causa.ui.court_filing import CourtFiling, build_court_filing
from causa.ui.gaps import GapQueue, build_gap_queue
from causa.ui.document_text import ExtractedText, GapEvidenceHints, build_gap_hints
from causa.ui.documents import GapClosure, UploadedDocument
from causa.ui.institute_titles import INSTITUTE_TITLES_RU
from causa.ui.labels import SourceLabel, source_labels
from causa.ui.qualification import CaseQualification, build_case_qualification
from causa.ui.reasoning import ReasoningView, build_reasoning_view
from causa.ui.relation_scheme import RelationScheme, build_relation_scheme
from causa.ui.remarks import OperatorRemark, RemarkLedger, build_remark_ledger
from causa.ui.session import CaseInputs, CaseSession
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
BANKRUPTCY_WORKSPACE_ID = "ws-bankruptcy-map"


class CaseView(BaseModel):
    """Полное содержимое основного окна по одному делу."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = DESKTOP_VERSION
    case_id: str
    title_ru: str
    workspace_id: str
    #: Оговорка о том, чем этот разбор является. Пусто для демонстрационного дела.
    caveat_ru: str = ""
    #: Фабула: что произошло. Читается раньше вердикта — вопрос раньше ответа.
    story: CaseStory
    #: Главный ответ по делу.
    verdict: CaseVerdict
    qualification: CaseQualification
    reasoning: ReasoningView
    gaps: GapQueue
    map: CaseMap
    #: Схема правоотношения: кто кому что должен и чем это кончилось.
    scheme: RelationScheme
    #: Что выводится при неустановленных фактах и кто отвечает за недоказанное.
    uncertainty: ThreeValuedEvaluation
    #: Спор как расхождение мира истца и мира ответчика.
    worlds: TwoWorldDebate
    remarks: RemarkLedger
    #: Подписи к идентификаторам источников, на которых держится линия вывода.
    sources: list[SourceLabel] = Field(default_factory=list)
    #: Документы, приложенные оператором в этой сессии.
    documents: list[UploadedDocument] = Field(default_factory=list)
    #: Пробелы, которые оператор закрыл документом.
    closures: list[GapClosure] = Field(default_factory=list)
    #: Текст приложенных документов — то, что оператор может прочитать здесь.
    document_texts: list[ExtractedText] = Field(default_factory=list)
    #: Места в документах, совпавшие со словами открытых вопросов.
    hints: list[GapEvidenceHints] = Field(default_factory=list)
    #: Проект процессуального документа по выводу системы.
    filing: CourtFiling
    #: Сводная карта дела о банкротстве — только у дел, которые её имеют.
    #: Конвейер разбирает один спор, а дело о банкротстве — это десятки
    #: требований и сделок; поэтому карта не выводится здесь, а приходит
    #: входом и лишь показывается.
    bankruptcy_map: BankruptcyCaseMap | None = None

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
    documents: list[UploadedDocument] | None = None,
    closures: list[GapClosure] | None = None,
    texts: list[ExtractedText] | None = None,
    claimed_articles: list[str] | None = None,
    unknown_facts: list[str] | None = None,
    bankruptcy_map: BankruptcyCaseMap | None = None,
) -> CaseView:
    """Собрать окно дела из результата конвейера."""
    qualification = build_case_qualification(result, claimed_articles)
    gaps = build_gap_queue(result)
    case_map = build_case_map(request, result)
    verdict = build_case_verdict(result, qualification, gaps)
    story = build_case_story(result, qualification)
    reasoning = build_reasoning_view(request, result, bundle)
    return CaseView(
        case_id=case_id,
        title_ru=title_ru,
        workspace_id=workspace_id,
        caveat_ru=caveat_ru,
        story=story,
        verdict=verdict,
        qualification=qualification,
        reasoning=reasoning,
        gaps=gaps,
        map=case_map,
        scheme=build_relation_scheme(result, qualification, verdict),
        uncertainty=evaluate_with_unknowns(
            result.constraint_set,
            result.evidence_mapping.facts,
            set(unknown_facts or ()),
        ),
        worlds=build_two_world_debate(
            result.constraint_set,
            result.evidence_mapping.facts,
            contested_without_documents(result),
        ),
        remarks=build_remark_ledger(case_id, remarks or []),
        sources=source_labels(
            [node.title_ru for node in case_map.nodes if node.kind is NodeKind.SOURCE]
        ),
        documents=list(documents or []),
        closures=list(closures or []),
        document_texts=list(texts or []),
        hints=build_gap_hints(gaps.gaps, list(texts or [])),
        filing=build_court_filing(
            result=result,
            story=story,
            line=reasoning.line,
            qualification=qualification,
            verdict=verdict,
            gaps=gaps,
            documents=list(documents or []),
        ),
        bankruptcy_map=bankruptcy_map,
    )


def build_demo_case_inputs() -> CaseInputs:
    """Входы демонстрационного дела о поставке."""
    trace = build_supply_dispute_demo_trace()
    return CaseInputs(
        case_id=trace.analysis_result.case_id,
        title_ru="Поставка: спор о просрочке передачи товара",
        workspace_id=DEMO_WORKSPACE_ID,
        request=trace.analysis_request,
        sources=list(trace.legal_sources),
        bundle=trace.translation_bundle,
    )


def build_demo_case_view() -> CaseView:
    """Демонстрационное дело о поставке — со всеми артефактами Этапа 0."""
    return CaseSession(build_demo_case_inputs()).build_view()


_PRACTICE_CAVEAT = (
    "Факты этого дела наложены на демонстрационное дело о поставке: заменены "
    "факты одного института, остальные наборы фактов остались синтетическими. "
    "Проверяется, что правовая суть дела проходит конвейер и доходит до итога, "
    "а не то, что система решила дело так же, как суд."
)


_BANKRUPTCY_CAVEAT = (
    "Карта дела настоящая: шесть требований, две сделки и зачёт проведены "
    "через реальные функции четырёх институтов банкротства. Остальные вкладки "
    "окна — разбор демонстрационного дела о поставке: конвейер разбирает один "
    "спор, а дело о банкротстве — это десятки требований сразу, и одной формой "
    "запроса они не описываются. Смешивать их молча было бы хуже, чем сказать "
    "об этом здесь."
)


def build_bankruptcy_case_inputs() -> CaseInputs:
    """Входы дела, у которого есть сводная карта банкротства."""
    trace = build_supply_dispute_demo_trace()
    return CaseInputs(
        case_id="case-bankruptcy-map-demo",
        title_ru="Банкротство ООО «Стройторг»: карта дела",
        workspace_id=BANKRUPTCY_WORKSPACE_ID,
        request=trace.analysis_request,
        sources=list(trace.legal_sources),
        bundle=trace.translation_bundle,
        caveat_ru=_BANKRUPTCY_CAVEAT,
        bankruptcy_map=build_synthetic_bankruptcy_case_map(),
    )


def build_bankruptcy_case_view() -> CaseView:
    """Окно дела о банкротстве со сводной картой."""
    return CaseSession(build_bankruptcy_case_inputs()).build_view()


def build_practice_case_inputs() -> list[CaseInputs]:
    """Входы дел практики, для которых конвейер может построить окно."""
    sources = build_synthetic_supply_analysis_sources()
    return [
        CaseInputs(
            case_id=scenario.case_id,
            title_ru=f"{scenario.case_number} — {INSTITUTE_TITLES_RU[scenario.institute]}",
            workspace_id=PRACTICE_WORKSPACE_ID,
            request=build_real_case_request(scenario),
            sources=list(sources),
            caveat_ru=f"{_PRACTICE_CAVEAT} Позиция суда: {scenario.court_holding_ru}",
        )
        for scenario in REAL_CASE_SCENARIOS
        if scenario.case_id not in PIPELINE_REJECTION_REASONS_RU
    ]


def build_practice_case_views() -> list[CaseView]:
    """Переведённые дела практики, прогнанные через весь конвейер.

    Дела, стоящие в очереди на перевод, на стенде не появляются: показывать
    дело, для которого фактов ещё нет, значило бы показывать чужой разбор под
    его номером.

    Не появляются и дела, которые конвейер отвергает на сверке входов, — они
    названы в `PIPELINE_REJECTION_REASONS_RU` с причиной. Окно для такого дела
    построить нельзя, и подменять отказ пустой карточкой было бы хуже, чем не
    показывать его вовсе.

    Сейчас этот список пуст. Четырнадцать дел о незаключённости,
    недействительности, прекращении обязательства и убытках стенд терял: их
    факты противоречили остальным контрактам демонстрационного дела. Теперь
    каждое такое дело объявляет следствия позиции суда за пределами своего
    института (`dependent_facts` сценария), и все пятьдесят четыре дела
    практики доходят до окна.
    """
    return [CaseSession(inputs).build_view() for inputs in build_practice_case_inputs()]


def build_demo_sessions() -> list[CaseSession]:
    """Сессии всех дел стенда: они умеют пересчитываться, а окна — нет."""
    return [
        CaseSession(inputs)
        for inputs in [
            build_demo_case_inputs(),
            *build_practice_case_inputs(),
            build_bankruptcy_case_inputs(),
        ]
    ]


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


def build_demo_desktop(views: list[CaseView] | None = None) -> DesktopState:
    """Собрать стенд целиком: организация, два пространства, пять дел.

    Готовые окна можно передать: после пересчёта дела стол пересобирается из
    уже посчитанных окон, а не считает всё заново.
    """
    if views is None:
        views = [
            build_demo_case_view(),
            *build_practice_case_views(),
            build_bankruptcy_case_view(),
        ]
    demo_view = next(view for view in views if view.workspace_id == DEMO_WORKSPACE_ID)
    practice_views = [view for view in views if view.workspace_id == PRACTICE_WORKSPACE_ID]
    bankruptcy_views = [view for view in views if view.workspace_id == BANKRUPTCY_WORKSPACE_ID]

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
        # Название пришлось поправить: оно осталось от первой выгрузки, когда все
        # дела были актами Верховного Суда. После второй выгрузки из сорока дел
        # стенда таких четыре, а тридцать шесть вынесены арбитражными судами
        # округов и кассационными судами общей юрисдикции. Прежнее название
        # обещало не тот источник, а по нему судят о весе разобранной практики.
        title_ru="Практика кассационных судов",
        organisation_id=DEMO_ORGANISATION_ID,
        sla_mode="deep",
        risk_tier="t3_draft_letter",
        cases=[view.card() for view in practice_views],
    )
    bankruptcy_workspace = Workspace(
        id=BANKRUPTCY_WORKSPACE_ID,
        title_ru="Банкротство: карта дела",
        organisation_id=DEMO_ORGANISATION_ID,
        sla_mode="deep",
        risk_tier="t3_draft_letter",
        cases=[view.card() for view in bankruptcy_views],
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
        workspaces=[demo_workspace, practice_workspace, bankruptcy_workspace],
    )
    return DesktopState(
        desk=Desk(
            organisation=organisation,
            operator=operator,
            workspace_ids=[
                DEMO_WORKSPACE_ID,
                PRACTICE_WORKSPACE_ID,
                BANKRUPTCY_WORKSPACE_ID,
            ],
        ),
        case_views=[demo_view, *practice_views, *bankruptcy_views],
    )
