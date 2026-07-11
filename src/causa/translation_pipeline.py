from enum import Enum

from pydantic import BaseModel, Field, model_validator

from causa.governance.engine import GovernanceRecord
from causa.institutional.contracts.reviewed_analysis import (
    ReviewedContractAnalysisRequest,
    ReviewedContractAnalysisResult,
)
from causa.management.policy_registry import PolicySnapshot
from causa.translation import (
    TranslationArtifact,
    TranslationAssertion,
    TranslationAssertionCode,
    TranslationLevel,
)
from causa.translation_templates import (
    TranslationTemplateSet,
    build_russian_translation_template_set,
)


TRANSLATION_PIPELINE_VERSION = "translation-pipeline-ru-v0"
TRANSLATION_DISCLAIMER_RU = (
    "Синтетический результат. Не является юридической консультацией и требует проверки юристом."
)


class TranslationCheckSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class TranslationCheckIssue(BaseModel):
    code: str
    severity: TranslationCheckSeverity
    level: TranslationLevel | None = None
    message_ru: str


class TranslationFaithfulnessReport(BaseModel):
    id: str
    trace_id: str
    passed: bool
    checked_levels: list[TranslationLevel] = Field(default_factory=list)
    issues: list[TranslationCheckIssue] = Field(default_factory=list)
    summary_ru: list[str] = Field(default_factory=list)


class TranslationUsabilityReport(BaseModel):
    id: str
    trace_id: str
    structural_checks_passed: bool
    requires_human_pilot: bool = True
    checked_levels: list[TranslationLevel] = Field(default_factory=list)
    issues: list[TranslationCheckIssue] = Field(default_factory=list)
    scope_ru: str
    summary_ru: list[str] = Field(default_factory=list)


class ReasoningPathComparison(BaseModel):
    id: str
    active_path_ru: list[str] = Field(default_factory=list)
    alternative_path_ru: list[str] = Field(default_factory=list)
    material_differences_ru: list[str] = Field(default_factory=list)
    selected_path: str
    selection_reason_ru: str


class TranslationBundle(BaseModel):
    id: str
    trace_id: str
    locale: str = "ru-RU"
    pipeline_version: str = TRANSLATION_PIPELINE_VERSION
    template_set_id: str
    template_version: str
    template_content_hash: str
    policy_snapshot_id: str
    policy_content_hash: str
    artifacts: list[TranslationArtifact] = Field(default_factory=list)
    path_comparisons: list[ReasoningPathComparison] = Field(default_factory=list)
    faithfulness_report: TranslationFaithfulnessReport
    usability_report: TranslationUsabilityReport
    ready_for_human_review: bool

    @model_validator(mode="after")
    def validate_bundle_integrity(self) -> "TranslationBundle":
        levels = [artifact.level for artifact in self.artifacts]
        if set(levels) != set(TranslationLevel) or len(levels) != len(set(levels)):
            raise ValueError("Bundle должен содержать ровно по одному артефакту каждого уровня.")
        for artifact in self.artifacts:
            if artifact.trace_id != self.trace_id:
                raise ValueError("Артефакт Translation Layer относится к другой трассировке.")
            if (
                artifact.template_version != self.template_version
                or artifact.template_content_hash != self.template_content_hash
            ):
                raise ValueError("Координаты шаблонов в bundle не согласованы.")
            if (
                artifact.policy_snapshot_id != self.policy_snapshot_id
                or artifact.policy_content_hash != self.policy_content_hash
            ):
                raise ValueError("Координаты политики в bundle не согласованы.")
            if not artifact.faithfulness_checked or not artifact.usability_checked:
                raise ValueError("Артефакт в bundle должен пройти обе автоматические проверки.")
            if artifact.faithfulness_passed != self.faithfulness_report.passed:
                raise ValueError("Флаг верности артефакта не согласован с отчетом.")
            if artifact.usability_passed != self.usability_report.structural_checks_passed:
                raise ValueError("Флаг usability артефакта не согласован с отчетом.")
        if (
            self.faithfulness_report.trace_id != self.trace_id
            or self.usability_report.trace_id != self.trace_id
        ):
            raise ValueError("Отчеты Translation Layer относятся к другой трассировке.")
        expected_ready = (
            self.faithfulness_report.passed
            and self.usability_report.structural_checks_passed
        )
        if self.ready_for_human_review != expected_ready:
            raise ValueError("Готовность bundle не согласована с результатами проверок.")
        return self

    def artifact_for(self, level: TranslationLevel) -> TranslationArtifact:
        return next(artifact for artifact in self.artifacts if artifact.level == level)


class TranslationBundleArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str = TRANSLATION_DISCLAIMER_RU
    bundle: TranslationBundle


def _yes_no(value: bool) -> str:
    return "Да" if value else "Нет"


def _provenance_refs(
    result: ReviewedContractAnalysisResult,
    *fact_names: str,
) -> list[str]:
    references = {
        source_ref
        for item in result.evidence_mapping.provenance
        if item.fact_name in fact_names
        for source_ref in item.source_refs
    }
    return sorted(references)


def build_translation_assertions(
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
) -> list[TranslationAssertion]:
    evaluation = result.constraint_evaluation
    authority = result.authority_evaluation
    authority_refs = list(request.authority_input.candidate_source_ids)
    counterfactual_report = result.counterfactual_sensitivity
    critical_scenario = (
        next(
            scenario
            for scenario in counterfactual_report.scenarios
            if scenario.id == counterfactual_report.critical_scenario_ids[0]
        )
        if counterfactual_report.critical_scenario_ids
        else None
    )
    assertions = [
        TranslationAssertion(
            code=TranslationAssertionCode.SOURCE_APPLICABLE,
            value=result.source_applicability.applicable,
            text_ru=(
                "Источник проверенной нормы применим на дату оценки."
                if result.source_applicability.applicable
                else "Источник проверенной нормы не применим на дату оценки."
            ),
            source_refs=[request.reviewed_norm.source_id],
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.DUE_DATE_MISSED,
            value=result.temporal_evaluation.due_date_missed,
            text_ru=result.temporal_evaluation.reasons_ru[0],
            source_refs=_provenance_refs(result, "due_date_missed"),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.BREACH_ISSUE,
            value=evaluation.breach_issue,
            text_ru=(
                "Формальная модель выявила вопрос о нарушении обязательства."
                if evaluation.breach_issue
                else "Формальная модель не выявила нарушения обязательства."
            ),
            source_refs=_provenance_refs(
                result,
                "duty_exists",
                "due_date_missed",
                "valid_exception_applies",
                "performance_completed",
                "performance_nonconforming",
                "payment_duty_exists",
                "payment_due",
                "payment_missed",
                "payment_defense_applies",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.LATE_PERFORMANCE_ISSUE,
            value=evaluation.late_performance_issue,
            text_ru=(
                "Установлены формальные признаки просрочки исполнения."
                if evaluation.late_performance_issue
                else "Формальные признаки просрочки исполнения не установлены."
            ),
            source_refs=_provenance_refs(
                result,
                "duty_exists",
                "due_date_missed",
                "valid_exception_applies",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.DEFECT_ISSUE,
            value=evaluation.defect_issue,
            text_ru=(
                "Установлены формальные признаки ненадлежащего исполнения."
                if evaluation.defect_issue
                else "Формальные признаки ненадлежащего исполнения не установлены."
            ),
            source_refs=_provenance_refs(
                result,
                "duty_exists",
                "performance_completed",
                "performance_nonconforming",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.PAYMENT_DEFAULT_ISSUE,
            value=evaluation.payment_default_issue,
            text_ru=(
                "Установлены формальные признаки просрочки платежа."
                if evaluation.payment_default_issue
                else "Формальные признаки просрочки платежа не установлены."
            ),
            source_refs=_provenance_refs(
                result,
                "payment_duty_exists",
                "payment_due",
                "payment_missed",
                "payment_defense_applies",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.DAMAGES_REMEDY_AVAILABLE,
            value=evaluation.damages_remedy_available,
            text_ru=(
                "Формальные предпосылки требования убытков установлены."
                if evaluation.damages_remedy_available
                else "Текущий набор фактов не подтверждает все формальные предпосылки требования убытков."
            ),
            source_refs=_provenance_refs(
                result,
                "loss_claimed",
                "causation_established",
                "remedy_requested",
                "limitation_period_expired",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.CAUSATION_EVIDENCE_GAP,
            value=evaluation.causation_evidence_gap,
            text_ru=(
                "Выявлен пробел в доказательствах причинной связи."
                if evaluation.causation_evidence_gap
                else "Формальный пробел причинной связи для заявленного требования не выявлен."
            ),
            source_refs=_provenance_refs(
                result,
                "loss_claimed",
                "causation_established",
                "remedy_requested",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.LIMITATION_BAR,
            value=evaluation.limitation_bar,
            text_ru=(
                "Установлен формальный барьер исковой давности."
                if evaluation.limitation_bar
                else "Формальный барьер исковой давности не установлен."
            ),
            source_refs=_provenance_refs(
                result,
                "remedy_requested",
                "limitation_period_expired",
            ),
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.AUTHORITY_WINNER,
            value=authority.selected_source_id or "human_resolution_required",
            text_ru=(
                f"По модели юридической силы выбран источник {authority.selected_source_id}."
                if authority.selected_source_id
                else "Модель юридической силы не выбрала единственный источник."
            ),
            source_refs=authority_refs,
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.HUMAN_RESOLUTION_REQUIRED,
            value=result.requires_human_resolution,
            text_ru=(
                "Для разрешения конкуренции источников требуется решение эксперта."
                if result.requires_human_resolution
                else "Конкуренция источников разрешена текущей синтетической моделью."
            ),
            source_refs=authority_refs,
        ),
        TranslationAssertion(
            code=TranslationAssertionCode.COUNTERFACTUAL_SENSITIVITY,
            value=(
                critical_scenario.operator_code.value
                if critical_scenario
                else "no_material_sensitivity"
            ),
            text_ru=(
                "Минимальная гипотеза чувствительности «"
                f"{critical_scenario.title_ru}» изменяет формальный результат."
                if critical_scenario
                else "В пределах бюджета материальная контрфактическая чувствительность не выявлена."
            ),
            source_refs=[],
        ),
    ]
    return assertions


def build_reasoning_path_comparison(
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
) -> ReasoningPathComparison:
    return ReasoningPathComparison(
        id=f"path-comparison:{request.case_id}:active-vs-shortcut",
        active_path_ru=[
            "Проверить временную применимость источников.",
            "Разрешить юридическую силу источников-кандидатов.",
            "Преобразовать только проверенные факты в формальные предикаты.",
            "Проверить обязанность, срок и применимое исключение в constraint set.",
        ],
        alternative_path_ru=[
            "Считать любую просрочку нарушением без проверки источника и исключений.",
        ],
        material_differences_ru=[
            "Альтернативный путь не сохраняет provenance фактов.",
            "Альтернативный путь не проверяет применимость и юридическую силу источника.",
            "Альтернативный путь способен необоснованно исключить основание освобождения.",
        ],
        selected_path="active_reviewed_path",
        selection_reason_ru=(
            "Выбран воспроизводимый путь с проверенными входами; shortcut отклонен "
            f"независимо от совпадения итогового breach_issue={evaluation_value(result)}."
        ),
    )


def evaluation_value(result: ReviewedContractAnalysisResult) -> str:
    return _yes_no(result.constraint_evaluation.breach_issue)


def _assertion_map(assertions: list[TranslationAssertion]) -> dict[str, TranslationAssertion]:
    return {assertion.code.value: assertion for assertion in assertions}


def _render_context(
    trace_id: str,
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
    governance: GovernanceRecord,
    policy_snapshot: PolicySnapshot,
    assertions: list[TranslationAssertion],
    comparison: ReasoningPathComparison,
    template_set: TranslationTemplateSet,
) -> dict[str, str]:
    by_code = _assertion_map(assertions)
    evaluation = result.constraint_evaluation
    conclusion_ru = by_code[TranslationAssertionCode.BREACH_ISSUE.value].text_ru
    if evaluation.late_performance_issue:
        conclusion_ru += " Основной выявленный паттерн — просрочка поставки."
    key_basis_ru = " ".join(
        [
            by_code[TranslationAssertionCode.DUE_DATE_MISSED.value].text_ru,
            by_code[TranslationAssertionCode.AUTHORITY_WINNER.value].text_ru,
        ]
    )
    risk_and_next_step_ru = (
        "Содержательная квалификация, расчет последствий и выбор способа защиты "
        "остаются за юристом; необходимо проверить первичные документы и актуальные источники."
    )
    facts_ru = "\n".join(
        [
            f"- Согласованный срок: {result.temporal_facts.agreed_due_date}.",
            f"- Фактическое исполнение: {result.temporal_facts.actual_performance_date}.",
            f"- Дата оценки: {result.temporal_facts.evaluation_date}.",
            f"- Срок пропущен: {_yes_no(result.temporal_evaluation.due_date_missed)}.",
            f"- Применимое исключение: {_yes_no(result.evidence_mapping.facts.valid_exception_applies)}.",
        ]
    )
    rule_and_authority_ru = "\n".join(
        [
            f"- Норма: {request.reviewed_norm.id}; действие: {result.formal_translation.obligation_rule.action}.",
            f"- Источник нормы: {request.reviewed_norm.source_id}.",
            *[f"- {reason}" for reason in result.authority_evaluation.reasons_ru],
        ]
    )
    formal_result_ru = "\n".join(
        f"- {assertion.text_ru}" for assertion in assertions[:9]
    )
    limitations_ru = "\n".join(f"- {warning}" for warning in result.warnings_ru)
    coordinates_ru = "\n".join(
        [
            f"- Trace: {trace_id}.",
            f"- Дело: {request.case_id}.",
            f"- Analysis pipeline: {result.pipeline_version}.",
            f"- Policy snapshot: {policy_snapshot.id}.",
            f"- Policy hash: {policy_snapshot.content_hash}.",
            f"- Translation template: {template_set.version}.",
            f"- Translation template hash: {template_set.content_hash}.",
        ]
    )
    provenance_ru = "\n".join(
        (
            f"- {item.fact_name}: assertion={item.assertion_id}; "
            f"sources={', '.join(item.source_refs) or 'нет'}; "
            f"formal_atoms={', '.join(item.formal_atom_refs) or 'нет'}."
        )
        for item in result.evidence_mapping.provenance
    )
    formal_rule_ru = "\n".join(
        [
            f"- Formal rule: {result.formal_translation.obligation_rule.id}.",
            f"- Constraint set: {result.constraint_set.id}.",
            *[f"- {expression}." for expression in result.constraint_set.expressions],
        ]
    )
    authority_trace_ru = "\n".join(
        [
            f"- Кандидаты: {', '.join(result.authority_evaluation.candidate_source_ids)}.",
            f"- Исключены: {', '.join(result.authority_evaluation.excluded_source_ids) or 'нет'}.",
            *[f"- {reason}" for reason in result.authority_evaluation.reasons_ru],
        ]
    )
    all_assertions_ru = "\n".join(
        (
            f"- {assertion.code.value}={assertion.value}: {assertion.text_ru} "
            f"[sources: {', '.join(assertion.source_refs) or 'нет'}]"
        )
        for assertion in assertions
    )
    governance_ru = "\n".join(
        (
            f"- {decision.from_stage_label_ru} → {decision.to_stage_label_ru}: "
            f"{' '.join(decision.reasons_ru)} [policy={decision.policy_version}; "
            f"hash={decision.policy_content_hash}]"
        )
        for decision in governance.decisions
    )
    path_comparison_ru = "\n".join(
        [
            *[f"- Активный путь: {step}" for step in comparison.active_path_ru],
            *[f"- Отклоненный путь: {step}" for step in comparison.alternative_path_ru],
            *[f"- Различие: {item}" for item in comparison.material_differences_ru],
            f"- Причина выбора: {comparison.selection_reason_ru}",
        ]
    )
    counterfactual_report = result.counterfactual_sensitivity
    critical_scenarios = [
        scenario
        for scenario_id in counterfactual_report.critical_scenario_ids
        for scenario in counterfactual_report.scenarios
        if scenario.id == scenario_id
    ]
    counterfactual_professional_ru = "\n".join(
        (
            f"- {scenario.title_ru}: меняются выводы — "
            + ", ".join(delta.field_label_ru for delta in scenario.outcome_deltas)
            + "."
        )
        for scenario in critical_scenarios[:3]
    ) or "- В пределах установленного бюджета материальные изменения не выявлены."
    counterfactual_forensic_ru = "\n".join(
        [
            f"- Engine: {counterfactual_report.engine_version}.",
            f"- Operator library: {counterfactual_report.operator_library_version}.",
            f"- Operator library hash: {counterfactual_report.operator_library_hash}.",
            f"- Baseline fact hash: {counterfactual_report.baseline_fact_hash}.",
            f"- Budget: scenarios={counterfactual_report.budget.max_scenarios}; "
            f"changed_facts={counterfactual_report.budget.max_changed_facts_per_scenario}.",
            *[
                (
                    f"- {scenario.operator_code.value}: факты ["
                    + "; ".join(
                        f"{delta.field_name}={delta.before}->{delta.after}"
                        for delta in scenario.fact_deltas
                    )
                    + "]; выводы ["
                    + "; ".join(
                        f"{delta.field_name}={delta.before}->{delta.after}"
                        for delta in scenario.outcome_deltas
                    )
                    + f"]; hypothetical_hash={scenario.hypothetical_fact_hash}."
                )
                for scenario in counterfactual_report.scenarios
            ],
            f"- {counterfactual_report.disclaimer_ru}",
        ]
    )
    return {
        "conclusion_ru": conclusion_ru,
        "key_basis_ru": key_basis_ru,
        "risk_and_next_step_ru": risk_and_next_step_ru,
        "facts_ru": facts_ru,
        "rule_and_authority_ru": rule_and_authority_ru,
        "formal_result_ru": formal_result_ru,
        "limitations_ru": limitations_ru,
        "coordinates_ru": coordinates_ru,
        "provenance_ru": provenance_ru,
        "formal_rule_ru": formal_rule_ru,
        "authority_trace_ru": authority_trace_ru,
        "all_assertions_ru": all_assertions_ru,
        "governance_ru": governance_ru,
        "path_comparison_ru": path_comparison_ru,
        "counterfactual_professional_ru": counterfactual_professional_ru,
        "counterfactual_forensic_ru": counterfactual_forensic_ru,
        "disclaimer_ru": TRANSLATION_DISCLAIMER_RU,
    }


def _render_artifact(
    level: TranslationLevel,
    *,
    trace_id: str,
    template_set: TranslationTemplateSet,
    policy_snapshot: PolicySnapshot,
    assertions: list[TranslationAssertion],
    source_refs: list[str],
    context: dict[str, str],
) -> TranslationArtifact:
    template = template_set.template_for(level)
    return TranslationArtifact(
        id=f"translation:{trace_id}:{level.value}",
        trace_id=trace_id,
        level=level,
        template_version=template_set.version,
        template_content_hash=template_set.content_hash,
        policy_snapshot_id=policy_snapshot.id,
        policy_content_hash=policy_snapshot.content_hash,
        text=template.template_text_ru.format(**context),
        assertions=assertions,
        source_refs=source_refs,
    )


def evaluate_translation_faithfulness(
    *,
    trace_id: str,
    artifacts: list[TranslationArtifact],
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
    governance: GovernanceRecord,
    policy_snapshot: PolicySnapshot,
    template_set: TranslationTemplateSet,
) -> TranslationFaithfulnessReport:
    expected_assertions = build_translation_assertions(request, result)
    comparison = build_reasoning_path_comparison(request, result)
    context = _render_context(
        trace_id,
        request,
        result,
        governance,
        policy_snapshot,
        expected_assertions,
        comparison,
        template_set,
    )
    issues: list[TranslationCheckIssue] = []
    artifacts_by_level = {artifact.level: artifact for artifact in artifacts}
    if len(artifacts_by_level) != len(artifacts):
        issues.append(
            TranslationCheckIssue(
                code="duplicate_level",
                severity=TranslationCheckSeverity.ERROR,
                message_ru="Набор содержит повторяющийся уровень представления.",
            )
        )
    for level in TranslationLevel:
        artifact = artifacts_by_level.get(level)
        if artifact is None:
            issues.append(
                TranslationCheckIssue(
                    code="missing_level",
                    severity=TranslationCheckSeverity.ERROR,
                    level=level,
                    message_ru="Отсутствует обязательный уровень представления.",
                )
            )
            continue
        expected = _render_artifact(
            level,
            trace_id=trace_id,
            template_set=template_set,
            policy_snapshot=policy_snapshot,
            assertions=expected_assertions,
            source_refs=result.source_ids,
            context=context,
        )
        checks = [
            (artifact.trace_id == trace_id, "trace_mismatch", "Неверная ссылка на trace."),
            (
                artifact.template_version == template_set.version
                and artifact.template_content_hash == template_set.content_hash,
                "template_mismatch",
                "Координаты шаблона не совпадают с проверяемым набором.",
            ),
            (
                artifact.policy_snapshot_id == policy_snapshot.id
                and artifact.policy_content_hash == policy_snapshot.content_hash,
                "policy_mismatch",
                "Координаты политики не совпадают с decision trace.",
            ),
            (
                artifact.assertions == expected_assertions,
                "assertion_distortion",
                "Структурированные юридические утверждения искажены.",
            ),
            (
                artifact.source_refs == result.source_ids,
                "source_distortion",
                "Набор ссылок на источники изменен.",
            ),
            (
                artifact.text == expected.text,
                "text_distortion",
                "Текст не воспроизводится из проверенного trace и шаблона.",
            ),
            (
                TRANSLATION_DISCLAIMER_RU in artifact.text,
                "missing_disclaimer",
                "Отсутствует обязательное предупреждение.",
            ),
        ]
        for passed, code, message_ru in checks:
            if not passed:
                issues.append(
                    TranslationCheckIssue(
                        code=code,
                        severity=TranslationCheckSeverity.ERROR,
                        level=level,
                        message_ru=message_ru,
                    )
                )
    passed = not any(issue.severity == TranslationCheckSeverity.ERROR for issue in issues)
    return TranslationFaithfulnessReport(
        id=f"translation-faithfulness:{trace_id}",
        trace_id=trace_id,
        passed=passed,
        checked_levels=list(TranslationLevel),
        issues=issues,
        summary_ru=[
            (
                "Все три уровня точно воспроизводятся из проверенного trace и шаблонов."
                if passed
                else "Обнаружено искажение между trace и юридическим объяснением."
            )
        ],
    )


def _cyrillic_ratio(text: str) -> float:
    letters = [character for character in text.lower() if character.isalpha()]
    if not letters:
        return 0.0
    cyrillic = sum("а" <= character <= "я" or character == "ё" for character in letters)
    return cyrillic / len(letters)


def evaluate_translation_usability(
    *,
    trace_id: str,
    artifacts: list[TranslationArtifact],
    template_set: TranslationTemplateSet,
) -> TranslationUsabilityReport:
    issues: list[TranslationCheckIssue] = []
    artifacts_by_level = {artifact.level: artifact for artifact in artifacts}
    for level in TranslationLevel:
        artifact = artifacts_by_level.get(level)
        template = template_set.template_for(level)
        if artifact is None:
            issues.append(
                TranslationCheckIssue(
                    code="missing_level",
                    severity=TranslationCheckSeverity.ERROR,
                    level=level,
                    message_ru="Отсутствует обязательный уровень представления.",
                )
            )
            continue
        if not template.min_characters <= len(artifact.text) <= template.max_characters:
            issues.append(
                TranslationCheckIssue(
                    code="length_out_of_bounds",
                    severity=TranslationCheckSeverity.ERROR,
                    level=level,
                    message_ru="Длина текста не соответствует уровню представления.",
                )
            )
        for heading in template.required_headings_ru:
            if heading not in artifact.text:
                issues.append(
                    TranslationCheckIssue(
                        code="missing_heading",
                        severity=TranslationCheckSeverity.ERROR,
                        level=level,
                        message_ru=f"Отсутствует раздел «{heading}».",
                    )
                )
        minimum_cyrillic_ratio = 0.30 if level == TranslationLevel.FORENSIC else 0.55
        if _cyrillic_ratio(artifact.text) < minimum_cyrillic_ratio:
            issues.append(
                TranslationCheckIssue(
                    code="insufficient_russian_text",
                    severity=TranslationCheckSeverity.ERROR,
                    level=level,
                    message_ru="В тексте недостаточно русского человекочитаемого содержания.",
                )
            )
        if max(len(line) for line in artifact.text.splitlines()) > 240:
            issues.append(
                TranslationCheckIssue(
                    code="line_too_long",
                    severity=TranslationCheckSeverity.WARNING,
                    level=level,
                    message_ru="Отдельная строка слишком длинна для удобного аудита.",
                )
            )
        if level != TranslationLevel.FORENSIC and any(
            marker in artifact.text for marker in ("=True", "=False", "sha256:")
        ):
            issues.append(
                TranslationCheckIssue(
                    code="machine_detail_leak",
                    severity=TranslationCheckSeverity.ERROR,
                    level=level,
                    message_ru="Машинные детали попали в человекочитаемый уровень.",
                )
            )
    if set(artifacts_by_level) == set(TranslationLevel):
        lengths = [
            len(artifacts_by_level[level].text)
            for level in (
                TranslationLevel.EXECUTIVE,
                TranslationLevel.PROFESSIONAL,
                TranslationLevel.FORENSIC,
            )
        ]
        if not lengths[0] < lengths[1] < lengths[2]:
            issues.append(
                TranslationCheckIssue(
                    code="level_depth_order",
                    severity=TranslationCheckSeverity.ERROR,
                    message_ru="Глубина представления не возрастает от краткого к forensic.",
                )
            )
    passed = not any(issue.severity == TranslationCheckSeverity.ERROR for issue in issues)
    return TranslationUsabilityReport(
        id=f"translation-usability:{trace_id}",
        trace_id=trace_id,
        structural_checks_passed=passed,
        checked_levels=list(TranslationLevel),
        issues=issues,
        scope_ru=(
            "Автоматическая проверка оценивает структуру, русский язык, глубину уровней "
            "и отсутствие машинных деталей. Она не доказывает понимание текста юристом."
        ),
        summary_ru=[
            (
                "Структурные usability-проверки пройдены; требуется пилотная оценка юристом."
                if passed
                else "Структурные usability-проверки выявили блокирующие проблемы."
            )
        ],
    )


def build_translation_bundle(
    *,
    trace_id: str,
    request: ReviewedContractAnalysisRequest,
    result: ReviewedContractAnalysisResult,
    governance: GovernanceRecord,
    policy_snapshot: PolicySnapshot,
    template_set: TranslationTemplateSet | None = None,
) -> TranslationBundle:
    selected_template_set = template_set or build_russian_translation_template_set()
    if policy_snapshot.payload.translation_template_version != selected_template_set.version:
        raise ValueError("Policy snapshot требует другую версию шаблонов Translation Layer.")
    if (
        policy_snapshot.payload.translation_template_hash
        != selected_template_set.content_hash
    ):
        raise ValueError("Policy snapshot содержит другой hash шаблонов Translation Layer.")
    assertions = build_translation_assertions(request, result)
    comparison = build_reasoning_path_comparison(request, result)
    context = _render_context(
        trace_id,
        request,
        result,
        governance,
        policy_snapshot,
        assertions,
        comparison,
        selected_template_set,
    )
    artifacts = [
        _render_artifact(
            level,
            trace_id=trace_id,
            template_set=selected_template_set,
            policy_snapshot=policy_snapshot,
            assertions=assertions,
            source_refs=result.source_ids,
            context=context,
        )
        for level in TranslationLevel
    ]
    faithfulness = evaluate_translation_faithfulness(
        trace_id=trace_id,
        artifacts=artifacts,
        request=request,
        result=result,
        governance=governance,
        policy_snapshot=policy_snapshot,
        template_set=selected_template_set,
    )
    usability = evaluate_translation_usability(
        trace_id=trace_id,
        artifacts=artifacts,
        template_set=selected_template_set,
    )
    checked_artifacts = [
        artifact.model_copy(
            update={
                "faithfulness_checked": True,
                "faithfulness_passed": faithfulness.passed,
                "usability_checked": True,
                "usability_passed": usability.structural_checks_passed,
            }
        )
        for artifact in artifacts
    ]
    return TranslationBundle(
        id=f"translation-bundle:{trace_id}",
        trace_id=trace_id,
        template_set_id=selected_template_set.id,
        template_version=selected_template_set.version,
        template_content_hash=selected_template_set.content_hash,
        policy_snapshot_id=policy_snapshot.id,
        policy_content_hash=policy_snapshot.content_hash,
        artifacts=checked_artifacts,
        path_comparisons=[comparison],
        faithfulness_report=faithfulness,
        usability_report=usability,
        ready_for_human_review=(
            faithfulness.passed and usability.structural_checks_passed
        ),
    )
