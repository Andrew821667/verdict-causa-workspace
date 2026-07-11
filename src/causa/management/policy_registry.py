import hashlib
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causa.localization.ru import (
    LOCALE_RU,
    RISK_TIER_LABELS_RU,
    SLA_MODE_LABELS_RU,
    label_ru,
)
from causa.management.policy_matrix import PolicyMatrixEntry, ReviewRequirement
from causa.management.risk_tiers import RiskTier
from causa.management.sla_modes import SLAMode


POLICY_REGISTRY_VERSION = "policy-registry-v0"


class PolicyChangeImpact(str, Enum):
    TIGHTENING = "tightening"
    RELAXATION = "relaxation"
    BEHAVIORAL = "behavioral"


class PolicyDiffDirection(str, Enum):
    TIGHTENED = "tightened"
    RELAXED = "relaxed"
    MIXED = "mixed"
    BEHAVIORAL = "behavioral"
    UNCHANGED = "unchanged"


class PolicyEventType(str, Enum):
    REGISTERED = "registered"
    ACTIVATED = "activated"
    ROLLED_BACK = "rolled_back"


POLICY_EVENT_LABELS_RU = {
    PolicyEventType.REGISTERED: "Снимок политики зарегистрирован",
    PolicyEventType.ACTIVATED: "Снимок политики активирован",
    PolicyEventType.ROLLED_BACK: "Выполнен откат политики",
}

POLICY_FIELD_LABELS_RU = {
    "mode": "Режим глубины",
    "risk_tier": "Уровень риска",
    "max_agent_passes": "Максимальное число агентных проходов",
    "max_requests": "Максимальное число модельных запросов",
    "max_tokens": "Максимальный токенный бюджет",
    "retrieval_depth": "Глубина извлечения источников",
    "confidence_threshold": "Минимальный порог уверенности",
    "allow_candidate_principles": "Допуск принципов-кандидатов",
    "require_formal_check": "Обязательная формальная проверка",
    "require_red_team": "Обязательная проверка Red Team",
    "human_review": "Обязательная экспертная проверка",
    "cross_review": "Обязательная перекрестная проверка",
    "replayable_trace": "Обязательная воспроизводимая трассировка",
    "complete_provenance": "Обязательное полное происхождение данных",
    "escalate_on_low_confidence": "Эскалация при низкой уверенности",
    "allow_counterfactual": "Допуск ограниченного контрфактического анализа",
    "counterfactual_max_scenarios": "Максимальное число контрфактических сценариев",
    "counterfactual_max_changed_facts": "Максимум изменений фактов в сценарии",
    "translation_template_version": "Версия шаблона юридического объяснения",
    "translation_template_hash": "Hash шаблонов юридического объяснения",
    "model_profile": "Профиль модели",
}


class BehaviorPolicyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: SLAMode
    risk_tier: RiskTier
    max_agent_passes: int = Field(ge=1)
    max_requests: int = Field(ge=1)
    max_tokens: int | None = Field(default=None, ge=1)
    retrieval_depth: int = Field(ge=1)
    confidence_threshold: float = Field(ge=0, le=1)
    allow_candidate_principles: bool
    require_formal_check: bool
    require_red_team: bool
    human_review: bool
    cross_review: bool
    replayable_trace: bool
    complete_provenance: bool
    escalate_on_low_confidence: bool
    allow_counterfactual: bool
    counterfactual_max_scenarios: int = Field(ge=1, le=32)
    counterfactual_max_changed_facts: int = Field(ge=1, le=8)
    translation_template_version: str
    translation_template_hash: str
    model_profile: str

    @model_validator(mode="after")
    def enforce_safety_invariants(self) -> "BehaviorPolicyPayload":
        high_risk = self.risk_tier in {
            RiskTier.T4_PROCEDURAL_DRAFT,
            RiskTier.T5_HIGH_STAKES_RECOMMENDATION,
            RiskTier.T6_READY_TO_FILE_DOCUMENT,
        }
        highest_risk = self.risk_tier in {
            RiskTier.T5_HIGH_STAKES_RECOMMENDATION,
            RiskTier.T6_READY_TO_FILE_DOCUMENT,
        }
        if high_risk and not self.human_review:
            raise ValueError("Политика уровней T4-T6 требует экспертной проверки.")
        if high_risk and not self.require_red_team:
            raise ValueError("Политика уровней T4-T6 требует проверки Red Team.")
        if high_risk and not self.complete_provenance:
            raise ValueError("Политика уровней T4-T6 требует полного происхождения данных.")
        if high_risk and self.allow_candidate_principles and self.mode not in {
            SLAMode.DEEP,
            SLAMode.RESEARCH,
        }:
            raise ValueError(
                "Принципы-кандидаты для T4-T6 допустимы только в углубленном "
                "или исследовательском режиме."
            )
        if highest_risk and not self.cross_review:
            raise ValueError("Политика уровней T5-T6 требует перекрестной проверки.")
        if self.cross_review and not self.human_review:
            raise ValueError("Перекрестная проверка невозможна без экспертной проверки.")
        if not self.replayable_trace:
            raise ValueError("Правовая политика должна требовать воспроизводимую трассировку.")
        if self.mode in {SLAMode.DEEP, SLAMode.RESEARCH} and not self.require_red_team:
            raise ValueError("Углубленный и исследовательский режимы требуют Red Team.")
        return self


def compute_policy_content_hash(payload: BehaviorPolicyPayload) -> str:
    canonical = json.dumps(
        payload.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def policy_matrix_entry_from_payload(
    payload: BehaviorPolicyPayload,
) -> PolicyMatrixEntry:
    return PolicyMatrixEntry(
        mode=payload.mode,
        risk_tier=payload.risk_tier,
        max_agent_passes=payload.max_agent_passes,
        allow_candidate_principles=payload.allow_candidate_principles,
        require_red_team=payload.require_red_team,
        review=ReviewRequirement(
            human_review=payload.human_review,
            cross_review=payload.cross_review,
            replayable_trace=payload.replayable_trace,
            complete_provenance=payload.complete_provenance,
        ),
    )


class PolicySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    family_id: str
    version: int = Field(ge=1)
    locale: str = LOCALE_RU
    parent_snapshot_id: str | None = None
    payload: BehaviorPolicyPayload
    content_hash: str
    created_at: datetime
    created_by: str
    reviewer_ids: tuple[str, ...] = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    change_summary_ru: str

    @model_validator(mode="after")
    def validate_coordinates_and_hash(self) -> "PolicySnapshot":
        expected_id = f"policy-snapshot:{self.family_id}@{self.version}"
        if self.id != expected_id:
            raise ValueError("Идентификатор снимка политики не соответствует семье и версии.")
        if self.version == 1 and self.parent_snapshot_id is not None:
            raise ValueError("Первая версия политики не может иметь родительский снимок.")
        if self.version > 1 and self.parent_snapshot_id is None:
            raise ValueError("Новая версия политики должна ссылаться на родительский снимок.")
        if self.content_hash != compute_policy_content_hash(self.payload):
            raise ValueError("Hash содержимого политики не соответствует payload.")
        return self


class PolicyFieldChange(BaseModel):
    field_name: str
    field_label_ru: str
    before: Any
    before_label_ru: str
    after: Any
    after_label_ru: str
    impact: PolicyChangeImpact
    impact_label_ru: str


class PolicySemanticDiff(BaseModel):
    from_snapshot_id: str
    to_snapshot_id: str
    direction: PolicyDiffDirection
    direction_label_ru: str
    changes: list[PolicyFieldChange] = Field(default_factory=list)
    summary_ru: list[str] = Field(default_factory=list)


class PolicyRegistryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    sequence: int = Field(ge=1)
    event_type: PolicyEventType
    event_type_label_ru: str
    family_id: str
    snapshot_id: str
    previous_snapshot_id: str | None = None
    actor_id: str
    occurred_at: datetime
    reasons_ru: tuple[str, ...] = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    resulting_revision: int = Field(ge=1)


class PolicyRegistryState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = "management-policy-registry"
    locale: str = LOCALE_RU
    registry_version: str = POLICY_REGISTRY_VERSION
    revision: int = Field(default=0, ge=0)
    snapshots: list[PolicySnapshot] = Field(default_factory=list)
    active_snapshot_ids: dict[str, str] = Field(default_factory=dict)
    events: list[PolicyRegistryEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_registry_integrity(self) -> "PolicyRegistryState":
        snapshot_ids = [snapshot.id for snapshot in self.snapshots]
        if len(snapshot_ids) != len(set(snapshot_ids)):
            raise ValueError("Реестр содержит повторяющиеся снимки политики.")
        snapshots_by_id = {snapshot.id: snapshot for snapshot in self.snapshots}
        snapshots_by_family: dict[str, list[PolicySnapshot]] = {}
        for snapshot in self.snapshots:
            snapshots_by_family.setdefault(snapshot.family_id, []).append(snapshot)
        for family_snapshots in snapshots_by_family.values():
            ordered = sorted(family_snapshots, key=lambda snapshot: snapshot.version)
            if len({snapshot.content_hash for snapshot in ordered}) != len(ordered):
                raise ValueError("Семья политик содержит повторяющееся содержимое.")
            for expected_version, snapshot in enumerate(ordered, start=1):
                if snapshot.version != expected_version:
                    raise ValueError("Версии семьи политик должны быть последовательными.")
                expected_parent = ordered[expected_version - 2].id if expected_version > 1 else None
                if snapshot.parent_snapshot_id != expected_parent:
                    raise ValueError("Нарушена родительская цепочка снимков политики.")
                if expected_version > 1:
                    previous = ordered[expected_version - 2]
                    if snapshot.content_hash == previous.content_hash:
                        raise ValueError("Последовательные версии политики не различаются.")
        for family_id, snapshot_id in self.active_snapshot_ids.items():
            snapshot = snapshots_by_id.get(snapshot_id)
            if snapshot is None or snapshot.family_id != family_id:
                raise ValueError("Активный снимок отсутствует или относится к другой семье.")
        if self.revision != len(self.events):
            raise ValueError("Ревизия реестра не соответствует числу событий.")
        previous_time: datetime | None = None
        registered_snapshot_ids: set[str] = set()
        replayed_active_snapshot_ids: dict[str, str] = {}
        for sequence, event in enumerate(self.events, start=1):
            if event.sequence != sequence or event.resulting_revision != sequence:
                raise ValueError("Нарушена последовательность событий реестра политик.")
            if event.snapshot_id not in snapshots_by_id:
                raise ValueError("Событие ссылается на отсутствующий снимок политики.")
            if event.event_type_label_ru != POLICY_EVENT_LABELS_RU[event.event_type]:
                raise ValueError("Русская метка события политики не соответствует типу.")
            if previous_time is not None and event.occurred_at < previous_time:
                raise ValueError("Нарушена хронология событий реестра политик.")
            snapshot = snapshots_by_id[event.snapshot_id]
            if snapshot.family_id != event.family_id:
                raise ValueError("Событие и снимок относятся к разным семьям политик.")
            current_active_id = replayed_active_snapshot_ids.get(event.family_id)
            if event.event_type == PolicyEventType.REGISTERED:
                if event.snapshot_id in registered_snapshot_ids:
                    raise ValueError("Снимок политики зарегистрирован повторно.")
                if event.occurred_at < snapshot.created_at:
                    raise ValueError("Снимок политики зарегистрирован до его создания.")
                registered_snapshot_ids.add(event.snapshot_id)
            elif event.event_type == PolicyEventType.ACTIVATED:
                if event.snapshot_id not in registered_snapshot_ids:
                    raise ValueError("Политика активирована до регистрации.")
                if event.previous_snapshot_id != current_active_id:
                    raise ValueError("Событие активации содержит неверный предыдущий снимок.")
                if current_active_id is not None:
                    current = snapshots_by_id[current_active_id]
                    if snapshot.version <= current.version:
                        raise ValueError("Обычная активация не может возвращать старую версию.")
                replayed_active_snapshot_ids[event.family_id] = event.snapshot_id
            elif event.event_type == PolicyEventType.ROLLED_BACK:
                if event.snapshot_id not in registered_snapshot_ids:
                    raise ValueError("Цель отката не зарегистрирована.")
                if event.previous_snapshot_id != current_active_id or current_active_id is None:
                    raise ValueError("Событие отката содержит неверный активный снимок.")
                current = snapshots_by_id[current_active_id]
                if snapshot.version >= current.version:
                    raise ValueError("Откат должен вести к более ранней версии политики.")
                replayed_active_snapshot_ids[event.family_id] = event.snapshot_id
            previous_time = event.occurred_at
        if registered_snapshot_ids != set(snapshot_ids):
            raise ValueError("В реестре присутствуют незарегистрированные снимки политики.")
        if replayed_active_snapshot_ids != self.active_snapshot_ids:
            raise ValueError("Активное состояние не воспроизводится из журнала событий.")
        return self


class PolicyRegistryArtifact(BaseModel):
    id: str
    locale: str = LOCALE_RU
    title_ru: str
    summary_ru: list[str] = Field(default_factory=list)
    registry: PolicyRegistryState
    diffs: list[PolicySemanticDiff] = Field(default_factory=list)


def create_policy_snapshot(
    *,
    family_id: str,
    version: int,
    payload: BehaviorPolicyPayload,
    created_at: datetime,
    created_by: str,
    reviewer_ids: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    change_summary_ru: str,
    parent_snapshot_id: str | None = None,
) -> PolicySnapshot:
    return PolicySnapshot(
        id=f"policy-snapshot:{family_id}@{version}",
        family_id=family_id,
        version=version,
        parent_snapshot_id=parent_snapshot_id,
        payload=payload,
        content_hash=compute_policy_content_hash(payload),
        created_at=created_at,
        created_by=created_by,
        reviewer_ids=reviewer_ids,
        evidence_refs=evidence_refs,
        change_summary_ru=change_summary_ru,
    )


def create_policy_registry() -> PolicyRegistryState:
    return PolicyRegistryState()


def _require_revision(registry: PolicyRegistryState, expected_revision: int) -> None:
    if registry.revision != expected_revision:
        raise ValueError(
            f"Ревизия реестра изменилась: ожидалась {expected_revision}, "
            f"текущая — {registry.revision}."
        )


def _append_event(
    registry: PolicyRegistryState,
    *,
    event_type: PolicyEventType,
    family_id: str,
    snapshot_id: str,
    previous_snapshot_id: str | None,
    actor_id: str,
    occurred_at: datetime,
    reasons_ru: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    snapshots: list[PolicySnapshot] | None = None,
    active_snapshot_ids: dict[str, str] | None = None,
) -> PolicyRegistryState:
    if registry.events and occurred_at < registry.events[-1].occurred_at:
        raise ValueError("Новое событие политики не может предшествовать журналу.")
    revision = registry.revision + 1
    event = PolicyRegistryEvent(
        id=f"policy-event:{revision}",
        sequence=revision,
        event_type=event_type,
        event_type_label_ru=POLICY_EVENT_LABELS_RU[event_type],
        family_id=family_id,
        snapshot_id=snapshot_id,
        previous_snapshot_id=previous_snapshot_id,
        actor_id=actor_id,
        occurred_at=occurred_at,
        reasons_ru=reasons_ru,
        evidence_refs=evidence_refs,
        resulting_revision=revision,
    )
    return registry.model_copy(
        update={
            "revision": revision,
            "snapshots": snapshots if snapshots is not None else registry.snapshots,
            "active_snapshot_ids": (
                active_snapshot_ids
                if active_snapshot_ids is not None
                else registry.active_snapshot_ids
            ),
            "events": [*registry.events, event],
        }
    )


def register_policy_snapshot(
    registry: PolicyRegistryState,
    snapshot: PolicySnapshot,
    *,
    expected_revision: int,
    actor_id: str,
    occurred_at: datetime,
    reasons_ru: tuple[str, ...],
    evidence_refs: tuple[str, ...],
) -> PolicyRegistryState:
    _require_revision(registry, expected_revision)
    family_snapshots = [
        candidate
        for candidate in registry.snapshots
        if candidate.family_id == snapshot.family_id
    ]
    if any(candidate.id == snapshot.id for candidate in registry.snapshots):
        raise ValueError("Снимок политики уже зарегистрирован.")
    if family_snapshots:
        latest = max(family_snapshots, key=lambda candidate: candidate.version)
        if snapshot.version != latest.version + 1:
            raise ValueError("Версия политики должна последовательно продолжать семью.")
        if snapshot.parent_snapshot_id != latest.id:
            raise ValueError("Родитель должен быть последним снимком семьи политик.")
        if any(
            snapshot.content_hash == candidate.content_hash
            for candidate in family_snapshots
        ):
            raise ValueError("Новая версия политики повторяет существующее содержимое.")
    elif snapshot.version != 1:
        raise ValueError("Первая зарегистрированная версия семьи должна иметь номер 1.")

    return _append_event(
        registry,
        event_type=PolicyEventType.REGISTERED,
        family_id=snapshot.family_id,
        snapshot_id=snapshot.id,
        previous_snapshot_id=snapshot.parent_snapshot_id,
        actor_id=actor_id,
        occurred_at=occurred_at,
        reasons_ru=reasons_ru,
        evidence_refs=evidence_refs,
        snapshots=[*registry.snapshots, snapshot],
    )


def _snapshot_by_id(registry: PolicyRegistryState, snapshot_id: str) -> PolicySnapshot:
    try:
        return next(snapshot for snapshot in registry.snapshots if snapshot.id == snapshot_id)
    except StopIteration as error:
        raise ValueError(f"Снимок политики {snapshot_id} не зарегистрирован.") from error


def activate_policy_snapshot(
    registry: PolicyRegistryState,
    snapshot_id: str,
    *,
    expected_revision: int,
    expected_active_snapshot_id: str | None,
    actor_id: str,
    occurred_at: datetime,
    reasons_ru: tuple[str, ...],
    evidence_refs: tuple[str, ...],
) -> PolicyRegistryState:
    _require_revision(registry, expected_revision)
    snapshot = _snapshot_by_id(registry, snapshot_id)
    current_active_id = registry.active_snapshot_ids.get(snapshot.family_id)
    if current_active_id != expected_active_snapshot_id:
        raise ValueError("Активный снимок изменился с момента подготовки решения.")
    if current_active_id == snapshot.id:
        raise ValueError("Снимок политики уже активен.")
    if current_active_id is not None:
        current = _snapshot_by_id(registry, current_active_id)
        if snapshot.version <= current.version:
            raise ValueError("Для возврата к прежней версии используйте явный откат.")
    active_snapshot_ids = {**registry.active_snapshot_ids, snapshot.family_id: snapshot.id}
    return _append_event(
        registry,
        event_type=PolicyEventType.ACTIVATED,
        family_id=snapshot.family_id,
        snapshot_id=snapshot.id,
        previous_snapshot_id=current_active_id,
        actor_id=actor_id,
        occurred_at=occurred_at,
        reasons_ru=reasons_ru,
        evidence_refs=evidence_refs,
        active_snapshot_ids=active_snapshot_ids,
    )


def rollback_policy_snapshot(
    registry: PolicyRegistryState,
    *,
    family_id: str,
    target_snapshot_id: str,
    expected_current_snapshot_id: str,
    expected_revision: int,
    actor_id: str,
    occurred_at: datetime,
    reasons_ru: tuple[str, ...],
    evidence_refs: tuple[str, ...],
) -> PolicyRegistryState:
    _require_revision(registry, expected_revision)
    current_snapshot_id = registry.active_snapshot_ids.get(family_id)
    if current_snapshot_id != expected_current_snapshot_id:
        raise ValueError("Активная политика изменилась с момента подготовки отката.")
    current = _snapshot_by_id(registry, current_snapshot_id)
    target = _snapshot_by_id(registry, target_snapshot_id)
    if target.family_id != family_id or current.family_id != family_id:
        raise ValueError("Откат возможен только внутри одной семьи политик.")
    if target.version >= current.version:
        raise ValueError("Цель отката должна быть более ранней версией политики.")
    active_snapshot_ids = {**registry.active_snapshot_ids, family_id: target.id}
    return _append_event(
        registry,
        event_type=PolicyEventType.ROLLED_BACK,
        family_id=family_id,
        snapshot_id=target.id,
        previous_snapshot_id=current.id,
        actor_id=actor_id,
        occurred_at=occurred_at,
        reasons_ru=reasons_ru,
        evidence_refs=evidence_refs,
        active_snapshot_ids=active_snapshot_ids,
    )


def active_policy_snapshot(
    registry: PolicyRegistryState,
    family_id: str,
) -> PolicySnapshot:
    try:
        snapshot_id = registry.active_snapshot_ids[family_id]
    except KeyError as error:
        raise ValueError(f"Для семьи {family_id} отсутствует активная политика.") from error
    return _snapshot_by_id(registry, snapshot_id)


def _boolean_safety_impact(field_name: str, before: bool, after: bool) -> PolicyChangeImpact:
    if field_name in {"allow_candidate_principles", "allow_counterfactual"}:
        return PolicyChangeImpact.TIGHTENING if before and not after else PolicyChangeImpact.RELAXATION
    return PolicyChangeImpact.TIGHTENING if not before and after else PolicyChangeImpact.RELAXATION


def _change_impact(field_name: str, before: Any, after: Any) -> PolicyChangeImpact:
    safety_booleans = {
        "allow_candidate_principles",
        "require_formal_check",
        "require_red_team",
        "human_review",
        "cross_review",
        "complete_provenance",
        "escalate_on_low_confidence",
        "allow_counterfactual",
    }
    if field_name in safety_booleans:
        return _boolean_safety_impact(field_name, bool(before), bool(after))
    if field_name == "confidence_threshold":
        return PolicyChangeImpact.TIGHTENING if after > before else PolicyChangeImpact.RELAXATION
    return PolicyChangeImpact.BEHAVIORAL


def _value_label_ru(field_name: str, value: Any) -> str:
    if field_name == "mode":
        return label_ru(str(value), SLA_MODE_LABELS_RU)
    if field_name == "risk_tier":
        return label_ru(str(value), RISK_TIER_LABELS_RU)
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if value is None:
        return "Не ограничено"
    return str(value)


def compare_policy_snapshots(
    before: PolicySnapshot,
    after: PolicySnapshot,
) -> PolicySemanticDiff:
    if before.family_id != after.family_id:
        raise ValueError("Сравнивать можно только снимки одной семьи политик.")
    before_payload = before.payload.model_dump(mode="json")
    after_payload = after.payload.model_dump(mode="json")
    changes: list[PolicyFieldChange] = []
    impact_labels = {
        PolicyChangeImpact.TIGHTENING: "Усиление контроля",
        PolicyChangeImpact.RELAXATION: "Ослабление контроля",
        PolicyChangeImpact.BEHAVIORAL: "Изменение поведения или бюджета",
    }
    for field_name in before_payload:
        before_value = before_payload[field_name]
        after_value = after_payload[field_name]
        if before_value == after_value:
            continue
        impact = _change_impact(field_name, before_value, after_value)
        changes.append(
            PolicyFieldChange(
                field_name=field_name,
                field_label_ru=POLICY_FIELD_LABELS_RU[field_name],
                before=before_value,
                before_label_ru=_value_label_ru(field_name, before_value),
                after=after_value,
                after_label_ru=_value_label_ru(field_name, after_value),
                impact=impact,
                impact_label_ru=impact_labels[impact],
            )
        )

    impacts = {change.impact for change in changes}
    if not changes:
        direction = PolicyDiffDirection.UNCHANGED
    elif PolicyChangeImpact.TIGHTENING in impacts and PolicyChangeImpact.RELAXATION in impacts:
        direction = PolicyDiffDirection.MIXED
    elif PolicyChangeImpact.TIGHTENING in impacts:
        direction = PolicyDiffDirection.TIGHTENED
    elif PolicyChangeImpact.RELAXATION in impacts:
        direction = PolicyDiffDirection.RELAXED
    else:
        direction = PolicyDiffDirection.BEHAVIORAL
    direction_labels = {
        PolicyDiffDirection.TIGHTENED: "Контроль усилен",
        PolicyDiffDirection.RELAXED: "Контроль ослаблен",
        PolicyDiffDirection.MIXED: "Смешанное изменение контроля",
        PolicyDiffDirection.BEHAVIORAL: "Изменено поведение или бюджет",
        PolicyDiffDirection.UNCHANGED: "Содержательных изменений нет",
    }
    return PolicySemanticDiff(
        from_snapshot_id=before.id,
        to_snapshot_id=after.id,
        direction=direction,
        direction_label_ru=direction_labels[direction],
        changes=changes,
        summary_ru=[
            f"Изменено полей: {len(changes)}.",
            f"Общая оценка: {direction_labels[direction]}.",
        ],
    )


class JSONPolicyRegistryStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> PolicyRegistryState:
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        return PolicyRegistryState.model_validate_json(self.path.read_text(encoding="utf-8"))

    def save(
        self,
        registry: PolicyRegistryState,
        *,
        expected_persisted_revision: int | None,
    ) -> None:
        if self.path.exists():
            persisted = self.load()
            if persisted.revision != expected_persisted_revision:
                raise ValueError("Сохраненная ревизия политики изменилась.")
        elif expected_persisted_revision is not None:
            raise ValueError("Хранилище политики еще не создано.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary_path.write_text(
            json.dumps(registry.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(self.path)
