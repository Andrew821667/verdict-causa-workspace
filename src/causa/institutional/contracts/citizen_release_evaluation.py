"""Бенчмарк и red-team для модели освобождения гражданина от обязательств.

Red-team здесь нагружен сильнее обычного, и причина в устройстве статьи. Она
даёт два разных ответа на двух уровнях — недопустимость освобождения вовсе
(пункт 4) и сохранение силы отдельного требования (пункты 5 и 6), — и обе
ошибки смешения дороги. Из сохранения силы одного требования нельзя выводить,
что гражданин не освобождён ни от чего; из состоявшегося освобождения нельзя
выводить, что погашено каждое требование.

Третья ловушка — оговорка «умышленно или по грубой неосторожности». Пункт 6
относит её к трём категориям из пяти, и распространение её на остальные две
освободило бы гражданина от субсидиарной ответственности и от последствий
недействительности сделки при недоказанной форме вины.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.citizen_release import (
    CITIZEN_RELEASE_LEGAL_SOURCE_REFS,
    CitizenReleaseConstraintSet,
    CitizenReleaseEvaluation,
    CitizenReleaseEvidenceMappingResult,
    CitizenReleaseFactSet,
    build_citizen_release_constraint_set,
    evaluate_citizen_release_constraints,
)


class CitizenReleaseEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: CitizenReleaseFactSet
    expected_outcomes: dict[str, bool]


class CitizenReleaseEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CitizenReleaseBenchmarkReport(BaseModel):
    id: str = "citizen-release-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[CitizenReleaseEvaluationResult] = Field(default_factory=list)


class CitizenReleaseRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: CitizenReleaseFactSet
    forbidden_outcomes: dict[str, bool]


class CitizenReleaseRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class CitizenReleaseRedTeamReport(BaseModel):
    id: str = "citizen-release-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[CitizenReleaseRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> CitizenReleaseFactSet:
    """Факты об освобождении гражданина от обязательств.

    По умолчанию всё ложно: гражданин банкротом не признан, определения о
    завершении реализации имущества нет, требование не описано.
    """
    values = {field_name: False for field_name in CitizenReleaseFactSet.model_fields}
    values.update(updates)
    return CitizenReleaseFactSet(**values)


def _completed(**updates: bool) -> CitizenReleaseFactSet:
    """Расчёты завершены: вопрос об освобождении возник (пункты 2 и 3)."""
    return _facts(
        citizen_declared_bankrupt=True,
        property_realisation_completed_by_court_ruling=True,
        **updates,
    )


SYNTHETIC_CITIZEN_RELEASE_BENCHMARKS = (
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-release-after-completion",
        title_ru="После завершения расчётов гражданин освобождается (пункт 3)",
        facts=_completed(),
        expected_outcomes={
            "citizen_released_from_obligations": True,
            "claim_discharged": True,
            "discharge_exception_applies_to_this_claim": False,
            "requires_human_citizen_release_assessment": False,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-no-release-before-the-ruling",
        title_ru="До определения о завершении реализации вопрос не возникает (пункт 2)",
        facts=_facts(citizen_declared_bankrupt=True),
        expected_outcomes={
            "citizen_released_from_obligations": False,
            "claim_discharged": False,
            "requires_human_citizen_release_assessment": False,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-barred-by-bankruptcy-offence",
        title_ru="Банкротное правонарушение в данном деле: освобождения нет (пункт 4)",
        facts=_completed(held_liable_for_bankruptcy_offence_in_this_case=True),
        expected_outcomes={
            "release_barred_by_bankruptcy_offence": True,
            "release_not_applied_at_all": True,
            "citizen_released_from_obligations": False,
            "claim_discharged": False,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-barred-by-withheld-information",
        title_ru="Сведения не предоставлены либо искажены: освобождения нет (пункт 4)",
        facts=_completed(withheld_or_falsified_information_established_by_court=True),
        expected_outcomes={
            "release_barred_by_withheld_information": True,
            "release_not_applied_at_all": True,
            "citizen_released_from_obligations": False,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-barred-by-unlawful-conduct",
        title_ru="Незаконное поведение в обязательстве: освобождения нет, нужен юрист",
        facts=_completed(acted_unlawfully_in_the_obligation_relied_on=True),
        expected_outcomes={
            "release_barred_by_unlawful_conduct_in_the_obligation": True,
            "release_not_applied_at_all": True,
            "requires_human_citizen_release_assessment": True,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-named-claim-survives",
        title_ru="Требование, названное пунктом 5, сохраняет силу",
        facts=_completed(
            is_claim_named_in_paragraph_five=True, claim_filed_in_bankruptcy_register=True
        ),
        expected_outcomes={
            "claim_survives_as_personally_bound": True,
            "claim_discharged": False,
            # Освобождение состоялось — просто этого требования не достигло.
            "citizen_released_from_obligations": True,
            "writ_of_execution_issued_for_the_surviving_registered_claim": True,
            "requires_human_citizen_release_assessment": False,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-current-payment-survives",
        title_ru="Текущий платёж сохраняет силу, но исполнительного листа не получает",
        facts=_completed(is_current_payment_claim=True),
        expected_outcomes={
            "claim_survives_as_personally_bound": True,
            # Лист выдаётся на требования, включённые в реестр; текущий платёж
            # в реестр не включается.
            "writ_of_execution_issued_for_the_surviving_registered_claim": False,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-other-personally-bound-claim-needs-a-lawyer",
        title_ru="Иное требование, связанное с личностью кредитора: оценочная категория",
        facts=_completed(is_other_claim_inseparable_from_the_creditors_person=True),
        expected_outcomes={
            "claim_survives_as_personally_bound": True,
            "requires_human_citizen_release_assessment": True,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-subsidiary-liability-needs-no-fault",
        title_ru="Субсидиарная ответственность сохраняется без формы вины (пункт 6)",
        facts=_completed(is_subsidiary_liability_claim=True),
        expected_outcomes={
            "claim_survives_under_paragraph_six": True,
            "claim_discharged": False,
            "requires_human_citizen_release_assessment": False,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-avoidance-consequences-need-no-fault",
        title_ru="Последствия недействительности сделки сохраняются без формы вины",
        facts=_completed(is_avoided_transaction_consequences_claim=True),
        expected_outcomes={
            "claim_survives_under_paragraph_six": True,
            "claim_discharged": False,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-article-53-1-damages-need-fault",
        title_ru="Убытки по статьям 53 и 53.1 ГК РФ требуют умысла или грубой неосторожности",
        facts=_completed(
            is_damages_claim_under_articles_53_and_53_1=True,
            caused_intentionally_or_by_gross_negligence=True,
        ),
        expected_outcomes={
            "claim_survives_under_paragraph_six": True,
            "claim_discharged": False,
            "requires_human_citizen_release_assessment": True,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-article-53-1-damages-without-fault-are-discharged",
        title_ru="Те же убытки без умысла и грубой неосторожности погашаются",
        facts=_completed(is_damages_claim_under_articles_53_and_53_1=True),
        expected_outcomes={
            "claim_survives_under_paragraph_six": False,
            "claim_discharged": True,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-property-damage-needs-fault",
        title_ru="Вред имуществу сохраняется только при умысле или грубой неосторожности",
        facts=_completed(
            is_property_damage_claim=True, caused_intentionally_or_by_gross_negligence=True
        ),
        expected_outcomes={"claim_survives_under_paragraph_six": True},
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-manager-damages-need-fault",
        title_ru="Убытки арбитражного управляющего — та же оговорка о вине",
        facts=_completed(
            is_manager_damages_claim=True, caused_intentionally_or_by_gross_negligence=True
        ),
        expected_outcomes={"claim_survives_under_paragraph_six": True},
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-claim-unknown-to-creditors-survives",
        title_ru="Требование, о котором кредиторы не знали, сохраняет силу (абзац 2 пункта 3)",
        facts=_completed(creditors_did_not_know_and_should_not_have_known=True),
        expected_outcomes={
            "claim_survives_as_unknown_to_creditors": True,
            "claim_discharged": False,
            "requires_human_citizen_release_assessment": True,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-separate-settlement-survives",
        title_ru="Требование под отдельным мировым соглашением сохраняет силу",
        facts=_completed(separate_settlement_under_article_213_10_1_approved=True),
        expected_outcomes={
            "claim_survives_under_separate_settlement": True,
            "claim_discharged": False,
            "requires_human_citizen_release_assessment": False,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-exception-collects-both-levels",
        title_ru="Исключение пункта 6 статьи 213.27 собирается с обоих уровней",
        facts=_completed(is_claim_named_in_paragraph_five=True),
        expected_outcomes={
            "discharge_exception_applies_to_this_claim": True,
            "release_not_applied_at_all": False,
        },
    ),
    CitizenReleaseEvaluationTask(
        id="citizen-release-bench-empty-facts-say-nothing",
        title_ru="Пустой набор фактов не даёт ни одного вывода",
        facts=_facts(),
        expected_outcomes={
            "citizen_released_from_obligations": False,
            "release_not_applied_at_all": False,
            "claim_survives_as_personally_bound": False,
            "claim_survives_under_paragraph_six": False,
            "claim_survives_as_unknown_to_creditors": False,
            "claim_survives_under_separate_settlement": False,
            "claim_discharged": False,
            "writ_of_execution_issued_for_the_surviving_registered_claim": False,
            "discharge_exception_applies_to_this_claim": False,
            "requires_human_citizen_release_assessment": False,
        },
    ),
)


SYNTHETIC_CITIZEN_RELEASE_RED_TEAM_CASES = (
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-surviving-claim-bars-the-whole-release",
        title_ru="Из сохранения силы одного требования вывести недопустимость освобождения",
        # Самое дорогое смешение двух уровней статьи: освобождение состоялось,
        # просто этого требования не достигло.
        facts=_completed(is_claim_named_in_paragraph_five=True),
        forbidden_outcomes={
            "release_not_applied_at_all": True,
            "citizen_released_from_obligations": False,
        },
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-release-discharges-every-claim",
        title_ru="Из состоявшегося освобождения вывести погашение любого требования",
        facts=_completed(is_subsidiary_liability_claim=True),
        forbidden_outcomes={"claim_discharged": True},
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-bar-discharges-the-claim-anyway",
        title_ru="Погасить требование при недопустимости освобождения",
        facts=_completed(held_liable_for_bankruptcy_offence_in_this_case=True),
        forbidden_outcomes={
            "claim_discharged": True,
            "citizen_released_from_obligations": True,
        },
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-fault-clause-reaches-subsidiary-liability",
        title_ru="Потребовать формы вины для субсидиарной ответственности",
        facts=_completed(is_subsidiary_liability_claim=True),
        forbidden_outcomes={"claim_survives_under_paragraph_six": False},
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-fault-clause-reaches-avoidance-consequences",
        title_ru="Потребовать формы вины для последствий недействительности сделки",
        facts=_completed(is_avoided_transaction_consequences_claim=True),
        forbidden_outcomes={"claim_survives_under_paragraph_six": False},
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-damages-survive-without-fault",
        title_ru="Сохранить убытки по статье 53.1 без умысла и грубой неосторожности",
        facts=_completed(is_damages_claim_under_articles_53_and_53_1=True),
        forbidden_outcomes={"claim_survives_under_paragraph_six": True},
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-property-damage-survives-without-fault",
        title_ru="Сохранить вред имуществу без умысла и грубой неосторожности",
        facts=_completed(is_property_damage_claim=True),
        forbidden_outcomes={"claim_survives_under_paragraph_six": True},
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-release-before-the-completion-ruling",
        title_ru="Освободить гражданина до определения о завершении реализации",
        facts=_facts(citizen_declared_bankrupt=True),
        forbidden_outcomes={
            "citizen_released_from_obligations": True,
            "claim_discharged": True,
            "discharge_exception_applies_to_this_claim": True,
        },
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-bar-without-a-bankruptcy-case",
        title_ru="Применить основания пункта 4 вне дела о банкротстве",
        facts=_facts(),
        forbidden_outcomes={
            "release_not_applied_at_all": True,
            "release_barred_by_bankruptcy_offence": True,
        },
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-writ-for-a-current-payment",
        title_ru="Выдать исполнительный лист на текущий платёж, в реестр не включённый",
        facts=_completed(is_current_payment_claim=True),
        forbidden_outcomes={"writ_of_execution_issued_for_the_surviving_registered_claim": True},
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-writ-for-a-discharged-claim",
        title_ru="Выдать исполнительный лист на погашенное требование",
        facts=_completed(claim_filed_in_bankruptcy_register=True),
        forbidden_outcomes={"writ_of_execution_issued_for_the_surviving_registered_claim": True},
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-unlawful-conduct-is-not-silent",
        title_ru="Снять освобождение по доказанному незаконному поведению без флага юриста",
        facts=_completed(acted_unlawfully_in_the_obligation_relied_on=True),
        forbidden_outcomes={"requires_human_citizen_release_assessment": False},
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-evaluative-personal-claim-is-not-silent",
        title_ru="Сохранить «иное связанное с личностью» требование без флага юриста",
        facts=_completed(is_other_claim_inseparable_from_the_creditors_person=True),
        forbidden_outcomes={"requires_human_citizen_release_assessment": False},
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-unknown-claim-is-not-silent",
        title_ru="Сохранить требование по незнанию кредитора без флага юриста",
        facts=_completed(creditors_did_not_know_and_should_not_have_known=True),
        forbidden_outcomes={"requires_human_citizen_release_assessment": False},
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-named-claim-raises-a-spurious-flag",
        title_ru="Поднять флаг юриста на прямо названном пунктом 5 требовании",
        # Обратная ошибка: требование названо законом, оценивать здесь нечего.
        facts=_completed(is_claim_named_in_paragraph_five=True),
        forbidden_outcomes={"requires_human_citizen_release_assessment": True},
    ),
    CitizenReleaseRedTeamCase(
        id="citizen-release-red-empty-facts-raise-no-flag",
        title_ru="Пустой набор фактов флага юриста не поднимает",
        facts=_facts(),
        forbidden_outcomes={"requires_human_citizen_release_assessment": True},
    ),
)


def _evaluate(facts: CitizenReleaseFactSet, artifact_id: str) -> CitizenReleaseEvaluation:
    mapping = CitizenReleaseEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=list(CITIZEN_RELEASE_LEGAL_SOURCE_REFS),
    )
    constraints: CitizenReleaseConstraintSet = build_citizen_release_constraint_set(mapping)
    return evaluate_citizen_release_constraints(constraints, facts)


def _outcomes(evaluation: CitizenReleaseEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_citizen_release_benchmark_suite() -> CitizenReleaseBenchmarkReport:
    results = []
    for task in SYNTHETIC_CITIZEN_RELEASE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            CitizenReleaseEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return CitizenReleaseBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_citizen_release_red_team_suite() -> CitizenReleaseRedTeamReport:
    results = []
    for case in SYNTHETIC_CITIZEN_RELEASE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        results.append(
            CitizenReleaseRedTeamResult(
                case_id=case.id,
                blocked=all(
                    observed[name] != forbidden
                    for name, forbidden in case.forbidden_outcomes.items()
                ),
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return CitizenReleaseRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
