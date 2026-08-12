"""Замечания оператора: два разных действия и путь к обучению системы.

## Почему это два действия, а не одно

Оператор, глядя на разбор, может сказать две совершенно разные вещи:

1. «В этом деле факт другой» — уточнение по делу. Оно меняет разбор **этого**
   дела и больше ничего.
2. «Система рассуждает неправильно» — сигнал резонанса. Он не меняет ни дело,
   ни систему: он порождает **кандидата** на изменение, который обязан пройти
   governance.

Смешать их — значит либо потерять экспертное знание в примечании к делу, либо
менять логику системы по одному замечанию одного юриста. Раздел 10.11 концепции
называет второе тихой эволюцией и запрещает его.

## Что здесь происходит с сигналом

Замечание типа «сигнал» превращается в `CandidateHypothesis` со статусом
`proposed` и в тип кандидата, определяющий, какие стадии governance обязательны.
Тип выводится из вида замечания:

| Вид замечания | Тип кандидата | Что это значит |
|---|---|---|
| не учтена норма или практика | `gap_heuristic` | пробел в знании |
| вывод неверен | `conflict_resolution_pattern` | спор о разрешении конфликта норм |
| квалификация неверна | `conflict_resolution_pattern` | то же на входе разбора |
| изложение непонятно | `translation_pattern` | вопрос слоя перевода, не права |

## Чего этот модуль не делает

Он **не** утверждает кандидатов. Ни один путь отсюда не создаёт кандидата со
статусом, отличным от `proposed`, — это проверяется тестом. Утверждение
происходит в `causa.governance`, с обязательными стадиями из профиля типа.
"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from causa.core.models import CandidateHypothesis
from causa.governance.candidate_types import CandidateType
from causa.governance.profiles import GovernanceProfile, get_governance_profile
from causa.localization.ru import GOVERNANCE_STAGE_LABELS_RU, label_ru

REMARKS_VERSION = "ui-remarks-v0"


class RemarkKind(str, Enum):
    #: Уточнение факта по делу — меняет разбор этого дела.
    CLARIFICATION = "clarification"
    #: Вывод неверен.
    DISAGREEMENT = "disagreement"
    #: Квалификация определена неверно.
    QUALIFICATION = "qualification"
    #: Не учтена норма, разъяснение или практика.
    MISSING_RULE = "missing_rule"
    #: Изложение непонятно или вводит в заблуждение.
    WORDING = "wording"


REMARK_KIND_LABELS_RU = {
    RemarkKind.CLARIFICATION: "уточнение по делу",
    RemarkKind.DISAGREEMENT: "не согласен с выводом",
    RemarkKind.QUALIFICATION: "квалификация определена неверно",
    RemarkKind.MISSING_RULE: "не учтена норма или практика",
    RemarkKind.WORDING: "изложение непонятно",
}

#: Вид замечания → тип кандидата, если замечание отправлено как сигнал.
#:
#: Уточнения по делу здесь нет намеренно: оно к системе не относится.
SIGNAL_CANDIDATE_TYPE: dict[RemarkKind, CandidateType] = {
    RemarkKind.DISAGREEMENT: CandidateType.CONFLICT_RESOLUTION_PATTERN,
    RemarkKind.QUALIFICATION: CandidateType.CONFLICT_RESOLUTION_PATTERN,
    RemarkKind.MISSING_RULE: CandidateType.GAP_HEURISTIC,
    RemarkKind.WORDING: CandidateType.TRANSLATION_PATTERN,
}


class OperatorRemark(BaseModel):
    """Что оператор написал и куда он это адресовал."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    operator_id: str
    kind: RemarkKind
    text_ru: str
    #: К чему относится замечание: звено линии, кластер, пробел или регистр.
    target: str = ""
    #: Истина — оператор нажал «как сигнал системе», а не «внести в дело».
    as_learning_signal: bool = False
    source_refs: list[str] = Field(default_factory=list)
    created_on: date | None = None


class RemarkOutcome(BaseModel):
    """Судьба замечания: что изменилось в деле и что ушло в governance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    remark_id: str
    kind_ru: str
    #: Что происходит с этим делом.
    case_effect_ru: str
    #: Что происходит с системой. Пусто, если замечание осталось в деле.
    system_effect_ru: str = ""
    candidate: CandidateHypothesis | None = None
    candidate_type: CandidateType | None = None
    governance_profile: GovernanceProfile | None = None
    required_stages_ru: list[str] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


class RemarkLedger(BaseModel):
    """Все замечания по делу и то, во что они превратились."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = REMARKS_VERSION
    case_id: str
    outcomes: list[RemarkOutcome] = Field(default_factory=list)

    @property
    def proposed_candidates(self) -> list[CandidateHypothesis]:
        return [o.candidate for o in self.outcomes if o.candidate is not None]


def _case_effect_ru(remark: OperatorRemark) -> str:
    if remark.kind is RemarkKind.CLARIFICATION:
        return (
            "Уточнение приобщено к делу как факт, заявленный оператором. Оно "
            "не считается доказанным, пока не пройдёт проверку, и не меняет "
            "выводы модели задним числом."
        )
    where = {
        RemarkKind.DISAGREEMENT: "рядом с выводом",
        RemarkKind.QUALIFICATION: "рядом с квалификацией",
        RemarkKind.MISSING_RULE: "рядом с линией вывода",
        RemarkKind.WORDING: "рядом с текстом изложения",
    }[remark.kind]
    if remark.as_learning_signal:
        return (
            f"В деле остаётся отметка оператора {where}. Сам вывод не "
            "переписывается: его меняет пересчёт по другим фактам, а не замечание."
        )
    return (
        f"Замечание приобщено к делу и видно {where}. Как сигнал системе оно не "
        "отправлено — это отдельное действие оператора."
    )


def apply_remark(remark: OperatorRemark) -> RemarkOutcome:
    """Разобрать одно замечание: что с делом, что с системой."""
    kind_ru = REMARK_KIND_LABELS_RU[remark.kind]
    notes: list[str] = []

    if not remark.as_learning_signal or remark.kind is RemarkKind.CLARIFICATION:
        if remark.kind is RemarkKind.CLARIFICATION and remark.as_learning_signal:
            notes.append(
                "Уточнение по делу не может быть сигналом системе: оно говорит о "
                "фактах этого дела, а не о том, как система рассуждает."
            )
        return RemarkOutcome(
            remark_id=remark.id,
            kind_ru=kind_ru,
            case_effect_ru=_case_effect_ru(remark),
            notes_ru=notes,
        )

    candidate_type = SIGNAL_CANDIDATE_TYPE[remark.kind]
    profile = get_governance_profile(candidate_type)
    candidate = CandidateHypothesis(
        id=f"candidate:{remark.case_id}:{remark.id}",
        statement=remark.text_ru,
        supporting_sources=list(remark.source_refs),
        risk_level="medium",
        status="proposed",
    )
    return RemarkOutcome(
        remark_id=remark.id,
        kind_ru=kind_ru,
        case_effect_ru=_case_effect_ru(remark),
        system_effect_ru=(
            "Создан кандидат на изменение системы со статусом «предложен». "
            "До прохождения governance он не влияет ни на одно дело — ни на это, "
            "ни на чужие."
        ),
        candidate=candidate,
        candidate_type=candidate_type,
        governance_profile=profile,
        required_stages_ru=[
            label_ru(stage, GOVERNANCE_STAGE_LABELS_RU) for stage in profile.required_stages
        ],
        notes_ru=notes,
    )


def build_remark_ledger(case_id: str, remarks: list[OperatorRemark]) -> RemarkLedger:
    """Собрать журнал замечаний по делу."""
    for remark in remarks:
        if remark.case_id != case_id:
            raise ValueError(
                f"Замечание {remark.id} относится к делу {remark.case_id}, "
                f"а журнал собирается по делу {case_id}."
            )
    return RemarkLedger(case_id=case_id, outcomes=[apply_remark(r) for r in remarks])
