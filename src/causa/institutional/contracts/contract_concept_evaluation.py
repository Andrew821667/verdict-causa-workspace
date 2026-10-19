"""Бенчмарк и red-team для модели понятия договора.

Бенчмарк проверяет, что модель отвечает то, что говорит статья 420; red-team —
что она не отвечает того, чего статья не говорит. Опасность здесь особого рода.
Остальные институты ошибаются в сторону требования или против него; этот
институт ошибается в сторону **применимости целого свода правил**. Объявить
общие положения об обязательствах применимыми там, где их вытеснило специальное
правило, — значит разрешить конвейеру разбирать дело не той частью кодекса.
"""

from pydantic import BaseModel, Field

from causa.institutional.contracts.contract_concept import (
    CONTRACT_CONCEPT_LEGAL_SOURCE_REFS,
    ContractConceptConstraintSet,
    ContractConceptEvaluation,
    ContractConceptEvidenceMappingResult,
    ContractConceptFactSet,
    build_contract_concept_constraint_set,
    evaluate_contract_concept_constraints,
)


class ContractConceptEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: ContractConceptFactSet
    expected_outcomes: dict[str, bool]


class ContractConceptEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ContractConceptBenchmarkReport(BaseModel):
    id: str = "contract-concept-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[ContractConceptEvaluationResult] = Field(default_factory=list)


class ContractConceptRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: ContractConceptFactSet
    forbidden_outcomes: dict[str, bool]


class ContractConceptRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class ContractConceptRedTeamReport(BaseModel):
    id: str = "contract-concept-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[ContractConceptRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> ContractConceptFactSet:
    """Факты о понятии договора и применимых к нему правилах.

    По умолчанию всё ложно: ни соглашения, ни односторонней сделки, ни
    направленности. Каждый случай ниже включает ровно те признаки, о которых
    он говорит.
    """
    values = {field_name: False for field_name in ContractConceptFactSet.model_fields}
    values.update(updates)
    return ContractConceptFactSet(**values)


#: Соглашение двух лиц об установлении гражданских прав: минимальный состав
#: пункта 1, на который опираются все выводы о применимых правилах.
_CONTRACT = dict(
    agreement_of_two_or_more_persons=True,
    directed_at_establishing_rights_and_duties=True,
)

#: Тот же договор, и спорное обязательство возникло из него: состав пункта 3.
_CONTRACTUAL_OBLIGATION = dict(_CONTRACT, obligation_arose_from_the_contract=True)


SYNTHETIC_CONTRACT_CONCEPT_BENCHMARKS = (
    ContractConceptEvaluationTask(
        id="contract-concept-bench-qualified-by-establishing",
        title_ru="Соглашение об установлении гражданских прав — договор (пункт 1)",
        facts=_facts(**_CONTRACT),
        expected_outcomes={
            "contract_qualified_under_article_420": True,
            "qualification_fails_for_lack_of_a_second_party": False,
            "qualification_fails_for_non_civil_subject_matter": False,
            "requires_human_contract_concept_assessment": False,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-qualified-by-terminating",
        title_ru="Соглашение о прекращении прав — договор не менее, чем о установлении",
        facts=_facts(
            agreement_of_two_or_more_persons=True,
            directed_at_terminating_rights_and_duties=True,
        ),
        expected_outcomes={
            "contract_qualified_under_article_420": True,
            "chapter_9_transaction_rules_apply": True,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-qualified-by-changing",
        title_ru="Соглашение об изменении прав — договор (третья направленность)",
        facts=_facts(
            agreement_of_two_or_more_persons=True,
            directed_at_changing_rights_and_duties=True,
        ),
        expected_outcomes={
            "contract_qualified_under_article_420": True,
            "chapter_9_transaction_rules_apply": True,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-unilateral-act-is-not-a-contract",
        title_ru="Односторонняя сделка договором не является (пункт 1)",
        facts=_facts(
            single_person_disposition_asserted=True,
            directed_at_establishing_rights_and_duties=True,
        ),
        expected_outcomes={
            "contract_qualified_under_article_420": False,
            "qualification_fails_for_lack_of_a_second_party": True,
            "chapter_9_transaction_rules_apply": False,
            "requires_human_contract_concept_assessment": False,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-non-civil-subject-matter",
        title_ru="Соглашение о негражданских правах под понятие не подпадает (пункт 1)",
        facts=_facts(**_CONTRACT, rights_and_duties_lie_outside_civil_law=True),
        expected_outcomes={
            "contract_qualified_under_article_420": False,
            "qualification_fails_for_non_civil_subject_matter": True,
            "qualification_fails_for_lack_of_a_second_party": False,
            "chapter_9_transaction_rules_apply": False,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-chapter-9-applies",
        title_ru="К договору применяются правила главы 9 о сделках (пункт 2)",
        facts=_facts(**_CONTRACT),
        expected_outcomes={
            "chapter_9_transaction_rules_apply": True,
            "requires_human_contract_concept_assessment": False,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-code-displaces-chapter-9",
        title_ru="Правила главы 9 вытеснены самим Кодексом (пункт 2)",
        facts=_facts(**_CONTRACT, code_provides_otherwise_for_transaction_rules=True),
        expected_outcomes={
            "contract_qualified_under_article_420": True,
            "chapter_9_transaction_rules_apply": False,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-general-obligation-provisions-apply",
        title_ru="К обязательству из договора применяются статьи 307–419 (пункт 3)",
        facts=_facts(**_CONTRACTUAL_OBLIGATION),
        expected_outcomes={
            "general_obligation_provisions_apply": True,
            "special_rule_displaces_general_provisions": False,
            "requires_human_contract_concept_assessment": False,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-chapter-27-displaces-general",
        title_ru="Общее положение вытеснено правилом главы 27 (пункт 3)",
        facts=_facts(**_CONTRACTUAL_OBLIGATION, chapter_27_rule_provides_otherwise=True),
        expected_outcomes={
            "general_obligation_provisions_apply": False,
            "special_rule_displaces_general_provisions": True,
            "requires_human_contract_concept_assessment": True,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-specific-type-displaces-general",
        title_ru="Общее положение вытеснено правилом об отдельном виде договора (пункт 3)",
        facts=_facts(
            **_CONTRACTUAL_OBLIGATION, specific_contract_type_rule_provides_otherwise=True
        ),
        expected_outcomes={
            "general_obligation_provisions_apply": False,
            "special_rule_displaces_general_provisions": True,
            "requires_human_contract_concept_assessment": True,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-agreement-cannot-displace-the-code",
        title_ru="Соглашение сторон правила Кодекса не вытесняет (пункты 2 и 3)",
        facts=_facts(**_CONTRACT, displacement_asserted_by_agreement_not_by_code=True),
        expected_outcomes={
            "agreement_cannot_displace_code_rules": True,
            "chapter_9_transaction_rules_apply": True,
            "requires_human_contract_concept_assessment": True,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-multiparty-general-provisions-apply",
        title_ru="К многостороннему договору общие положения применяются (пункт 4)",
        facts=_facts(**_CONTRACT, contract_has_more_than_two_parties=True),
        expected_outcomes={
            "general_contract_provisions_apply_to_multiparty_contract": True,
            "general_contract_provisions_withheld_from_multiparty_contract": False,
            "requires_human_contract_concept_assessment": False,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-multiparty-provision-withheld",
        title_ru="Общее положение противоречит многостороннему характеру (пункт 4)",
        facts=_facts(
            **_CONTRACT,
            contract_has_more_than_two_parties=True,
            general_contract_provision_contradicts_multilateral_nature=True,
        ),
        expected_outcomes={
            "general_contract_provisions_apply_to_multiparty_contract": False,
            "general_contract_provisions_withheld_from_multiparty_contract": True,
            "requires_human_contract_concept_assessment": True,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-two-party-contract-has-no-multiparty-conclusion",
        title_ru="У двустороннего договора вывода о пункте 4 нет",
        facts=_facts(**_CONTRACT),
        expected_outcomes={
            "contract_qualified_under_article_420": True,
            "general_contract_provisions_apply_to_multiparty_contract": False,
            "general_contract_provisions_withheld_from_multiparty_contract": False,
        },
    ),
    ContractConceptEvaluationTask(
        id="contract-concept-bench-empty-facts-say-nothing",
        title_ru="Пустой набор фактов не даёт ни одного вывода",
        facts=_facts(),
        expected_outcomes={
            "contract_qualified_under_article_420": False,
            "qualification_fails_for_lack_of_a_second_party": False,
            "qualification_fails_for_non_civil_subject_matter": False,
            "chapter_9_transaction_rules_apply": False,
            "general_obligation_provisions_apply": False,
            "special_rule_displaces_general_provisions": False,
            "agreement_cannot_displace_code_rules": False,
            "general_contract_provisions_apply_to_multiparty_contract": False,
            "general_contract_provisions_withheld_from_multiparty_contract": False,
            "requires_human_contract_concept_assessment": False,
        },
    ),
)


SYNTHETIC_CONTRACT_CONCEPT_RED_TEAM_CASES = (
    ContractConceptRedTeamCase(
        id="contract-concept-red-agreement-without-any-aim",
        title_ru="Соглашение без направленности на права и обязанности не договор",
        facts=_facts(agreement_of_two_or_more_persons=True),
        forbidden_outcomes={
            "contract_qualified_under_article_420": True,
            "chapter_9_transaction_rules_apply": True,
        },
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-aim-without-agreement",
        title_ru="Направленность без соглашения двух лиц не даёт договора",
        facts=_facts(directed_at_establishing_rights_and_duties=True),
        forbidden_outcomes={
            "contract_qualified_under_article_420": True,
            "qualification_fails_for_lack_of_a_second_party": True,
        },
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-unilateral-act-does-not-get-contract-rules",
        title_ru="Односторонней сделке правила о договорах не достаются",
        facts=_facts(
            single_person_disposition_asserted=True,
            directed_at_establishing_rights_and_duties=True,
        ),
        forbidden_outcomes={
            "contract_qualified_under_article_420": True,
            "chapter_9_transaction_rules_apply": True,
            "general_contract_provisions_apply_to_multiparty_contract": True,
        },
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-non-civil-agreement-gets-no-code-rules",
        title_ru="Соглашению о негражданских правах правила Кодекса не достаются",
        facts=_facts(**_CONTRACT, rights_and_duties_lie_outside_civil_law=True),
        forbidden_outcomes={
            "contract_qualified_under_article_420": True,
            "chapter_9_transaction_rules_apply": True,
        },
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-two-failures-are-not-the-same-failure",
        title_ru="Неудача по числу лиц и неудача по отрасли прав не смешиваются",
        facts=_facts(**_CONTRACT, rights_and_duties_lie_outside_civil_law=True),
        forbidden_outcomes={"qualification_fails_for_lack_of_a_second_party": True},
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-general-provisions-need-a-contractual-obligation",
        title_ru="Общие положения об обязательствах без обязательства из договора",
        facts=_facts(**_CONTRACT),
        forbidden_outcomes={
            "general_obligation_provisions_apply": True,
            "special_rule_displaces_general_provisions": True,
        },
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-displacement-does-not-also-apply-them",
        title_ru="Вытеснение и применимость одновременно не выводятся",
        facts=_facts(**_CONTRACTUAL_OBLIGATION, chapter_27_rule_provides_otherwise=True),
        forbidden_outcomes={"general_obligation_provisions_apply": True},
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-agreement-displacement-is-not-a-code-displacement",
        title_ru="Вытеснение соглашением не отменяет правил главы 9 и статей 307–419",
        facts=_facts(
            **_CONTRACTUAL_OBLIGATION, displacement_asserted_by_agreement_not_by_code=True
        ),
        forbidden_outcomes={
            "chapter_9_transaction_rules_apply": False,
            "general_obligation_provisions_apply": False,
            "special_rule_displaces_general_provisions": True,
        },
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-code-displacement-touches-only-chapter-9",
        title_ru="Оговорка пункта 2 не отменяет общих положений об обязательствах",
        facts=_facts(**_CONTRACTUAL_OBLIGATION, code_provides_otherwise_for_transaction_rules=True),
        forbidden_outcomes={
            "general_obligation_provisions_apply": False,
            "special_rule_displaces_general_provisions": True,
        },
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-chapter-27-displacement-touches-only-article-3",
        title_ru="Оговорка пункта 3 не отменяет правил главы 9 о сделках",
        facts=_facts(**_CONTRACTUAL_OBLIGATION, chapter_27_rule_provides_otherwise=True),
        forbidden_outcomes={"chapter_9_transaction_rules_apply": False},
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-multiparty-rule-needs-more-than-two-parties",
        title_ru="Вывод пункта 4 у двустороннего договора не возникает",
        facts=_facts(**_CONTRACTUAL_OBLIGATION),
        forbidden_outcomes={
            "general_contract_provisions_apply_to_multiparty_contract": True,
            "general_contract_provisions_withheld_from_multiparty_contract": True,
        },
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-multiparty-contradiction-is-not-silent",
        title_ru="Противоречие многостороннему характеру без флага юриста не проходит",
        facts=_facts(
            **_CONTRACT,
            contract_has_more_than_two_parties=True,
            general_contract_provision_contradicts_multilateral_nature=True,
        ),
        forbidden_outcomes={
            "requires_human_contract_concept_assessment": False,
            "general_contract_provisions_apply_to_multiparty_contract": True,
        },
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-displacement-is-not-silent",
        title_ru="Вытеснение общего положения без флага юриста не проходит",
        facts=_facts(
            **_CONTRACTUAL_OBLIGATION, specific_contract_type_rule_provides_otherwise=True
        ),
        forbidden_outcomes={"requires_human_contract_concept_assessment": False},
    ),
    ContractConceptRedTeamCase(
        id="contract-concept-red-empty-facts-raise-no-flag",
        title_ru="Пустой набор фактов флага юриста не поднимает",
        facts=_facts(),
        forbidden_outcomes={"requires_human_contract_concept_assessment": True},
    ),
)


def _evaluate(facts: ContractConceptFactSet, artifact_id: str) -> ContractConceptEvaluation:
    mapping = ContractConceptEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=list(CONTRACT_CONCEPT_LEGAL_SOURCE_REFS),
    )
    constraints: ContractConceptConstraintSet = build_contract_concept_constraint_set(mapping)
    return evaluate_contract_concept_constraints(constraints, facts)


def _outcomes(evaluation: ContractConceptEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_contract_concept_benchmark_suite() -> ContractConceptBenchmarkReport:
    results = []
    for task in SYNTHETIC_CONTRACT_CONCEPT_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            ContractConceptEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return ContractConceptBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_contract_concept_red_team_suite() -> ContractConceptRedTeamReport:
    results = []
    for case in SYNTHETIC_CONTRACT_CONCEPT_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        results.append(
            ContractConceptRedTeamResult(
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
    return ContractConceptRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
