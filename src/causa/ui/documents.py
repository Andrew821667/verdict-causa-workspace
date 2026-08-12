"""Загрузка документов: чем закрывается пробел и что при этом меняется.

## Чего система не делает

Она **не читает документ**. Извлечения фактов из текста в ядре нет, и рисовать
его в интерфейсе нельзя: загруженный файл, из которого система якобы что-то
поняла, — самый дорогой вид обмана в этой предметной области.

## Что происходит на самом деле

Очередь пробелов уже говорит, чем каждый пробел закрывается: «документ о
согласованном сроке», «доказательства причинной связи». Загрузка привязывается
к пробелу:

1. Оператор прикладывает файл к конкретному пробелу.
2. Оператор **сам утверждает**, что этот документ подтверждает факт.
3. Идентификатор документа становится источником соответствующего утверждения
   в проверенных фактах дела — provenance сохраняется.
4. Дело пересчитывается целиком, и разница показывается.

То есть меняет вывод не файл, а утверждение оператора; файл — записанное
основание этого утверждения. Разница существенная, и она видна в данных: в
`source_refs` появляется идентификатор документа, а не текст из него.

## Как факт связан с доказательством

Поля модели обязательства совпадают с предикатами проверенных фактов один в
один — кроме `due_date_missed`, который не утверждается, а **вычисляется** из
дат. Поэтому пробел о сроке закрывается датой, а не галочкой: оператор вводит
дату, которую документ устанавливает.
"""

import hashlib
from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from causa.core.models import LegalSource, SourceType
from causa.institutional.contracts.reviewed_analysis import (
    CaseEvidenceAssertion,
    ContractEvidencePredicate,
    ReviewedContractAnalysisRequest,
)

DOCUMENTS_VERSION = "ui-documents-v0"

#: Максимальный размер файла на стенде. Стенд не хранилище: большие файлы здесь
#: означают, что кто-то принял его за систему ведения дел.
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024

#: Поле модели обязательства → предикат проверенных фактов.
#:
#: Совпадение один в один не случайно: предикаты и есть входы этой модели.
FACT_TO_PREDICATE: dict[str, ContractEvidencePredicate] = {
    "duty_exists": ContractEvidencePredicate.DUTY_EXISTS,
    "valid_exception_applies": ContractEvidencePredicate.VALID_EXCEPTION_APPLIES,
    "performance_completed": ContractEvidencePredicate.PERFORMANCE_COMPLETED,
    "performance_nonconforming": ContractEvidencePredicate.PERFORMANCE_NONCONFORMING,
    "payment_duty_exists": ContractEvidencePredicate.PAYMENT_DUTY_EXISTS,
    "payment_due": ContractEvidencePredicate.PAYMENT_DUE,
    "payment_missed": ContractEvidencePredicate.PAYMENT_MISSED,
    "payment_defense_applies": ContractEvidencePredicate.PAYMENT_DEFENSE_APPLIES,
    "loss_claimed": ContractEvidencePredicate.LOSS_CLAIMED,
    "causation_established": ContractEvidencePredicate.CAUSATION_ESTABLISHED,
    "remedy_requested": ContractEvidencePredicate.REMEDY_REQUESTED,
    "limitation_period_expired": ContractEvidencePredicate.LIMITATION_PERIOD_EXPIRED,
}

#: Факты, которые не утверждаются, а вычисляются, и потому закрываются иначе.
DERIVED_FACTS_RU: dict[str, str] = {
    "due_date_missed": (
        "пропуск срока вычисляется из согласованной даты и даты фактического "
        "исполнения, поэтому закрывается датой из документа, а не утверждением"
    ),
}


class ClosureKind(str, Enum):
    #: Оператор утверждает значение предиката, документ — основание утверждения.
    ASSERTED_FACT = "asserted_fact"
    #: Оператор вводит дату, которую документ устанавливает.
    SUPPLIED_DATE = "supplied_date"


class UploadedDocument(BaseModel):
    """Файл, приложенный к делу. Содержимое здесь не разбирается."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    filename: str
    media_type: str = "application/octet-stream"
    size_bytes: int = Field(ge=0)
    #: Отпечаток содержимого: по нему видно, что приложен именно этот файл.
    sha256: str
    uploaded_by: str
    uploaded_on: date | None = None

    @property
    def label_ru(self) -> str:
        return f"{self.filename} ({self.size_bytes // 1024 or 1} КиБ)"


class DocumentTooLargeError(ValueError):
    """Файл больше того, что стенд готов принять."""


def build_document(
    *,
    case_id: str,
    filename: str,
    content: bytes,
    uploaded_by: str,
    media_type: str = "application/octet-stream",
    uploaded_on: date | None = None,
) -> UploadedDocument:
    """Принять файл, посчитать отпечаток и ничего в нём не разбирать."""
    if len(content) > MAX_DOCUMENT_BYTES:
        raise DocumentTooLargeError(
            f"Файл {filename} больше {MAX_DOCUMENT_BYTES // (1024 * 1024)} МиБ: "
            "стенд предназначен для проверки разбора, а не для хранения дел."
        )
    digest = hashlib.sha256(content).hexdigest()
    return UploadedDocument(
        id=f"doc:{case_id}:{digest[:16]}",
        case_id=case_id,
        filename=filename,
        media_type=media_type,
        size_bytes=len(content),
        sha256=digest,
        uploaded_by=uploaded_by,
        uploaded_on=uploaded_on,
    )


def document_source(document: UploadedDocument) -> LegalSource:
    """Зарегистрировать документ как фактический источник дела.

    Конвейер отвергает ссылку на незарегистрированный источник — и правильно
    делает: утверждение, ссылающееся в пустоту, непроверяемо. Поэтому документ
    попадает в реестр источников с типом «фактический материал».

    Текст источника **не** содержит содержимого файла: система его не читала, и
    подставлять сюда что-либо, кроме честной записи об этом, значит выдавать
    непрочитанное за разобранное.
    """
    return LegalSource(
        id=document.id,
        title=f"Документ оператора: {document.filename}",
        source_type=SourceType.FACT,
        text=(
            "Файл, приложенный оператором к делу. Содержимое системой не "
            f"разбиралось. Отпечаток SHA-256: {document.sha256}."
        ),
        metadata={
            "filename": document.filename,
            "media_type": document.media_type,
            "size_bytes": document.size_bytes,
            "uploaded_by": document.uploaded_by,
        },
    )


class GapClosure(BaseModel):
    """Чем оператор закрывает пробел и что именно он этим утверждает."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    gap_id: str
    document_id: str
    kind: ClosureKind
    #: Для `ASSERTED_FACT`: поле модели и утверждаемое значение.
    fact_updates: dict[str, bool] = Field(default_factory=dict)
    #: Для `SUPPLIED_DATE`: какую дату устанавливает документ.
    agreed_due_date: date | None = None
    actual_performance_date: date | None = None
    #: Что именно утверждает оператор — своими словами, в деле остаётся это.
    statement_ru: str = ""

    @property
    def summary_ru(self) -> str:
        if self.kind is ClosureKind.SUPPLIED_DATE:
            dates = []
            if self.agreed_due_date:
                dates.append(f"согласованный срок — {self.agreed_due_date:%d.%m.%Y}")
            if self.actual_performance_date:
                dates.append(f"исполнение — {self.actual_performance_date:%d.%m.%Y}")
            return "; ".join(dates) or "дата не указана"
        return ", ".join(
            f"{field} = {'да' if value else 'нет'}" for field, value in self.fact_updates.items()
        )


class UnknownFactError(KeyError):
    """Поле, которого нет ни среди предикатов, ни среди вычисляемых фактов."""


def apply_closure(
    request: ReviewedContractAnalysisRequest,
    closure: GapClosure,
    document: UploadedDocument,
) -> ReviewedContractAnalysisRequest:
    """Внести утверждение оператора в проверенные факты дела.

    Идентификатор документа добавляется в `source_refs` изменённого утверждения:
    видно, на чём именно держится новое значение.
    """
    if document.id != closure.document_id:
        raise ValueError("Закрытие пробела ссылается на другой документ.")

    if closure.kind is ClosureKind.SUPPLIED_DATE:
        temporal = request.temporal_evidence
        updates: dict[str, object] = {
            "source_refs": tuple({*temporal.source_refs, document.id}),
        }
        if closure.agreed_due_date is not None:
            updates["agreed_due_date"] = closure.agreed_due_date
        if closure.actual_performance_date is not None:
            updates["actual_performance_date"] = closure.actual_performance_date
        if len(updates) == 1:
            raise ValueError("Закрытие пробела датой не содержит ни одной даты.")
        return request.model_copy(update={"temporal_evidence": temporal.model_copy(update=updates)})

    if not closure.fact_updates:
        raise ValueError("Закрытие пробела утверждением не содержит ни одного факта.")

    unknown = [
        field
        for field in closure.fact_updates
        if field not in FACT_TO_PREDICATE and field not in DERIVED_FACTS_RU
    ]
    if unknown:
        raise UnknownFactError("Неизвестные поля фактов: " + ", ".join(sorted(unknown)))
    derived = [field for field in closure.fact_updates if field in DERIVED_FACTS_RU]
    if derived:
        raise ValueError(
            "Эти факты не утверждаются, а вычисляются: "
            + "; ".join(f"{field} — {DERIVED_FACTS_RU[field]}" for field in sorted(derived))
        )

    wanted = {FACT_TO_PREDICATE[field]: value for field, value in closure.fact_updates.items()}
    assertions = tuple(
        assertion
        if assertion.predicate not in wanted
        else assertion.model_copy(
            update={
                "value": wanted[assertion.predicate],
                "source_refs": tuple({*assertion.source_refs, document.id}),
            }
        )
        for assertion in request.case_evidence.assertions
    )
    missing = wanted.keys() - {
        assertion.predicate for assertion in request.case_evidence.assertions
    }
    if missing:
        assertions = assertions + tuple(
            CaseEvidenceAssertion(
                id=f"assertion:{request.case_id}:{predicate.value}",
                predicate=predicate,
                value=wanted[predicate],
                source_refs=(document.id,),
            )
            for predicate in sorted(missing, key=lambda item: item.value)
        )
    return request.model_copy(
        update={
            "case_evidence": request.case_evidence.model_copy(update={"assertions": assertions})
        }
    )
