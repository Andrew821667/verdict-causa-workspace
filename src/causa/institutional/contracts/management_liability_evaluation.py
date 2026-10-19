"""Бенчмарк и red-team для модели ответственности управляющих лиц.

Бенчмарк проверяет, что модель выводит то, что говорит статья 53.1; red-team —
что она **не** выводит того, чего статья не говорит. Второе здесь важнее: ошибка
в сторону ответственности дороже ошибки в сторону её отсутствия, потому что она
переносит на директора или участника последствия, которых закон не предусмотрел.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.management_liability import (
    MANAGEMENT_LIABILITY_LEGAL_SOURCE_REFS,
    ManagementLiabilityConstraintSet,
    ManagementLiabilityEvaluation,
    ManagementLiabilityEvidenceMappingResult,
    ManagementLiabilityFactSet,
    build_management_liability_constraint_set,
    evaluate_management_liability_constraints,
)


class ManagementLiabilityEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ManagementLiabilityFactSet
    expected_outcomes: dict[str, bool]


class ManagementLiabilityEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ManagementLiabilityBenchmarkReport(BaseModel):
    id: str = "management-liability-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ManagementLiabilityEvaluationResult] = Field(default_factory=list)


class ManagementLiabilityRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ManagementLiabilityFactSet
    forbidden_outcomes: dict[str, bool]


class ManagementLiabilityRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ManagementLiabilityRedTeamReport(BaseModel):
    id: str = "management-liability-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ManagementLiabilityRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ManagementLiabilityFactSet:
    """Факты по требованию о возмещении убытков юридическому лицу.

    По умолчанию всё ложно: субъект статьи не назван, убытков нет, соглашения
    нет. Каждый случай ниже включает ровно те признаки, о которых он говорит.
    """
    values = {field_name: False for field_name in ManagementLiabilityFactSet.model_fields}
    values.update(updates)
    return ManagementLiabilityFactSet(**values)


#: Полный набор признаков ответственности по пункту 1: субъект, требование,
#: убытки, вина и нарушенный стандарт.
_DIRECTOR_LIABLE = dict(
    authorised_to_act_for_entity=True,
    claim_brought_by_entity_or_participant=True,
    losses_caused_to_entity=True,
    fault_proven=True,
    bad_faith_proven=True,
)

_MEMBER_LIABLE = dict(
    member_of_collegial_body=True,
    claim_brought_by_entity_or_participant=True,
    losses_caused_to_entity=True,
    fault_proven=True,
    bad_faith_proven=True,
)

SYNTHETIC_MANAGEMENT_LIABILITY_BENCHMARKS = (
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-director",
        title_ru="Директор: вина и недобросовестность доказаны — отвечает (пункт 1)",
        facts=_facts(**_DIRECTOR_LIABLE),
        expected_outcomes={
            "liability_of_authorised_person": True,
            "standard_of_conduct_breached": True,
            "person_within_article_53_1": True,
        },
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-unreasonableness-is-enough",
        title_ru="Неразумности достаточно: стандарт нарушен и без недобросовестности",
        facts=_facts(
            authorised_to_act_for_entity=True,
            claim_brought_by_entity_or_participant=True,
            losses_caused_to_entity=True,
            fault_proven=True,
            unreasonableness_proven=True,
        ),
        expected_outcomes={
            "standard_of_conduct_breached": True,
            "liability_of_authorised_person": True,
        },
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-ordinary-course-is-an-instance",
        title_ru="Выход за обычные условия оборота — частный случай «в том числе»",
        facts=_facts(
            authorised_to_act_for_entity=True,
            claim_brought_by_entity_or_participant=True,
            losses_caused_to_entity=True,
            fault_proven=True,
            conduct_outside_ordinary_course_or_risk=True,
        ),
        expected_outcomes={
            "standard_of_conduct_breached": True,
            "liability_of_authorised_person": True,
            "requires_human_management_liability_assessment": True,
        },
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-no-claim-no-duty-to-compensate",
        title_ru="Без требования юридического лица обязанности возместить нет (пункт 1)",
        facts=_facts(
            authorised_to_act_for_entity=True,
            losses_caused_to_entity=True,
            fault_proven=True,
            bad_faith_proven=True,
        ),
        expected_outcomes={
            "liability_of_authorised_person": False,
            "standard_of_conduct_breached": True,
        },
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-no-fault-no-liability",
        title_ru="Без вины ответственности нет, как бы ни оценивалось поведение",
        facts=_facts(
            authorised_to_act_for_entity=True,
            claim_brought_by_entity_or_participant=True,
            losses_caused_to_entity=True,
            bad_faith_proven=True,
        ),
        expected_outcomes={"liability_of_authorised_person": False},
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-member-liable",
        title_ru="Член коллегиального органа отвечает по пункту 1 через пункт 2",
        facts=_facts(**_MEMBER_LIABLE),
        expected_outcomes={
            "liability_of_collegial_member": True,
            "collegial_member_exempt": False,
        },
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-member-voted-against",
        title_ru="Голосовавший против освобождён (пункт 2)",
        facts=_facts(**_MEMBER_LIABLE, voted_against_the_harmful_decision=True),
        expected_outcomes={
            "collegial_member_exempt": True,
            "liability_of_collegial_member": False,
        },
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-member-abstained-in-good-faith",
        title_ru="Добросовестно не участвовавший в голосовании освобождён (пункт 2)",
        facts=_facts(**_MEMBER_LIABLE, abstained_in_good_faith=True),
        expected_outcomes={
            "collegial_member_exempt": True,
            "liability_of_collegial_member": False,
            "requires_human_management_liability_assessment": True,
        },
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-controlling-person-without-claim",
        title_ru="Пункт 3 требования условием не называет — в отличие от пункта 1",
        facts=_facts(
            has_actual_ability_to_determine_actions=True,
            losses_caused_to_entity=True,
            fault_proven=True,
            unreasonableness_proven=True,
        ),
        expected_outcomes={"liability_of_controlling_person": True},
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-joint-liability",
        title_ru="Совместное причинение убытков — солидарная обязанность (пункт 4)",
        facts=_facts(**_DIRECTOR_LIABLE, losses_caused_jointly_with_others=True),
        expected_outcomes={
            "joint_and_several_liability": True,
            "requires_human_management_liability_assessment": True,
        },
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-agreement-void-for-bad-faith",
        title_ru="Соглашение об ограничении за недобросовестность ничтожно (пункт 5)",
        facts=_facts(
            authorised_to_act_for_entity=True,
            liability_limitation_agreement_made=True,
            agreement_covers_bad_faith_conduct=True,
        ),
        expected_outcomes={"liability_limitation_agreement_void": True},
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-public-company-extends-voidness",
        title_ru="В публичном обществе ничтожность распространяется на неразумность",
        facts=_facts(
            authorised_to_act_for_entity=True,
            entity_is_public_company=True,
            liability_limitation_agreement_made=True,
            agreement_covers_unreasonable_conduct=True,
        ),
        expected_outcomes={
            "liability_limitation_agreement_void": True,
            "limitation_of_unreasonable_conduct_permitted": False,
        },
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-non-public-limitation-permitted",
        title_ru="В непубличном обществе ограничение за неразумность ничтожным не является",
        facts=_facts(
            authorised_to_act_for_entity=True,
            liability_limitation_agreement_made=True,
            agreement_covers_unreasonable_conduct=True,
        ),
        expected_outcomes={
            "limitation_of_unreasonable_conduct_permitted": True,
            "liability_limitation_agreement_void": False,
        },
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-controlling-agreement-always-void",
        title_ru="Для лица пункта 3 ничтожно любое такое соглашение (пункт 5 абзац 2)",
        facts=_facts(
            has_actual_ability_to_determine_actions=True,
            liability_limitation_agreement_made=True,
        ),
        expected_outcomes={
            "liability_limitation_agreement_void": True,
            "limitation_of_unreasonable_conduct_permitted": False,
        },
    ),
    ManagementLiabilityEvaluationTask(
        id="management-liability-bench-outside-the-article",
        title_ru="Лицо вне субъектов статьи 53.1 — ответственность к нему не применяется",
        facts=_facts(losses_caused_to_entity=True, fault_proven=True, bad_faith_proven=True),
        expected_outcomes={
            "person_within_article_53_1": False,
            "liability_of_authorised_person": False,
            "liability_of_collegial_member": False,
            "liability_of_controlling_person": False,
            "requires_human_management_liability_assessment": False,
        },
    ),
)


SYNTHETIC_MANAGEMENT_LIABILITY_RED_TEAM_CASES = (
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-liability-without-fault",
        title_ru="Возложить ответственность без вины",
        facts=_facts(
            authorised_to_act_for_entity=True,
            claim_brought_by_entity_or_participant=True,
            losses_caused_to_entity=True,
            bad_faith_proven=True,
        ),
        forbidden_outcomes={"liability_of_authorised_person": True},
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-liability-without-standard-breach",
        title_ru="Возложить ответственность за убытки без нарушения стандарта поведения",
        facts=_facts(
            authorised_to_act_for_entity=True,
            claim_brought_by_entity_or_participant=True,
            losses_caused_to_entity=True,
            fault_proven=True,
        ),
        forbidden_outcomes={"liability_of_authorised_person": True},
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-liability-without-losses",
        title_ru="Возложить ответственность без убытков",
        facts=_facts(
            authorised_to_act_for_entity=True,
            claim_brought_by_entity_or_participant=True,
            bad_faith_proven=True,
        ),
        forbidden_outcomes={"liability_of_authorised_person": True},
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-director-duty-without-claim",
        title_ru="Вывести обязанность возместить по пункту 1 без требования",
        facts=_facts(
            authorised_to_act_for_entity=True,
            losses_caused_to_entity=True,
            fault_proven=True,
            bad_faith_proven=True,
        ),
        forbidden_outcomes={"liability_of_authorised_person": True},
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-ignore-vote-against",
        title_ru="Привлечь члена органа, голосовавшего против решения",
        facts=_facts(**_MEMBER_LIABLE, voted_against_the_harmful_decision=True),
        forbidden_outcomes={"liability_of_collegial_member": True},
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-ignore-good-faith-abstention",
        title_ru="Привлечь члена органа, добросовестно не участвовавшего в голосовании",
        facts=_facts(**_MEMBER_LIABLE, abstained_in_good_faith=True),
        forbidden_outcomes={"liability_of_collegial_member": True},
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-exemption-spills-to-other-grounds",
        title_ru="Распространить исключение пункта 2 на ответственность директора",
        facts=_facts(
            **_DIRECTOR_LIABLE,
            member_of_collegial_body=True,
            voted_against_the_harmful_decision=True,
        ),
        forbidden_outcomes={"liability_of_authorised_person": False},
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-void-non-public-unreasonableness",
        title_ru="Объявить ничтожным ограничение за неразумность в непубличном обществе",
        facts=_facts(
            authorised_to_act_for_entity=True,
            liability_limitation_agreement_made=True,
            agreement_covers_unreasonable_conduct=True,
        ),
        forbidden_outcomes={"liability_limitation_agreement_void": True},
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-permit-limitation-for-bad-faith",
        title_ru="Признать допустимым ограничение за недобросовестные действия",
        facts=_facts(
            authorised_to_act_for_entity=True,
            liability_limitation_agreement_made=True,
            agreement_covers_bad_faith_conduct=True,
            agreement_covers_unreasonable_conduct=True,
        ),
        forbidden_outcomes={"limitation_of_unreasonable_conduct_permitted": True},
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-permit-limitation-for-controlling-person",
        title_ru="Признать допустимым ограничение ответственности лица пункта 3",
        facts=_facts(
            has_actual_ability_to_determine_actions=True,
            liability_limitation_agreement_made=True,
            agreement_covers_unreasonable_conduct=True,
        ),
        forbidden_outcomes={
            "limitation_of_unreasonable_conduct_permitted": True,
            "liability_limitation_agreement_void": False,
        },
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-joint-liability-without-liability",
        title_ru="Вывести солидарность при отсутствии ответственности самого лица",
        facts=_facts(
            authorised_to_act_for_entity=True,
            losses_caused_to_entity=True,
            losses_caused_jointly_with_others=True,
            fault_proven=True,
            bad_faith_proven=True,
        ),
        forbidden_outcomes={"joint_and_several_liability": True},
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-liability-outside-the-article",
        title_ru="Привлечь лицо, не являющееся субъектом статьи 53.1",
        facts=_facts(
            claim_brought_by_entity_or_participant=True,
            losses_caused_to_entity=True,
            fault_proven=True,
            bad_faith_proven=True,
        ),
        forbidden_outcomes={
            "liability_of_authorised_person": True,
            "liability_of_collegial_member": True,
            "liability_of_controlling_person": True,
        },
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-skip-human-on-ordinary-course",
        title_ru="Пропустить оценку юриста при выходе за обычные условия оборота",
        facts=_facts(
            authorised_to_act_for_entity=True,
            claim_brought_by_entity_or_participant=True,
            losses_caused_to_entity=True,
            fault_proven=True,
            conduct_outside_ordinary_course_or_risk=True,
        ),
        forbidden_outcomes={"requires_human_management_liability_assessment": False},
    ),
    ManagementLiabilityRedTeamCase(
        id="management-liability-red-human-flag-on-plain-bad-faith",
        title_ru="Требовать оценку юриста там, где недобросовестность прямо доказана",
        facts=_facts(**_DIRECTOR_LIABLE),
        forbidden_outcomes={"requires_human_management_liability_assessment": True},
    ),
)


def _evaluate(facts: ManagementLiabilityFactSet, artifact_id: str) -> ManagementLiabilityEvaluation:
    mapping = ManagementLiabilityEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=list(MANAGEMENT_LIABILITY_LEGAL_SOURCE_REFS),
    )
    constraints: ManagementLiabilityConstraintSet = build_management_liability_constraint_set(
        mapping
    )
    return evaluate_management_liability_constraints(constraints, facts)


def _outcomes(evaluation: ManagementLiabilityEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_management_liability_benchmark_suite() -> ManagementLiabilityBenchmarkReport:
    results = []
    for task in SYNTHETIC_MANAGEMENT_LIABILITY_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ManagementLiabilityEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ManagementLiabilityBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_management_liability_red_team_suite() -> ManagementLiabilityRedTeamReport:
    results = []
    for case in SYNTHETIC_MANAGEMENT_LIABILITY_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        results.append(
            ManagementLiabilityRedTeamResult(
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
    return ManagementLiabilityRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
