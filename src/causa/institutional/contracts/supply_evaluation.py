from pydantic import BaseModel, Field

from causa.institutional.contracts.supply import (
    SupplyEvaluation,
    SupplyEvidenceMappingResult,
    SupplyFactSet,
    build_supply_constraint_set,
    evaluate_supply_constraints,
)


class SupplyEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: SupplyFactSet
    expected_outcomes: dict[str, bool]


class SupplyEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SupplyBenchmarkReport(BaseModel):
    id: str = "supply-articles-506-524-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[SupplyEvaluationResult] = Field(default_factory=list)


class SupplyRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: SupplyFactSet
    forbidden_outcomes: dict[str, bool]


class SupplyRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SupplyRedTeamReport(BaseModel):
    id: str = "supply-articles-506-524-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[SupplyRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> SupplyFactSet:
    values = {field_name: False for field_name in SupplyFactSet.model_fields}
    values.update(
        contract_concluded=True,
        supplier_business=True,
        supplier_produced_or_procured_goods=True,
        goods_nonpersonal_use=True,
        transfer_term_defined=True,
    )
    values.update(updates)
    return SupplyFactSet(**values)


SYNTHETIC_SUPPLY_ARTICLES_BENCHMARKS = (
    SupplyEvaluationTask(
        id="supply-bench-506-qualified",
        title_ru="Квалифицирующие признаки договора поставки",
        facts=_facts(),
        expected_outcomes={"supply_contract_qualified": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-506-term-default",
        title_ru="Определение неуказанного срока поставки по общим правилам",
        facts=_facts(transfer_term_defined=False),
        expected_outcomes={
            "supply_contract_qualified": True,
            "delivery_term_requires_general_default": True,
        },
    ),
    SupplyEvaluationTask(
        id="supply-bench-507-negotiation-loss",
        title_ru="Уклонение от согласования разногласий",
        facts=_facts(disagreements_received=True, loss_claimed=True, causation_proven=True),
        expected_outcomes={
            "negotiation_response_breach": True,
            "negotiation_loss_issue": True,
        },
    ),
    SupplyEvaluationTask(
        id="supply-bench-508-agreed-schedule",
        title_ru="Согласованный график внутри периодов поставки",
        facts=_facts(
            periodic_delivery=True,
            delivery_periods_agreed=True,
            delivery_schedule_agreed=True,
        ),
        expected_outcomes={"agreed_delivery_schedule_controls": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-508-monthly-default",
        title_ru="Равномерная помесячная поставка при отсутствии периодов",
        facts=_facts(periodic_delivery=True),
        expected_outcomes={"monthly_delivery_default": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-508-early-delivery",
        title_ru="Согласованная и принятая досрочная поставка",
        facts=_facts(
            early_delivery=True,
            buyer_consented_early_delivery=True,
            buyer_accepted_early_delivery=True,
        ),
        expected_outcomes={
            "early_delivery_permitted": True,
            "early_delivery_counts_next_period": True,
        },
    ),
    SupplyEvaluationTask(
        id="supply-bench-509-shipment-order",
        title_ru="Убытки из-за непредставления отгрузочной разнарядки",
        facts=_facts(
            shipment_order_required=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        expected_outcomes={
            "shipment_order_default": True,
            "shipment_order_loss_issue": True,
        },
    ),
    SupplyEvaluationTask(
        id="supply-bench-513-inspection-gap",
        title_ru="Получение товара без своевременной проверки",
        facts=_facts(buyer_received_goods=True),
        expected_outcomes={
            "acceptance_duties_satisfied": False,
            "acceptance_inspection_gap": True,
        },
    ),
    SupplyEvaluationTask(
        id="supply-bench-510-transport-choice",
        title_ru="Выбор транспорта поставщиком при пробеле договора",
        facts=_facts(supplier_selected_transport=True),
        expected_outcomes={"supplier_transport_choice": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-511-makeup",
        title_ru="Восполнение недопоставки в последующем периоде",
        facts=_facts(quantity_shortfall=True, contract_term_continues=True),
        expected_outcomes={"makeup_delivery_required": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-511-refusal",
        title_ru="Отказ покупателя от просроченного восполнения",
        facts=_facts(
            quantity_shortfall=True,
            contract_term_continues=True,
            buyer_refused_late_makeup_by_notice=True,
        ),
        expected_outcomes={
            "makeup_delivery_required": False,
            "late_makeup_refusal_effective": True,
        },
    ),
    SupplyEvaluationTask(
        id="supply-bench-512-assortment-offset",
        title_ru="Зачет превышения по одному ассортименту без согласия",
        facts=_facts(quantity_shortfall=True, cross_assortment_offset=True),
        expected_outcomes={"cross_assortment_offset_barred": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-513-acceptance",
        title_ru="Надлежащая приемка с извещением о расхождении",
        facts=_facts(
            buyer_received_goods=True,
            inspection_timely=True,
            discrepancy_found=True,
            prompt_written_notice=True,
        ),
        expected_outcomes={
            "acceptance_duties_satisfied": True,
            "acceptance_notice_gap": False,
        },
    ),
    SupplyEvaluationTask(
        id="supply-bench-512-makeup-assortment",
        title_ru="Ассортимент восполнения при отсутствии соглашения",
        facts=_facts(
            quantity_shortfall=True,
            prior_period_assortment_proven=True,
        ),
        expected_outcomes={"makeup_assortment_default_to_prior_period": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-514-custody",
        title_ru="Ответственное хранение и расходы покупателя",
        facts=_facts(
            lawful_refusal=True,
            goods_preserved=True,
            supplier_notified=True,
            custody_expenses_documented=True,
        ),
        expected_outcomes={
            "responsible_custody_duties_satisfied": True,
            "supplier_custody_cost_liability": True,
        },
    ),
    SupplyEvaluationTask(
        id="supply-bench-514-disposal",
        title_ru="Реализация или возврат товара при бездействии поставщика",
        facts=_facts(
            lawful_refusal=True,
            goods_preserved=True,
            supplier_notified=True,
            buyer_realized_or_returned_goods=True,
        ),
        expected_outcomes={"buyer_disposal_available": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-514-unlawful-refusal",
        title_ru="Требование оплаты при неправомерном отказе от товара",
        facts=_facts(
            unlawful_refusal=True,
            supplier_demanded_payment_after_refusal=True,
        ),
        expected_outcomes={"supplier_payment_claim_after_unlawful_refusal": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-515-selection",
        title_ru="Неосуществление покупателем выборки",
        facts=_facts(
            buyer_selection_required=True,
            selection_due=True,
            buyer_failed_selection=True,
            supplier_notified_readiness=True,
        ),
        expected_outcomes={"selection_supplier_remedy_available": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-516-payment",
        title_ru="Требование к покупателю после неплатежа получателя",
        facts=_facts(
            payment_due=True,
            consignee_payment_duty=True,
            consignee_failed_payment=True,
        ),
        expected_outcomes={"buyer_payment_claim_available": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-517-container",
        title_ru="Невозврат многооборотной тары",
        facts=_facts(returnable_container=True, container_return_due=True),
        expected_outcomes={"container_return_breach": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-518-quality",
        title_ru="Требования покупателя из недостатков товара",
        facts=_facts(quality_defect=True),
        expected_outcomes={"quality_remedies_available": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-518-prompt-cure",
        title_ru="Незамедлительная замена дефектного товара",
        facts=_facts(quality_defect=True, defect_promptly_cured_or_replaced=True),
        expected_outcomes={
            "quality_remedies_available": False,
            "quality_remedies_displaced_by_prompt_cure": True,
        },
    ),
    SupplyEvaluationTask(
        id="supply-bench-519-completeness",
        title_ru="Требования из некомплектной поставки",
        facts=_facts(incomplete_goods=True),
        expected_outcomes={"completeness_remedies_available": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-520-cover",
        title_ru="Закупка недопоставленного товара у третьего лица",
        facts=_facts(
            quantity_shortfall=True,
            buyer_acquired_substitute=True,
            substitute_expenses_reasonable_documented=True,
        ),
        expected_outcomes={"cover_purchase_cost_recovery": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-520-withholding",
        title_ru="Удержание оплаты за неустраненный некачественный товар",
        facts=_facts(quality_defect=True, payment_withheld=True),
        expected_outcomes={"payment_withholding_available": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-521-penalty",
        title_ru="Начисление неустойки до фактического восполнения",
        facts=_facts(
            delivery_late=True,
            penalty_applies_to_short_or_late=True,
            replenishment_duty_continues=True,
        ),
        expected_outcomes={"penalty_continues_until_replenishment": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-522-allocation",
        title_ru="Распределение исполнения между несколькими договорами",
        facts=_facts(multiple_supply_contracts=True),
        expected_outcomes={"default_contract_allocation_required": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-523-supplier-breach",
        title_ru="Повторная просрочка как существенное нарушение поставщика",
        facts=_facts(
            delivery_late=True,
            repeated_late_delivery=True,
            unilateral_refusal_notice_delivered=True,
            contract_terminated=True,
        ),
        expected_outcomes={
            "supplier_material_breach": True,
            "supply_unilateral_refusal_effective": True,
        },
    ),
    SupplyEvaluationTask(
        id="supply-bench-523-buyer-breach",
        title_ru="Повторное нарушение срока оплаты покупателем",
        facts=_facts(
            payment_due=True,
            repeated_payment_default=True,
            unilateral_refusal_notice_delivered=True,
            contract_terminated=True,
        ),
        expected_outcomes={
            "buyer_material_breach": True,
            "supply_unilateral_refusal_effective": True,
        },
    ),
    SupplyEvaluationTask(
        id="supply-bench-524-concrete",
        title_ru="Конкретные убытки по заменяющей сделке",
        facts=_facts(
            contract_terminated=True,
            replacement_transaction_made=True,
            replacement_transaction_reasonable=True,
            replacement_transaction_timely=True,
            contract_price_proven=True,
            replacement_price_proven=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        expected_outcomes={"concrete_price_damages_available": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-524-abstract",
        title_ru="Абстрактные убытки по текущей цене",
        facts=_facts(
            contract_terminated=True,
            contract_price_proven=True,
            current_price_available=True,
            current_price_proven=True,
            current_price_time_place_adjusted=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        expected_outcomes={"abstract_current_price_damages_available": True},
    ),
    SupplyEvaluationTask(
        id="supply-bench-524-other-loss",
        title_ru="Сохранение иных доказанных убытков",
        facts=_facts(
            contract_terminated=True,
            loss_claimed=True,
            causation_proven=True,
            other_loss_proven=True,
        ),
        expected_outcomes={"other_damages_preserved": True},
    ),
)


SYNTHETIC_SUPPLY_ARTICLES_RED_TEAM_CASES = (
    SupplyRedTeamCase(
        id="supply-red-506-personal-use",
        title_ru="Квалифицировать личную покупку как поставку",
        facts=_facts(goods_nonpersonal_use=False),
        forbidden_outcomes={"supply_contract_qualified": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-506-nonbusiness-supplier",
        title_ru="Игнорировать предпринимательский статус поставщика",
        facts=_facts(supplier_business=False),
        forbidden_outcomes={"supply_contract_qualified": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-506-goods-origin",
        title_ru="Игнорировать производство или закупку товара поставщиком",
        facts=_facts(supplier_produced_or_procured_goods=False),
        forbidden_outcomes={"supply_contract_qualified": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-506-retail-context",
        title_ru="Квалифицировать розничную продажу как поставку",
        facts=_facts(retail_sale_context=True),
        forbidden_outcomes={"supply_contract_qualified": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-507-timely-response",
        title_ru="Взыскать убытки при своевременном ответе на разногласия",
        facts=_facts(
            disagreements_received=True,
            thirty_day_response_or_refusal=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        forbidden_outcomes={"negotiation_loss_issue": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-508-agreed-periods",
        title_ru="Подменить согласованные периоды помесячным правилом",
        facts=_facts(periodic_delivery=True, delivery_periods_agreed=True),
        forbidden_outcomes={"monthly_delivery_default": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-508-early-no-consent",
        title_ru="Разрешить досрочную поставку без согласия покупателя",
        facts=_facts(early_delivery=True),
        forbidden_outcomes={"early_delivery_permitted": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-509-complete-order",
        title_ru="Возложить убытки при надлежащей разнарядке",
        facts=_facts(
            shipment_order_required=True,
            shipment_order_timely_complete=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        forbidden_outcomes={"shipment_order_loss_issue": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-511-no-term",
        title_ru="Обязать восполнить недопоставку за пределами срока договора",
        facts=_facts(quantity_shortfall=True),
        forbidden_outcomes={"makeup_delivery_required": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-512-consented-offset",
        title_ru="Запретить согласованный ассортиментный зачет",
        facts=_facts(
            quantity_shortfall=True,
            cross_assortment_offset=True,
            buyer_consented_offset=True,
        ),
        forbidden_outcomes={"cross_assortment_offset_barred": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-513-no-notice",
        title_ru="Признать приемку надлежащей без извещения о расхождении",
        facts=_facts(
            buyer_received_goods=True,
            inspection_timely=True,
            discrepancy_found=True,
        ),
        forbidden_outcomes={"acceptance_duties_satisfied": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-514-no-preservation",
        title_ru="Взыскать расходы без сохранности товара",
        facts=_facts(
            lawful_refusal=True,
            supplier_notified=True,
            custody_expenses_documented=True,
        ),
        forbidden_outcomes={"supplier_custody_cost_liability": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-514-supplier-acted",
        title_ru="Реализовать товар после своевременного распоряжения поставщика",
        facts=_facts(
            lawful_refusal=True,
            goods_preserved=True,
            supplier_notified=True,
            supplier_disposed_reasonable_time=True,
            buyer_realized_or_returned_goods=True,
        ),
        forbidden_outcomes={"buyer_disposal_available": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-514-unlawful-no-demand",
        title_ru="Присудить оплату без требования поставщика после отказа",
        facts=_facts(unlawful_refusal=True),
        forbidden_outcomes={"supplier_payment_claim_after_unlawful_refusal": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-515-no-readiness",
        title_ru="Отказ поставщика без извещения о готовности товара",
        facts=_facts(
            buyer_selection_required=True,
            selection_due=True,
            buyer_failed_selection=True,
        ),
        forbidden_outcomes={"selection_supplier_remedy_available": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-516-buyer-paid",
        title_ru="Повторно взыскать оплату с уже исполнившего покупателя",
        facts=_facts(
            payment_due=True,
            consignee_payment_duty=True,
            consignee_failed_payment=True,
            buyer_paid=True,
        ),
        forbidden_outcomes={"buyer_payment_claim_available": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-517-not-due",
        title_ru="Признать нарушение возврата тары до срока",
        facts=_facts(returnable_container=True),
        forbidden_outcomes={"container_return_breach": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-518-prompt-replacement",
        title_ru="Игнорировать незамедлительную замену дефектного товара",
        facts=_facts(quality_defect=True, defect_promptly_cured_or_replaced=True),
        forbidden_outcomes={"quality_remedies_available": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-519-prompt-completion",
        title_ru="Игнорировать незамедлительное доукомплектование",
        facts=_facts(
            incomplete_goods=True,
            incompleteness_promptly_cured_or_replaced=True,
        ),
        forbidden_outcomes={"completeness_remedies_available": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-520-undocumented-cover",
        title_ru="Взыскать недоказанные расходы на заменяющую закупку",
        facts=_facts(quantity_shortfall=True, buyer_acquired_substitute=True),
        forbidden_outcomes={"cover_purchase_cost_recovery": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-520-cured-quality",
        title_ru="Сохранить специальные меры после незамедлительного устранения недостатка",
        facts=_facts(
            quality_defect=True,
            defect_promptly_cured_or_replaced=True,
            buyer_acquired_substitute=True,
            substitute_expenses_reasonable_documented=True,
            payment_withheld=True,
        ),
        forbidden_outcomes={
            "cover_purchase_cost_recovery": True,
            "payment_withholding_available": True,
        },
    ),
    SupplyRedTeamCase(
        id="supply-red-520-shortfall-withholding",
        title_ru="Распространить специальное удержание оплаты на одну лишь недопоставку",
        facts=_facts(quantity_shortfall=True, payment_withheld=True),
        forbidden_outcomes={"payment_withholding_available": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-521-replenished",
        title_ru="Продолжить неустойку после фактического восполнения",
        facts=_facts(
            quantity_shortfall=True,
            penalty_applies_to_short_or_late=True,
            replenishment_duty_continues=True,
            actual_replenishment_completed=True,
        ),
        forbidden_outcomes={"penalty_continues_until_replenishment": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-522-designated",
        title_ru="Применить очередность закона вопреки обозначению стороны",
        facts=_facts(
            multiple_supply_contracts=True,
            performance_allocation_designated=True,
        ),
        forbidden_outcomes={"default_contract_allocation_required": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-523-single-delay",
        title_ru="Считать единичную просрочку презюмируемо существенной",
        facts=_facts(delivery_late=True, unilateral_refusal_notice_delivered=True),
        forbidden_outcomes={"supply_unilateral_refusal_effective": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-523-curable-defect",
        title_ru="Отказаться от договора из-за устранимого недостатка",
        facts=_facts(quality_defect=True, unilateral_refusal_notice_delivered=True),
        forbidden_outcomes={"supplier_material_breach": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-523-no-notice",
        title_ru="Признать односторонний отказ без доставленного уведомления",
        facts=_facts(delivery_late=True, repeated_late_delivery=True),
        forbidden_outcomes={"supply_unilateral_refusal_effective": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-524-no-termination",
        title_ru="Рассчитать специальную ценовую разницу без прекращения договора",
        facts=_facts(loss_claimed=True, causation_proven=True),
        forbidden_outcomes={"abstract_current_price_damages_available": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-524-unreasonable-transaction",
        title_ru="Принять неразумную заменяющую сделку",
        facts=_facts(
            contract_terminated=True,
            replacement_transaction_made=True,
            contract_price_proven=True,
            replacement_price_proven=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        forbidden_outcomes={"concrete_price_damages_available": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-524-untimely-transaction",
        title_ru="Принять заменяющую сделку вне разумного срока",
        facts=_facts(
            contract_terminated=True,
            replacement_transaction_made=True,
            replacement_transaction_reasonable=True,
            contract_price_proven=True,
            replacement_price_proven=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        forbidden_outcomes={"concrete_price_damages_available": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-524-missing-current-price",
        title_ru="Рассчитать абстрактные убытки без доказанной текущей цены",
        facts=_facts(
            contract_terminated=True,
            contract_price_proven=True,
            current_price_available=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        forbidden_outcomes={"abstract_current_price_damages_available": True},
    ),
    SupplyRedTeamCase(
        id="supply-red-524-unadjusted-current-price",
        title_ru="Использовать текущую цену без привязки ко времени и месту",
        facts=_facts(
            contract_terminated=True,
            contract_price_proven=True,
            current_price_available=True,
            current_price_proven=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        forbidden_outcomes={"abstract_current_price_damages_available": True},
    ),
)


def _evaluate(facts: SupplyFactSet, artifact_id: str) -> SupplyEvaluation:
    mapping = SupplyEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="evaluation",
        mapping_version="evaluation",
        facts=facts,
        legal_source_refs=["synthetic-supply-law"],
    )
    constraint_set = build_supply_constraint_set(mapping)
    return evaluate_supply_constraints(constraint_set, facts)


def _outcomes(evaluation: SupplyEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: getattr(evaluation, name) for name in names}


def run_supply_benchmark_suite() -> SupplyBenchmarkReport:
    results = []
    for task in SYNTHETIC_SUPPLY_ARTICLES_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            SupplyEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return SupplyBenchmarkReport(
        total=len(results), passed=passed, failed=len(results) - passed, results=results
    )


def run_supply_red_team_suite() -> SupplyRedTeamReport:
    results = []
    for case in SYNTHETIC_SUPPLY_ARTICLES_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = observed != case.forbidden_outcomes
        results.append(
            SupplyRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return SupplyRedTeamReport(
        total=len(results), blocked=blocked, unblocked=len(results) - blocked, results=results
    )
