from pydantic import BaseModel, Field

from causa.institutional.contracts.sale import (
    SaleEvaluation,
    SaleEvidenceMappingResult,
    SaleFactSet,
    build_sale_constraint_set,
    evaluate_sale_constraints,
)


class SaleEvaluationTask(BaseModel):
    id: str
    title_ru: str
    facts: SaleFactSet
    expected_outcomes: dict[str, bool]


class SaleEvaluationResult(BaseModel):
    task_id: str
    passed: bool
    expected_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SaleBenchmarkReport(BaseModel):
    id: str = "sale-articles-454-491-benchmark-report-v0"
    total: int
    passed: int
    failed: int
    results: list[SaleEvaluationResult] = Field(default_factory=list)


class SaleRedTeamCase(BaseModel):
    id: str
    title_ru: str
    facts: SaleFactSet
    forbidden_outcomes: dict[str, bool]


class SaleRedTeamResult(BaseModel):
    case_id: str
    blocked: bool
    forbidden_outcomes: dict[str, bool]
    observed_outcomes: dict[str, bool]
    reasons_ru: list[str] = Field(default_factory=list)


class SaleRedTeamReport(BaseModel):
    id: str = "sale-articles-454-491-red-team-report-v0"
    total: int
    blocked: int
    unblocked: int
    results: list[SaleRedTeamResult] = Field(default_factory=list)


def _facts(**updates: bool) -> SaleFactSet:
    values = {field_name: False for field_name in SaleFactSet.model_fields}
    values.update(
        contract_concluded=True,
        seller_transfer_ownership_duty=True,
        buyer_acceptance_duty=True,
        buyer_payment_duty=True,
        goods_existing_or_future=True,
        goods_name_agreed=True,
        quantity_determinable=True,
    )
    values.update(updates)
    return SaleFactSet(**values)


SYNTHETIC_SALE_ARTICLES_BENCHMARKS = (
    SaleEvaluationTask(
        id="sale-bench-454-qualified",
        title_ru="Квалифицирующие признаки договора купли-продажи",
        facts=_facts(),
        expected_outcomes={"sale_contract_qualified": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-454-property-right",
        title_ru="Применение правил купли-продажи к имущественному праву",
        facts=_facts(property_right_subject=True),
        expected_outcomes={"property_right_sale_rules_applicable": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-456-transfer-package",
        title_ru="Передача товара, принадлежностей и документов",
        facts=_facts(
            goods_transfer_completed=True,
            delivery_obligation=True,
            goods_delivered_to_buyer=True,
            accessories_required=True,
            accessories_transferred=True,
            documents_required=True,
            documents_transferred=True,
        ),
        expected_outcomes={
            "transfer_package_complete": True,
            "transfer_duty_performed": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-457-fixed-term",
        title_ru="Просрочка договора к строго определенному сроку",
        facts=_facts(
            transfer_term_due=True,
            delivery_late=True,
            fixed_term_contract=True,
            buyer_interest_lost_after_term=True,
        ),
        expected_outcomes={"late_fixed_term_transfer_requires_consent": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-458-availability",
        title_ru="Предоставление товара в распоряжение покупателя",
        facts=_facts(goods_transfer_completed=True, goods_made_available=True),
        expected_outcomes={"transfer_duty_performed": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-458-carrier",
        title_ru="Исполнение обязанностью сдачей товара перевозчику",
        facts=_facts(
            goods_transfer_completed=True,
            shipment_contract=True,
            goods_handed_to_carrier=True,
        ),
        expected_outcomes={"transfer_duty_performed": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-459-default-risk",
        title_ru="Переход риска по общему правилу",
        facts=_facts(
            goods_transfer_completed=True,
            delivery_obligation=True,
            goods_delivered_to_buyer=True,
        ),
        expected_outcomes={"risk_passed_by_default": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-459-contract-risk",
        title_ru="Договорное распределение риска",
        facts=_facts(risk_allocation_agreed=True, risk_passed_by_agreement=True),
        expected_outcomes={"risk_passed_by_contract": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-459-transit-loss",
        title_ru="Оспаривание условия о риске при известной продавцу утрате",
        facts=_facts(goods_sold_in_transit=True, seller_knew_transit_loss=True),
        expected_outcomes={"transit_risk_clause_challenge": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-459-transit-default",
        title_ru="Переход риска при продаже товара в пути",
        facts=_facts(goods_sold_in_transit=True),
        expected_outcomes={"transit_risk_passed_at_conclusion": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-460-third-party-rights",
        title_ru="Несогласованные права третьих лиц на товар",
        facts=_facts(third_party_rights_exist=True),
        expected_outcomes={"third_party_rights_breach": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-461-eviction",
        title_ru="Убытки при изъятии товара по прежнему основанию",
        facts=_facts(
            third_party_rights_exist=True,
            goods_withdrawn_by_third_party=True,
            withdrawal_ground_predates_transfer=True,
            seller_eviction_exclusion_agreement=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        expected_outcomes={
            "eviction_loss_remedy_available": True,
            "eviction_exclusion_ineffective": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-462-procedure-gap",
        title_ru="Непривлечение продавца к делу об эвикции",
        facts=_facts(third_party_eviction_claim_filed=True),
        expected_outcomes={"buyer_eviction_procedure_gap": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-462-seller-default",
        title_ru="Неучастие извещенного продавца в деле об эвикции",
        facts=_facts(
            third_party_eviction_claim_filed=True,
            buyer_joined_seller_to_eviction_case=True,
        ),
        expected_outcomes={"seller_eviction_defense_barred": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-463-specific-performance",
        title_ru="Требование передачи индивидуально-определенной вещи",
        facts=_facts(
            seller_refused_goods_transfer=True,
            individually_defined_goods=True,
            specific_performance_requested=True,
        ),
        expected_outcomes={
            "goods_transfer_refusal_remedy_available": True,
            "specific_performance_available": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-463-contract-refusal",
        title_ru="Отказ покупателя при непередаче товара",
        facts=_facts(
            seller_refused_goods_transfer=True,
            buyer_chose_contract_refusal_for_nontransfer=True,
            unilateral_refusal_notice_delivered=True,
            contract_terminated=True,
        ),
        expected_outcomes={"sale_contract_refusal_effective": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-464-documents-refusal",
        title_ru="Отказ после непередачи документов в дополнительный срок",
        facts=_facts(
            goods_transfer_completed=True,
            documents_required=True,
            buyer_set_reasonable_document_term=True,
            seller_failed_document_term=True,
            buyer_refused_goods_for_documents=True,
        ),
        expected_outcomes={
            "documents_remedy_available": True,
            "documents_refusal_ground": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-466-shortfall",
        title_ru="Средства защиты при передаче меньшего количества",
        facts=_facts(quantity_shortfall=True),
        expected_outcomes={"quantity_shortfall_remedies": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-466-excess",
        title_ru="Принятие и оплата излишнего количества",
        facts=_facts(
            excess_quantity=True,
            buyer_notified_excess=True,
            buyer_accepted_excess=True,
        ),
        expected_outcomes={
            "excess_quantity_deemed_accepted": True,
            "excess_quantity_payment_due": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-467-assortment-default",
        title_ru="Выбор ассортимента по известным потребностям покупателя",
        facts=_facts(
            assortment_required=True,
            assortment_determinable_from_needs=True,
            seller_selected_assortment=True,
        ),
        expected_outcomes={"seller_assortment_choice_default": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-468-mixed-assortment",
        title_ru="Отказ от всей смешанной ассортиментной поставки",
        facts=_facts(
            assortment_nonconforming=True,
            mixed_assortment_delivery=True,
            buyer_rejected_all_mixed_goods=True,
            buyer_notified_assortment_refusal_reasonable_time=True,
        ),
        expected_outcomes={
            "assortment_remedies_available": True,
            "mixed_assortment_total_refusal_available": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-468-deemed-acceptance",
        title_ru="Принятие несоответствующего ассортимента без своевременного отказа",
        facts=_facts(assortment_nonconforming=True),
        expected_outcomes={"assortment_deemed_accepted": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-469-quality-default",
        title_ru="Определение качества по обычной цели использования",
        facts=_facts(ordinary_purpose_known=True),
        expected_outcomes={"quality_standard_requires_general_default": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-475-ordinary-defect",
        title_ru="Обычные средства защиты при недостатке товара",
        facts=_facts(
            quality_defect=True,
            buyer_proved_pretransfer_defect_cause=True,
            defect_discovered_within_applicable_period=True,
            buyer_chose_free_repair=True,
        ),
        expected_outcomes={"quality_remedies_available": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-475-material-defect",
        title_ru="Замена при существенном недостатке товара",
        facts=_facts(
            quality_defect=True,
            defect_material=True,
            buyer_proved_pretransfer_defect_cause=True,
            defect_discovered_within_applicable_period=True,
            buyer_chose_replacement=True,
        ),
        expected_outcomes={"material_defect_remedies_available": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-476-warranty-burden",
        title_ru="Бремя продавца в пределах гарантийного срока",
        facts=_facts(
            quality_defect=True,
            seller_warranty_given=True,
            warranty_period_active=True,
            defect_discovered_within_applicable_period=True,
            buyer_chose_free_repair=True,
        ),
        expected_outcomes={
            "warranty_seller_burden_applies": True,
            "quality_remedies_available": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-472-shelf-life",
        title_ru="Передача товара без достаточного остатка срока годности",
        facts=_facts(goods_transfer_completed=True, shelf_life_set=True),
        expected_outcomes={"shelf_life_transfer_breach": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-474-inspection",
        title_ru="Пробел обязательной проверки качества",
        facts=_facts(inspection_required=True, buyer_received_goods=True),
        expected_outcomes={"quality_inspection_gap": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-480-completeness-primary",
        title_ru="Первичное требование о доукомплектовании",
        facts=_facts(incomplete_goods=True, buyer_requested_completion=True),
        expected_outcomes={"completeness_primary_remedies": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-480-completeness-secondary",
        title_ru="Замена после неисполненного требования о доукомплектовании",
        facts=_facts(
            incomplete_goods=True,
            buyer_requested_completion=True,
            buyer_requested_complete_replacement=True,
        ),
        expected_outcomes={"completeness_secondary_remedies": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-479-set",
        title_ru="Неполная передача согласованного комплекта товаров",
        facts=_facts(set_of_goods_agreed=True, transfer_term_due=True),
        expected_outcomes={"set_delivery_breach": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-482-packaging",
        title_ru="Требование надлежащей упаковки",
        facts=_facts(
            goods_transfer_completed=True,
            packaging_required=True,
            buyer_requested_packaging=True,
        ),
        expected_outcomes={"packaging_remedies_available": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-483-notice-defense",
        title_ru="Возражение продавца из несвоевременного извещения",
        facts=_facts(discrepancy_found=True, seller_proved_notice_prejudice=True),
        expected_outcomes={"notice_defense_available": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-483-seller-knowledge",
        title_ru="Недопустимость возражения при осведомленности продавца",
        facts=_facts(
            discrepancy_found=True,
            seller_knew_or_should_have_known_discrepancy=True,
        ),
        expected_outcomes={"notice_defense_displaced_by_seller_knowledge": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-484-acceptance",
        title_ru="Средства продавца при уклонении от принятия товара",
        facts=_facts(buyer_failed_acceptance=True, seller_demanded_acceptance=True),
        expected_outcomes={
            "buyer_acceptance_breach": True,
            "seller_nonacceptance_remedies": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-485-price-default",
        title_ru="Определение цены по общему правилу",
        facts=_facts(),
        expected_outcomes={"price_general_default_required": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-485-net-weight",
        title_ru="Расчет цены по весу нетто",
        facts=_facts(price_based_on_weight=True, net_weight_proven=True),
        expected_outcomes={"net_weight_price_controls": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-485-price-revision",
        title_ru="Недоказанные показатели договорного пересмотра цены",
        facts=_facts(price_revision_formula_agreed=True),
        expected_outcomes={"price_revision_requires_review": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-486-payment",
        title_ru="Просрочка непосредственной оплаты товара",
        facts=_facts(payment_due=True, seller_demanded_payment=True),
        expected_outcomes={
            "payment_default": True,
            "seller_payment_remedies": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-487-prepayment-default",
        title_ru="Просрочка предварительной оплаты покупателем",
        facts=_facts(prepayment_required=True, prepayment_due=True),
        expected_outcomes={"prepayment_default": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-487-prepaid-buyer",
        title_ru="Возврат предоплаты при непередаче товара",
        facts=_facts(
            prepayment_required=True,
            prepayment_made=True,
            seller_failed_after_prepayment=True,
            buyer_requested_prepayment_return=True,
        ),
        expected_outcomes={"prepaid_buyer_remedies": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-488-credit",
        title_ru="Требования продавца при неоплате товара в кредит",
        facts=_facts(
            credit_sale=True,
            credit_payment_due=True,
            seller_demanded_credit_payment_or_return=True,
            seller_security_interest_applies=True,
        ),
        expected_outcomes={
            "credit_payment_default": True,
            "credit_seller_remedies": True,
            "credit_goods_security_active": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-489-installment-terms",
        title_ru="Пробел существенных условий рассрочки",
        facts=_facts(installment_sale=True),
        expected_outcomes={"installment_terms_gap": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-489-installment-refusal",
        title_ru="Отказ продавца при просрочке очередного платежа",
        facts=_facts(
            installment_sale=True,
            installment_essential_terms_complete=True,
            installment_payment_due=True,
            seller_chose_installment_refusal=True,
        ),
        expected_outcomes={"installment_refusal_available": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-489-half-payment",
        title_ru="Запрет отказа после оплаты более половины цены",
        facts=_facts(
            installment_sale=True,
            installment_essential_terms_complete=True,
            installment_payment_due=True,
            paid_amount_exceeds_half_price=True,
            seller_chose_installment_refusal=True,
        ),
        expected_outcomes={"installment_refusal_barred_by_half_payment": True},
    ),
    SaleEvaluationTask(
        id="sale-bench-490-insurance",
        title_ru="Самостоятельное страхование и отказ при нарушении обязанности",
        facts=_facts(
            insurance_duty_allocated=True,
            insurance_duty_due=True,
            counterparty_insured_goods=True,
            counterparty_chose_insurance_refusal=True,
        ),
        expected_outcomes={
            "insurance_breach": True,
            "insurance_self_help_available": True,
            "insurance_refusal_available": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-491-title-retention",
        title_ru="Возврат товара при сохранении права собственности",
        facts=_facts(
            title_retention_agreed=True,
            buyer_disposed_before_title=True,
            seller_required_goods_return=True,
        ),
        expected_outcomes={
            "title_disposal_bar": True,
            "title_return_remedy": True,
        },
    ),
    SaleEvaluationTask(
        id="sale-bench-refusal-effective",
        title_ru="Доставленный отказ из-за существенного недостатка",
        facts=_facts(
            quality_defect=True,
            defect_material=True,
            buyer_proved_pretransfer_defect_cause=True,
            defect_discovered_within_applicable_period=True,
            buyer_chose_contract_refusal_for_defect=True,
            unilateral_refusal_notice_delivered=True,
            contract_terminated=True,
        ),
        expected_outcomes={"sale_contract_refusal_effective": True},
    ),
)


SYNTHETIC_SALE_ARTICLES_RED_TEAM_CASES = (
    SaleRedTeamCase(
        id="sale-red-455-no-quantity",
        title_ru="Признать договор заключенным без определимого количества",
        facts=_facts(quantity_determinable=False),
        forbidden_outcomes={"sale_contract_qualified": True},
    ),
    SaleRedTeamCase(
        id="sale-red-455-no-name",
        title_ru="Признать договор заключенным без наименования товара",
        facts=_facts(goods_name_agreed=False),
        forbidden_outcomes={"sale_contract_qualified": True},
    ),
    SaleRedTeamCase(
        id="sale-red-454-right-nature",
        title_ru="Применить правила продажи вопреки природе имущественного права",
        facts=_facts(
            property_right_subject=True,
            property_right_nature_excludes_sale_rules=True,
        ),
        forbidden_outcomes={"property_right_sale_rules_applicable": True},
    ),
    SaleRedTeamCase(
        id="sale-red-456-missing-documents",
        title_ru="Признать пакет передачи полным без обязательных документов",
        facts=_facts(goods_transfer_completed=True, documents_required=True),
        forbidden_outcomes={"transfer_package_complete": True},
    ),
    SaleRedTeamCase(
        id="sale-red-457-buyer-consent",
        title_ru="Игнорировать согласие покупателя на просроченную передачу",
        facts=_facts(
            transfer_term_due=True,
            delivery_late=True,
            fixed_term_contract=True,
            buyer_interest_lost_after_term=True,
            buyer_consented_late_transfer=True,
        ),
        forbidden_outcomes={"late_fixed_term_transfer_requires_consent": True},
    ),
    SaleRedTeamCase(
        id="sale-red-458-no-route",
        title_ru="Признать передачу исполненной без применимого способа",
        facts=_facts(goods_transfer_completed=True),
        forbidden_outcomes={"transfer_duty_performed": True},
    ),
    SaleRedTeamCase(
        id="sale-red-459-agreed-risk",
        title_ru="Применить общий переход риска вопреки соглашению",
        facts=_facts(
            goods_transfer_completed=True,
            delivery_obligation=True,
            goods_delivered_to_buyer=True,
            risk_allocation_agreed=True,
        ),
        forbidden_outcomes={"risk_passed_by_default": True},
    ),
    SaleRedTeamCase(
        id="sale-red-459-risk-not-passed",
        title_ru="Признать договорный риск перешедшим без соответствующего факта",
        facts=_facts(risk_allocation_agreed=True),
        forbidden_outcomes={"risk_passed_by_contract": True},
    ),
    SaleRedTeamCase(
        id="sale-red-459-disclosed-loss",
        title_ru="Оспорить риск после раскрытия утраты продавцом",
        facts=_facts(
            goods_sold_in_transit=True,
            seller_knew_transit_loss=True,
            seller_disclosed_transit_loss=True,
        ),
        forbidden_outcomes={"transit_risk_clause_challenge": True},
    ),
    SaleRedTeamCase(
        id="sale-red-459-transit-agreement",
        title_ru="Применить риск момента заключения вопреки соглашению сторон",
        facts=_facts(goods_sold_in_transit=True, risk_allocation_agreed=True),
        forbidden_outcomes={"transit_risk_passed_at_conclusion": True},
    ),
    SaleRedTeamCase(
        id="sale-red-460-consented-rights",
        title_ru="Считать согласованное обременение нарушением",
        facts=_facts(
            third_party_rights_exist=True,
            buyer_consented_third_party_rights=True,
        ),
        forbidden_outcomes={"third_party_rights_breach": True},
    ),
    SaleRedTeamCase(
        id="sale-red-461-buyer-knew",
        title_ru="Возместить убытки при известном покупателю основании эвикции",
        facts=_facts(
            third_party_rights_exist=True,
            goods_withdrawn_by_third_party=True,
            withdrawal_ground_predates_transfer=True,
            buyer_knew_withdrawal_ground=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        forbidden_outcomes={"eviction_loss_remedy_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-462-preventable-withdrawal",
        title_ru="Игнорировать доказанную возможность продавца предотвратить эвикцию",
        facts=_facts(
            third_party_rights_exist=True,
            goods_withdrawn_by_third_party=True,
            withdrawal_ground_predates_transfer=True,
            third_party_eviction_claim_filed=True,
            seller_could_prevent_withdrawal=True,
            loss_claimed=True,
            causation_proven=True,
        ),
        forbidden_outcomes={"eviction_loss_remedy_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-462-seller-participated",
        title_ru="Лишить участвовавшего продавца процессуального возражения",
        facts=_facts(
            third_party_eviction_claim_filed=True,
            buyer_joined_seller_to_eviction_case=True,
            seller_participated_in_eviction_case=True,
        ),
        forbidden_outcomes={"seller_eviction_defense_barred": True},
    ),
    SaleRedTeamCase(
        id="sale-red-463-generic-goods",
        title_ru="Требовать конкретную вещь без индивидуальной определенности",
        facts=_facts(seller_refused_goods_transfer=True),
        forbidden_outcomes={"specific_performance_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-464-no-additional-term",
        title_ru="Отказаться из-за документов без дополнительного срока",
        facts=_facts(
            goods_transfer_completed=True,
            documents_required=True,
            seller_failed_document_term=True,
            buyer_refused_goods_for_documents=True,
        ),
        forbidden_outcomes={"documents_refusal_ground": True},
    ),
    SaleRedTeamCase(
        id="sale-red-466-no-shortfall",
        title_ru="Активировать количественные средства без недостачи",
        facts=_facts(),
        forbidden_outcomes={"quantity_shortfall_remedies": True},
    ),
    SaleRedTeamCase(
        id="sale-red-466-seller-disposed",
        title_ru="Считать излишек принятым после распоряжения продавца",
        facts=_facts(
            excess_quantity=True,
            buyer_notified_excess=True,
            seller_disposed_excess_reasonable_time=True,
            buyer_accepted_excess=True,
        ),
        forbidden_outcomes={"excess_quantity_deemed_accepted": True},
    ),
    SaleRedTeamCase(
        id="sale-red-467-agreed-assortment",
        title_ru="Применить выбор продавца при согласованном ассортименте",
        facts=_facts(
            assortment_required=True,
            assortment_agreed=True,
            assortment_determinable_from_needs=True,
            seller_selected_assortment=True,
        ),
        forbidden_outcomes={"seller_assortment_choice_default": True},
    ),
    SaleRedTeamCase(
        id="sale-red-468-timely-refusal",
        title_ru="Считать ассортимент принятым при своевременном отказе",
        facts=_facts(
            assortment_nonconforming=True,
            buyer_notified_assortment_refusal_reasonable_time=True,
        ),
        forbidden_outcomes={"assortment_deemed_accepted": True},
    ),
    SaleRedTeamCase(
        id="sale-red-468-no-mixed-delivery",
        title_ru="Разрешить полный отказ без смешанной передачи",
        facts=_facts(
            assortment_nonconforming=True,
            buyer_rejected_all_mixed_goods=True,
        ),
        forbidden_outcomes={"mixed_assortment_total_refusal_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-468-late-total-refusal",
        title_ru="Разрешить полный отказ от смешанной передачи без своевременного извещения",
        facts=_facts(
            assortment_nonconforming=True,
            mixed_assortment_delivery=True,
            buyer_rejected_all_mixed_goods=True,
        ),
        forbidden_outcomes={"mixed_assortment_total_refusal_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-475-no-causation",
        title_ru="Активировать качество без доказанного момента причины",
        facts=_facts(
            quality_defect=True,
            defect_discovered_within_applicable_period=True,
            buyer_chose_free_repair=True,
        ),
        forbidden_outcomes={"quality_remedies_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-476-post-transfer-cause",
        title_ru="Игнорировать доказанную продавцом послепередаточную причину",
        facts=_facts(
            quality_defect=True,
            seller_warranty_given=True,
            warranty_period_active=True,
            seller_proved_posttransfer_defect_cause=True,
            defect_discovered_within_applicable_period=True,
            buyer_chose_free_repair=True,
        ),
        forbidden_outcomes={"quality_remedies_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-475-nonmaterial",
        title_ru="Применить замену как последствие существенного недостатка без существенности",
        facts=_facts(
            quality_defect=True,
            buyer_proved_pretransfer_defect_cause=True,
            defect_discovered_within_applicable_period=True,
            buyer_chose_replacement=True,
        ),
        forbidden_outcomes={"material_defect_remedies_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-477-out-of-time",
        title_ru="Применить требования вне срока обнаружения недостатка",
        facts=_facts(
            quality_defect=True,
            buyer_proved_pretransfer_defect_cause=True,
            buyer_chose_free_repair=True,
        ),
        forbidden_outcomes={"quality_remedies_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-472-usable-shelf-life",
        title_ru="Считать надлежащий остаток срока годности нарушением",
        facts=_facts(
            goods_transfer_completed=True,
            shelf_life_set=True,
            goods_transferred_with_usable_shelf_life=True,
        ),
        forbidden_outcomes={"shelf_life_transfer_breach": True},
    ),
    SaleRedTeamCase(
        id="sale-red-472-before-transfer",
        title_ru="Считать срок годности нарушенным до передачи товара",
        facts=_facts(shelf_life_set=True),
        forbidden_outcomes={"shelf_life_transfer_breach": True},
    ),
    SaleRedTeamCase(
        id="sale-red-474-compliant-inspection",
        title_ru="Фиксировать пробел при надлежащей проверке качества",
        facts=_facts(
            inspection_required=True,
            buyer_received_goods=True,
            inspection_timely=True,
            inspection_method_complied=True,
        ),
        forbidden_outcomes={"quality_inspection_gap": True},
    ),
    SaleRedTeamCase(
        id="sale-red-480-completed",
        title_ru="Активировать вторичные меры после своевременного доукомплектования",
        facts=_facts(
            incomplete_goods=True,
            buyer_requested_completion=True,
            seller_completed_reasonable_time=True,
            buyer_requested_complete_replacement=True,
        ),
        forbidden_outcomes={"completeness_secondary_remedies": True},
    ),
    SaleRedTeamCase(
        id="sale-red-479-complete-set",
        title_ru="Считать полный комплект нарушением",
        facts=_facts(
            set_of_goods_agreed=True,
            transfer_term_due=True,
            set_transfer_complete=True,
        ),
        forbidden_outcomes={"set_delivery_breach": True},
    ),
    SaleRedTeamCase(
        id="sale-red-479-set-before-due",
        title_ru="Считать комплект нарушенным до наступления срока передачи",
        facts=_facts(set_of_goods_agreed=True),
        forbidden_outcomes={"set_delivery_breach": True},
    ),
    SaleRedTeamCase(
        id="sale-red-482-conforming-packaging",
        title_ru="Активировать меры при надлежащей упаковке",
        facts=_facts(
            goods_transfer_completed=True,
            packaging_required=True,
            packaging_transferred=True,
            packaging_conforming=True,
        ),
        forbidden_outcomes={"packaging_remedies_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-482-before-transfer",
        title_ru="Активировать последствия упаковки до передачи товара",
        facts=_facts(packaging_required=True, buyer_requested_packaging=True),
        forbidden_outcomes={"packaging_remedies_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-483-prompt-notice",
        title_ru="Разрешить возражение при своевременном извещении",
        facts=_facts(
            discrepancy_found=True,
            prompt_notice_given=True,
            seller_proved_notice_prejudice=True,
        ),
        forbidden_outcomes={"notice_defense_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-483-seller-knowledge",
        title_ru="Разрешить возражение осведомленному продавцу",
        facts=_facts(
            discrepancy_found=True,
            seller_knew_or_should_have_known_discrepancy=True,
            seller_proved_notice_prejudice=True,
        ),
        forbidden_outcomes={"notice_defense_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-484-accepted",
        title_ru="Считать покупателя уклонившимся после принятия товара",
        facts=_facts(buyer_received_goods=True, buyer_acceptance_completed=True),
        forbidden_outcomes={"buyer_acceptance_breach": True},
    ),
    SaleRedTeamCase(
        id="sale-red-485-determinable-price",
        title_ru="Применить общую цену при договорном порядке определения",
        facts=_facts(price_determinable=True),
        forbidden_outcomes={"price_general_default_required": True},
    ),
    SaleRedTeamCase(
        id="sale-red-485-no-net-proof",
        title_ru="Рассчитать весовую цену без веса нетто",
        facts=_facts(price_based_on_weight=True),
        forbidden_outcomes={"net_weight_price_controls": True},
    ),
    SaleRedTeamCase(
        id="sale-red-485-proven-revision",
        title_ru="Направить на проверку полностью доказанный пересмотр цены",
        facts=_facts(
            price_revision_formula_agreed=True,
            price_revision_inputs_proven=True,
        ),
        forbidden_outcomes={"price_revision_requires_review": True},
    ),
    SaleRedTeamCase(
        id="sale-red-486-paid",
        title_ru="Зафиксировать просрочку после оплаты",
        facts=_facts(payment_due=True, buyer_paid=True, seller_demanded_payment=True),
        forbidden_outcomes={"payment_default": True},
    ),
    SaleRedTeamCase(
        id="sale-red-487-prepaid",
        title_ru="Считать исполненную предоплату просроченной",
        facts=_facts(
            prepayment_required=True,
            prepayment_due=True,
            prepayment_made=True,
        ),
        forbidden_outcomes={"prepayment_default": True},
    ),
    SaleRedTeamCase(
        id="sale-red-487-seller-performed",
        title_ru="Дать средства покупателю без нарушения после предоплаты",
        facts=_facts(
            prepayment_required=True,
            prepayment_made=True,
            buyer_requested_prepaid_delivery=True,
        ),
        forbidden_outcomes={"prepaid_buyer_remedies": True},
    ),
    SaleRedTeamCase(
        id="sale-red-488-credit-paid",
        title_ru="Считать товар в кредит неоплаченным после платежа",
        facts=_facts(
            credit_sale=True,
            credit_payment_due=True,
            credit_payment_made=True,
            seller_demanded_credit_payment_or_return=True,
        ),
        forbidden_outcomes={"credit_payment_default": True},
    ),
    SaleRedTeamCase(
        id="sale-red-489-half-paid",
        title_ru="Разрешить отказ после оплаты более половины цены",
        facts=_facts(
            installment_sale=True,
            installment_essential_terms_complete=True,
            installment_payment_due=True,
            paid_amount_exceeds_half_price=True,
            seller_chose_installment_refusal=True,
        ),
        forbidden_outcomes={"installment_refusal_available": True},
    ),
    SaleRedTeamCase(
        id="sale-red-490-insured",
        title_ru="Активировать последствия при исполненной обязанности страхования",
        facts=_facts(
            insurance_duty_allocated=True,
            insurance_duty_due=True,
            insurance_obtained=True,
        ),
        forbidden_outcomes={"insurance_breach": True},
    ),
    SaleRedTeamCase(
        id="sale-red-490-not-due",
        title_ru="Считать обязанность страхования нарушенной до срока исполнения",
        facts=_facts(insurance_duty_allocated=True),
        forbidden_outcomes={"insurance_breach": True},
    ),
    SaleRedTeamCase(
        id="sale-red-491-title-passed",
        title_ru="Ограничить распоряжение после перехода права собственности",
        facts=_facts(
            title_retention_agreed=True,
            title_condition_met=True,
            buyer_disposed_before_title=True,
        ),
        forbidden_outcomes={"title_disposal_bar": True},
    ),
    SaleRedTeamCase(
        id="sale-red-491-disposal-permitted",
        title_ru="Запретить разрешенное досрочное распоряжение товаром",
        facts=_facts(
            title_retention_agreed=True,
            buyer_disposed_before_title=True,
            title_early_disposal_permitted=True,
        ),
        forbidden_outcomes={"title_disposal_bar": True},
    ),
    SaleRedTeamCase(
        id="sale-red-491-return-contract-bar",
        title_ru="Разрешить возврат вопреки условию договора",
        facts=_facts(
            title_retention_agreed=True,
            seller_required_goods_return=True,
            title_return_contract_bar=True,
        ),
        forbidden_outcomes={"title_return_remedy": True},
    ),
    SaleRedTeamCase(
        id="sale-red-refusal-no-notice",
        title_ru="Признать отказ действующим без доставленного уведомления",
        facts=_facts(
            quality_defect=True,
            defect_material=True,
            buyer_proved_pretransfer_defect_cause=True,
            defect_discovered_within_applicable_period=True,
            buyer_chose_contract_refusal_for_defect=True,
        ),
        forbidden_outcomes={"sale_contract_refusal_effective": True},
    ),
)


def _evaluate(facts: SaleFactSet, artifact_id: str) -> SaleEvaluation:
    mapping = SaleEvidenceMappingResult(
        evidence_id=artifact_id,
        schema_version="synthetic-sale-evaluation.v0",
        mapping_version="synthetic-sale-evaluation-v0",
        facts=facts,
    )
    constraint_set = build_sale_constraint_set(mapping)
    return evaluate_sale_constraints(constraint_set, facts)


def _outcomes(evaluation: SaleEvaluation, names: dict[str, bool]) -> dict[str, bool]:
    return {name: bool(getattr(evaluation, name)) for name in names}


def run_sale_benchmark_suite() -> SaleBenchmarkReport:
    results = []
    for task in SYNTHETIC_SALE_ARTICLES_BENCHMARKS:
        evaluation = _evaluate(task.facts, task.id)
        observed = _outcomes(evaluation, task.expected_outcomes)
        results.append(
            SaleEvaluationResult(
                task_id=task.id,
                passed=observed == task.expected_outcomes,
                expected_outcomes=task.expected_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    passed = sum(result.passed for result in results)
    return SaleBenchmarkReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def run_sale_red_team_suite() -> SaleRedTeamReport:
    results = []
    for case in SYNTHETIC_SALE_ARTICLES_RED_TEAM_CASES:
        evaluation = _evaluate(case.facts, case.id)
        observed = _outcomes(evaluation, case.forbidden_outcomes)
        blocked = all(
            observed[name] != forbidden for name, forbidden in case.forbidden_outcomes.items()
        )
        results.append(
            SaleRedTeamResult(
                case_id=case.id,
                blocked=blocked,
                forbidden_outcomes=case.forbidden_outcomes,
                observed_outcomes=observed,
                reasons_ru=evaluation.reasons_ru,
            )
        )
    blocked = sum(result.blocked for result in results)
    return SaleRedTeamReport(
        total=len(results),
        blocked=blocked,
        unblocked=len(results) - blocked,
        results=results,
    )
