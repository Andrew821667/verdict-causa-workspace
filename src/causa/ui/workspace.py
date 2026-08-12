"""Организация, рабочие пространства и дела — то, что вокруг окна разбора.

## Четыре уровня

`Organisation`
    Кто отвечает за результат: юридическая фирма, департамент, практика. Здесь
    живут роли и то, какие режимы глубины и риск-тиры вообще разрешены.

`Workspace`
    Изолированный контур: клиент, проект, направление. Раздел 11 концепции
    требует изоляции клиентских материалов — здесь это не настройка, а
    инвариант: дело принадлежит ровно одному пространству, и материалы одного
    пространства не видны из другого.

`CaseCard`
    Дело: материалы, квалификация, разбор, замечания. Открывается в основном
    окне.

Узлы разбора — уровень внутри дела; они живут в `causa.ui.case_map`.

## Что здесь проверяется, а не описывается

Изоляция — инвариант модели: `Desk.case` отказывается отдать дело, если
запрошенное пространство ему не принадлежит, а не полагается на то, что
интерфейс не покажет чужую кнопку.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causa.localization.ru import RISK_TIER_LABELS_RU, SLA_MODE_LABELS_RU, label_ru

WORKSPACE_VERSION = "ui-workspace-v0"


class OperatorRole(str, Enum):
    #: Ведёт дела, задаёт уточнения, отправляет сигналы.
    LAWYER = "lawyer"
    #: Проверяет выводы и снимает флаги «требует человека».
    REVIEWER = "reviewer"
    #: Утверждает кандидатов в governance.
    KNOWLEDGE_OWNER = "knowledge_owner"
    #: Управляет пространствами и доступом.
    ADMIN = "admin"


ROLE_LABELS_RU = {
    OperatorRole.LAWYER: "юрист",
    OperatorRole.REVIEWER: "проверяющий",
    OperatorRole.KNOWLEDGE_OWNER: "владелец знания",
    OperatorRole.ADMIN: "администратор",
}

#: Что роль имеет право делать. Список короткий намеренно: право утверждать
#: кандидата отделено от права вести дело, иначе governance превращается в
#: формальность, которую проходит сам автор замечания.
ROLE_RIGHTS_RU: dict[OperatorRole, tuple[str, ...]] = {
    OperatorRole.LAWYER: (
        "загружать материалы и вести дело",
        "вносить уточнения по делу",
        "отправлять сигналы обучения",
    ),
    OperatorRole.REVIEWER: (
        "снимать флаг «требует решения человека» с обоснованием",
        "оспаривать квалификацию",
    ),
    OperatorRole.KNOWLEDGE_OWNER: (
        "проводить кандидата по стадиям governance",
        "утверждать и отзывать изменения знания",
    ),
    OperatorRole.ADMIN: (
        "создавать пространства и назначать роли",
        "задавать режим глубины и риск-тир",
    ),
}


class Operator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    display_name: str
    role: OperatorRole

    @property
    def role_ru(self) -> str:
        return ROLE_LABELS_RU[self.role]

    @property
    def rights_ru(self) -> list[str]:
        return list(ROLE_RIGHTS_RU[self.role])


class CaseCard(BaseModel):
    """Карточка дела в списке пространства."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    title_ru: str
    workspace_id: str
    #: Кластер, определённый системой. Пусто, пока разбор не выполнен.
    cluster_ru: str = ""
    #: Сколько пробелов сейчас блокируют окончательный вывод.
    blocking_gaps: int = 0
    #: Институты, чей вывод по этому делу не доходит до итога без обоснования.
    open_debt_ru: list[str] = Field(default_factory=list)
    needs_human: bool = False


class Workspace(BaseModel):
    """Изолированный контур: клиент, проект, направление."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title_ru: str
    organisation_id: str
    #: Режим глубины и риск-тир задаются пространством, а не делом: их выбирает
    #: тот, кто отвечает за результат, а не тот, кто торопится.
    sla_mode: str = "standard"
    risk_tier: str = "t2_internal_memo"
    cases: list[CaseCard] = Field(default_factory=list)

    @model_validator(mode="after")
    def cases_belong_here(self) -> "Workspace":
        alien = [case.case_id for case in self.cases if case.workspace_id != self.id]
        if alien:
            raise ValueError(
                "Дела принадлежат другому пространству и не могут быть показаны "
                f"в этом: {', '.join(alien)}."
            )
        return self

    @property
    def sla_mode_ru(self) -> str:
        return label_ru(self.sla_mode, SLA_MODE_LABELS_RU)

    @property
    def risk_tier_ru(self) -> str:
        return label_ru(self.risk_tier, RISK_TIER_LABELS_RU)


class Organisation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    title_ru: str
    operators: list[Operator] = Field(default_factory=list)
    workspaces: list[Workspace] = Field(default_factory=list)

    @model_validator(mode="after")
    def workspaces_belong_here(self) -> "Organisation":
        alien = [ws.id for ws in self.workspaces if ws.organisation_id != self.id]
        if alien:
            raise ValueError(f"Пространства принадлежат другой организации: {', '.join(alien)}.")
        return self


class Desk(BaseModel):
    """Рабочий стол оператора: организация, его роль и доступные пространства."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = WORKSPACE_VERSION
    organisation: Organisation
    operator: Operator
    #: Пространства, к которым у оператора есть доступ.
    workspace_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def access_is_within_organisation(self) -> "Desk":
        known = {ws.id for ws in self.organisation.workspaces}
        unknown = [ws_id for ws_id in self.workspace_ids if ws_id not in known]
        if unknown:
            raise ValueError(
                f"Доступ выдан к пространствам, которых нет в организации: {', '.join(unknown)}."
            )
        return self

    def workspace(self, workspace_id: str) -> Workspace:
        if workspace_id not in self.workspace_ids:
            raise PermissionError(
                f"Пространство {workspace_id} недоступно оператору "
                f"{self.operator.id}: изоляция материалов — инвариант, а не настройка."
            )
        return next(ws for ws in self.organisation.workspaces if ws.id == workspace_id)

    def case(self, workspace_id: str, case_id: str) -> CaseCard:
        workspace = self.workspace(workspace_id)
        for case in workspace.cases:
            if case.case_id == case_id:
                return case
        raise KeyError(
            f"Дело {case_id} не найдено в пространстве {workspace_id}. Поиск по "
            "другим пространствам не выполняется намеренно."
        )
