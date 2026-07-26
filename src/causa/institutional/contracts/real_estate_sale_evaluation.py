from pydantic import BaseModel, Field

from causa.institutional.contracts.real_estate_sale import (
    RealEstateSaleConstraintSet,
    RealEstateSaleEvaluation,
    RealEstateSaleEvidenceMappingResult,
    RealEstateSaleFactSet,
    build_real_estate_sale_constraint_set,
    evaluate_real_estate_sale_constraints,
)


class RealEstateSaleEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: RealEstateSaleFactSet
    expected_outcomes: dict[str, bool]


class RealEstateSaleEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class RealEstateSaleBenchmarkReport(BaseModel):
    id: str = "real-estate-sale-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[RealEstateSaleEvaluationResult] = Field(default_factory=list)


class RealEstateSaleRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: RealEstateSaleFactSet
    forbidden_outcomes: dict[str, bool]


class RealEstateSaleRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class RealEstateSaleRedTeamReport(BaseModel):
    id: str = "real-estate-sale-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[RealEstateSaleRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> RealEstateSaleFactSet:
    values = {field_name: False for field_name in RealEstateSaleFactSet.model_fields}
    values.update(updates)
    return RealEstateSaleFactSet(**values)


SYNTHETIC_REAL_ESTATE_SALE_BENCHMARKS = (
    RealEstateSaleEvaluationTask(
        id="real-estate-sale-bench-qualified",
        title_ru="Договор о передаче в собственность недвижимого имущества",
        facts=_facts(real_estate_transfer_contract=True),
        expected_outcomes={
            "real_estate_sale_qualified": True,
            "requires_human_real_estate_sale_assessment": False,
        },
    ),
    RealEstateSaleEvaluationTask(
        id="real-estate-sale-bench-not-qualified",
        title_ru="Отношения без передачи недвижимости в собственность",
        facts=_facts(written_single_document_signed=True),
        expected_outcomes={"real_estate_sale_qualified": False},
    ),
    RealEstateSaleEvaluationTask(
        id="real-estate-sale-bench-written-form",
        title_ru="Письменная форма одним документом, подписанным сторонами",
        facts=_facts(
            real_estate_transfer_contract=True,
            written_single_document_signed=True,
        ),
        expected_outcomes={
            "written_form_satisfied": True,
            "requires_human_real_estate_sale_assessment": False,
        },
    ),
    RealEstateSaleEvaluationTask(
        id="real-estate-sale-bench-concluded",
        title_ru="Предмет определён и цена согласована — договор заключён",
        facts=_facts(
            real_estate_transfer_contract=True,
            written_single_document_signed=True,
            property_definitively_identified=True,
            price_agreed_in_contract=True,
        ),
        expected_outcomes={
            "contract_concluded": True,
            "requires_human_real_estate_sale_assessment": False,
        },
    ),
    RealEstateSaleEvaluationTask(
        id="real-estate-sale-bench-residential-concluded",
        title_ru="Жилое помещение: указан перечень лиц с правом пользования",
        facts=_facts(
            real_estate_transfer_contract=True,
            written_single_document_signed=True,
            property_definitively_identified=True,
            price_agreed_in_contract=True,
            residential_premises=True,
            occupant_rights_list_included=True,
        ),
        expected_outcomes={
            "contract_concluded": True,
            "requires_human_real_estate_sale_assessment": False,
        },
    ),
    RealEstateSaleEvaluationTask(
        id="real-estate-sale-bench-residential-not-concluded",
        title_ru="Жилое помещение без перечня лиц — договор не заключён",
        facts=_facts(
            real_estate_transfer_contract=True,
            written_single_document_signed=True,
            property_definitively_identified=True,
            price_agreed_in_contract=True,
            residential_premises=True,
        ),
        expected_outcomes={
            "contract_concluded": False,
            "requires_human_real_estate_sale_assessment": False,
        },
    ),
    RealEstateSaleEvaluationTask(
        id="real-estate-sale-bench-ownership-registered",
        title_ru="Переход права собственности зарегистрирован",
        facts=_facts(
            real_estate_transfer_contract=True,
            ownership_transfer_registered=True,
        ),
        expected_outcomes={
            "ownership_transfer_effective": True,
            "requires_human_real_estate_sale_assessment": False,
        },
    ),
    RealEstateSaleEvaluationTask(
        id="real-estate-sale-bench-transfer-by-deed",
        title_ru="Недвижимость передана по передаточному акту",
        facts=_facts(
            real_estate_transfer_contract=True,
            property_handed_over_by_deed=True,
        ),
        expected_outcomes={
            "transfer_obligation_met": True,
            "requires_human_real_estate_sale_assessment": False,
        },
    ),
    RealEstateSaleEvaluationTask(
        id="real-estate-sale-bench-quality-defect",
        title_ru="Недвижимость ненадлежащего качества — средства защиты покупателя",
        facts=_facts(
            real_estate_transfer_contract=True,
            property_quality_defective=True,
        ),
        expected_outcomes={
            "buyer_quality_remedies_available": True,
            "requires_human_real_estate_sale_assessment": True,
        },
    ),
    RealEstateSaleEvaluationTask(
        id="real-estate-sale-bench-transfer-evasion",
        title_ru="Уклонение от подписания передаточного акта считается отказом",
        facts=_facts(
            real_estate_transfer_contract=True,
            party_evaded_transfer_deed=True,
        ),
        expected_outcomes={
            "transfer_evasion_is_refusal": True,
            "requires_human_real_estate_sale_assessment": True,
        },
    ),
)


SYNTHETIC_REAL_ESTATE_SALE_RED_TEAM_CASES = (
    RealEstateSaleRedTeamCase(
        id="real-estate-sale-red-qualify-without-transfer",
        title_ru="Квалифицировать продажу недвижимости без передачи в собственность",
        facts=_facts(written_single_document_signed=True),
        forbidden_outcomes={"real_estate_sale_qualified": True},
    ),
    RealEstateSaleRedTeamCase(
        id="real-estate-sale-red-form-without-signed-document",
        title_ru="Считать форму соблюдённой без единого подписанного документа",
        facts=_facts(real_estate_transfer_contract=True),
        forbidden_outcomes={"written_form_satisfied": True},
    ),
    RealEstateSaleRedTeamCase(
        id="real-estate-sale-red-concluded-without-identification",
        title_ru="Считать договор заключённым без определения предмета",
        facts=_facts(
            real_estate_transfer_contract=True,
            written_single_document_signed=True,
            price_agreed_in_contract=True,
        ),
        forbidden_outcomes={"contract_concluded": True},
    ),
    RealEstateSaleRedTeamCase(
        id="real-estate-sale-red-concluded-without-price",
        title_ru="Считать договор заключённым без согласования цены",
        facts=_facts(
            real_estate_transfer_contract=True,
            written_single_document_signed=True,
            property_definitively_identified=True,
        ),
        forbidden_outcomes={"contract_concluded": True},
    ),
    RealEstateSaleRedTeamCase(
        id="real-estate-sale-red-residential-concluded-without-occupants",
        title_ru="Считать продажу жилого помещения заключённой без перечня лиц",
        facts=_facts(
            real_estate_transfer_contract=True,
            written_single_document_signed=True,
            property_definitively_identified=True,
            price_agreed_in_contract=True,
            residential_premises=True,
        ),
        forbidden_outcomes={"contract_concluded": True},
    ),
    RealEstateSaleRedTeamCase(
        id="real-estate-sale-red-ownership-without-registration",
        title_ru="Считать переход права состоявшимся без государственной регистрации",
        facts=_facts(
            real_estate_transfer_contract=True,
            property_definitively_identified=True,
            price_agreed_in_contract=True,
        ),
        forbidden_outcomes={"ownership_transfer_effective": True},
    ),
    RealEstateSaleRedTeamCase(
        id="real-estate-sale-red-transfer-without-deed",
        title_ru="Считать обязанность по передаче исполненной без передаточного акта",
        facts=_facts(real_estate_transfer_contract=True),
        forbidden_outcomes={"transfer_obligation_met": True},
    ),
    RealEstateSaleRedTeamCase(
        id="real-estate-sale-red-remedies-without-defect",
        title_ru="Признать средства защиты по качеству без недостатков недвижимости",
        facts=_facts(real_estate_transfer_contract=True),
        forbidden_outcomes={"buyer_quality_remedies_available": True},
    ),
    RealEstateSaleRedTeamCase(
        id="real-estate-sale-red-skip-human-on-defect",
        title_ru="Пропустить экспертизу при недвижимости ненадлежащего качества",
        facts=_facts(
            real_estate_transfer_contract=True,
            property_quality_defective=True,
        ),
        forbidden_outcomes={"requires_human_real_estate_sale_assessment": False},
    ),
    RealEstateSaleRedTeamCase(
        id="real-estate-sale-red-skip-human-on-evasion",
        title_ru="Пропустить экспертизу при уклонении от передаточного акта",
        facts=_facts(
            real_estate_transfer_contract=True,
            party_evaded_transfer_deed=True,
        ),
        forbidden_outcomes={"requires_human_real_estate_sale_assessment": False},
    ),
)


def _evaluate(facts: RealEstateSaleFactSet, artifact_id: str) -> RealEstateSaleEvaluation:
    mapping = RealEstateSaleEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-real-estate-sale-law"],
    )
    constraints: RealEstateSaleConstraintSet = build_real_estate_sale_constraint_set(mapping)
    return evaluate_real_estate_sale_constraints(constraints, facts)


def _outcomes(evaluation: RealEstateSaleEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_real_estate_sale_benchmark_suite() -> RealEstateSaleBenchmarkReport:
    results = []
    for task in SYNTHETIC_REAL_ESTATE_SALE_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            RealEstateSaleEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return RealEstateSaleBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_real_estate_sale_red_team_suite() -> RealEstateSaleRedTeamReport:
    results = []
    for case in SYNTHETIC_REAL_ESTATE_SALE_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            RealEstateSaleRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return RealEstateSaleRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
