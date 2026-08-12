"""Сессия дела: пересчёт после того, как оператор что-то добавил.

## Зачем отдельный слой

`CaseView` — снимок разбора. Чтобы разбор изменился, нужны входы: запрос к
конвейеру, источники и накопленные действия оператора. Сессия держит их вместе
и умеет одно: пересобрать дело заново, когда добавился документ.

## Что считается изменением

Пересчёт идёт по **всему** конвейеру, а не по одной модели. Иначе получилось бы
то, чего этот проект уже дважды избегал: вывод, изменившийся в одном институте
и не дошедший до итога. Разница считается по тому, что читает юрист: вердикт,
звенья линии вывода, число блокирующих пробелов.

## Граница

Сессия живёт в памяти процесса. Стенд предназначен для проверки разбора, а не
для ведения дел: перезапуск теряет и документы, и пересчёт.
"""

from pydantic import BaseModel, ConfigDict, Field

from causa.core.models import LegalSource
from causa.institutional.contracts.fact_consistency import FactConsistencyError
from causa.institutional.contracts.reviewed_analysis import (
    ReviewedContractAnalysisRequest,
    run_reviewed_contract_analysis,
)
from causa.reasoning.counterfactual import CounterfactualBudget
from causa.translation_pipeline import TranslationBundle
from causa.ui.documents import GapClosure, UploadedDocument, apply_closure, document_source
from causa.ui.remarks import OperatorRemark

SESSION_VERSION = "ui-case-session-v0"


class CaseInputs(BaseModel):
    """Входы, из которых собирается окно дела."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    case_id: str
    title_ru: str
    workspace_id: str
    caveat_ru: str = ""
    request: ReviewedContractAnalysisRequest
    sources: list[LegalSource]
    bundle: TranslationBundle | None = None

    @property
    def key(self) -> str:
        return f"{self.workspace_id}/{self.case_id}"


class StepChange(BaseModel):
    """Одно звено линии вывода, ответ на которое изменился."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    question_ru: str
    before: bool | str
    after: bool | str


class ChangeReport(BaseModel):
    """Что изменилось в деле после действия оператора."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = SESSION_VERSION
    verdict_changed: bool = False
    verdict_before_ru: str = ""
    verdict_after_ru: str = ""
    steps: list[StepChange] = Field(default_factory=list)
    blocking_gaps_before: int = 0
    blocking_gaps_after: int = 0
    notes_ru: list[str] = Field(default_factory=list)

    @property
    def anything_changed(self) -> bool:
        return (
            self.verdict_changed
            or bool(self.steps)
            or self.blocking_gaps_before != self.blocking_gaps_after
        )


class GapClosureConflict(RuntimeError):
    """Закрытие пробела противоречит фактам, заявленным в других институтах."""

    def __init__(self, closure: GapClosure, error: FactConsistencyError) -> None:
        self.closure = closure
        self.mismatches = error.mismatches
        super().__init__(
            f"Утверждение по пробелу {closure.gap_id} противоречит "
            f"{len(error.mismatches)} фактам дела."
        )

    def payload(self) -> dict:
        return {
            "gap_id": self.closure.gap_id,
            "document_id": self.closure.document_id,
            "conflicts_ru": [mismatch.line_ru for mismatch in self.mismatches],
            "explanation_ru": (
                "Пересчёт не выполнен, а изменение откачено. Тот же факт описан "
                "в нескольких институтах, и ваше утверждение расходится с тем, "
                "что заявлено там. Система не выбирает версию за юриста: "
                "согласовать эти факты должен человек."
            ),
            "next_step_ru": (
                "Приведите перечисленные факты в согласие с новым утверждением "
                "либо откажитесь от него."
            ),
        }


class CaseSession:
    """Дело вместе с тем, что оператор к нему добавил."""

    def __init__(self, inputs: CaseInputs, *, budget: CounterfactualBudget | None = None) -> None:
        self.inputs = inputs
        self.budget = budget or CounterfactualBudget()
        self.documents: list[UploadedDocument] = []
        self.closures: list[GapClosure] = []
        self.remarks: list[OperatorRemark] = []
        self._request = inputs.request
        # Источники дела растут: приложенный документ обязан попасть в реестр,
        # иначе ссылка на него из утверждения будет ссылкой в пустоту.
        self._sources = list(inputs.sources)

    @property
    def request(self) -> ReviewedContractAnalysisRequest:
        return self._request

    def document(self, document_id: str) -> UploadedDocument:
        for document in self.documents:
            if document.id == document_id:
                return document
        raise KeyError(f"Документ {document_id} к делу {self.inputs.case_id} не приложен.")

    def add_document(self, document: UploadedDocument) -> UploadedDocument:
        if document.case_id != self.inputs.case_id:
            raise ValueError("Документ относится к другому делу.")
        for existing in self.documents:
            if existing.id == document.id:
                # Тот же файл уже приложен: повторная загрузка не создаёт копию.
                return existing
        self.documents.append(document)
        self._sources.append(document_source(document))
        return document

    def close_gap(self, closure: GapClosure):
        """Внести утверждение оператора в факты дела и пересчитать его целиком.

        Если новое утверждение противоречит фактам, заявленным в других
        институтах, слой сверки отвергает анализ — и правильно делает: иначе
        решателю пришлось бы молча выбрать одну из двух версий факта. Тогда
        изменение откатывается, а оператор получает список расхождений.
        Согласовывать их система за него не будет.
        """
        document = self.document(closure.document_id)
        previous = self._request
        self._request = apply_closure(self._request, closure, document)
        try:
            view = self.build_view()
        except FactConsistencyError as error:
            self._request = previous
            raise GapClosureConflict(closure, error) from error
        self.closures.append(closure)
        return view

    def build_view(self):
        """Собрать окно дела по текущим входам."""
        # Импорт здесь: `desktop` собирает окно из сессии, и на уровне модуля
        # это дало бы круговую зависимость.
        from causa.ui.desktop import build_case_view

        result = run_reviewed_contract_analysis(
            self._request,
            self._sources,
            counterfactual_budget=self.budget,
        )
        return build_case_view(
            case_id=self.inputs.case_id,
            title_ru=self.inputs.title_ru,
            workspace_id=self.inputs.workspace_id,
            request=self._request,
            result=result,
            bundle=self.inputs.bundle,
            remarks=self.remarks,
            caveat_ru=self.inputs.caveat_ru,
            documents=self.documents,
            closures=self.closures,
        )


def compare_views(before, after) -> ChangeReport:
    """Сравнить два состояния дела так, как их читает юрист."""
    steps_before = {step.code: step for step in before.reasoning.line}
    steps = [
        StepChange(
            question_ru=step.question_ru,
            before=steps_before[step.code].value,
            after=step.value,
        )
        for step in after.reasoning.line
        if step.code in steps_before and steps_before[step.code].value != step.value
    ]
    verdict_changed = before.verdict.headline_ru != after.verdict.headline_ru

    notes: list[str] = []
    if not verdict_changed and not steps:
        notes.append(
            "Вывод не изменился. Это тоже результат: документ приобщён к делу, "
            "но на формальный итог он не повлиял."
        )
    return ChangeReport(
        verdict_changed=verdict_changed,
        verdict_before_ru=before.verdict.headline_ru,
        verdict_after_ru=after.verdict.headline_ru,
        steps=steps,
        blocking_gaps_before=len([gap for gap in before.gaps.gaps if gap.blocking]),
        blocking_gaps_after=len([gap for gap in after.gaps.gaps if gap.blocking]),
        notes_ru=notes,
    )
