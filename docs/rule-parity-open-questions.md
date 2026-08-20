# Условия, которые объявляли, а система не проверяет

Сверка объявленного правила с исполняемым закрыта: расхождений ноль, объявленный
текст переписан по тому, что действительно считается. При этом из объявленного
исчезли имена, которым в модели не нашлось соответствия. Стереть их молча нельзя:
каждое — либо описка, либо условие, которое кто-то счёл нужным и которое так и не
реализовали. Второе решает юрист, и здесь оно вынесено вопросом, а не выводом.

Имена, оказавшиеся сокращением существующего факта (`concluded` при
`contract_concluded`, `creditor_consent` при `creditor_consented_debt_transfer`),
в список не попали: их 111, и они не несут содержания.

Осталось имён без соответствия: 40.

Список — вопросы, а не дефекты: сверка не знает права и не берётся судить,
должно ли условие быть в модели. Она знает только, что его там нет.

## Купля-продажа, статьи 454–491

**`eviction_remedy`** — объявлялось так:

```
eviction_remedy == withdrawal_on_pretransfer_ground AND NOT buyer_knowledge AND NOT preventable_procedure_gap
```

В модели нет: `buyer_knowledge`, `preventable_procedure_gap`, `withdrawal_on_pretransfer_ground`.

**`installment_refusal`** — объявлялось так:

```
installment_refusal == installment_default AND seller_refusal AND NOT more_than_half_paid
```

В модели нет: `installment_default`, `more_than_half_paid`.

**`notice_defense`** — объявлялось так:

```
notice_defense == late_notice AND proven_prejudice AND NOT seller_knowledge
```

В модели нет: `late_notice`.

**`quality_remedy`** — объявлялось так:

```
quality_remedy == defect AND timely_claim AND applicable_causation_burden
```

В модели нет: `applicable_causation_burden`.

**`sale_contract`** — объявлялось так:

```
sale_contract == concluded AND transfer_ownership_duty AND acceptance_duty AND payment_duty AND goods_subject AND name AND quantity
```

В модели нет: `goods_subject`.

**`sale_refusal`** — объявлялось так:

```
sale_refusal == statutory_refusal_ground AND delivered_notice
```

В модели нет: `statutory_refusal_ground`.

**`title_return`** — объявлялось так:

```
title_return == retained_title AND unmet_condition AND seller_return_demand
```

В модели нет: `retained_title`, `unmet_condition`.

**`transfer_duty`** — объявлялось так:

```
transfer_duty == completed AND (delivery OR availability OR carrier_handover)
```

В модели нет: `availability`.

## Поставка, статьи 506–524

**`article_520_cover`** — объявлялось так:

```
article_520_cover == unremedied_nonconformity AND substitute_purchase AND documented_expenses
```

В модели нет: `substitute_purchase`, `unremedied_nonconformity`.

**`article_520_withholding`** — объявлялось так:

```
article_520_withholding == unremedied_quality_or_completeness AND payment_withheld
```

В модели нет: `unremedied_quality_or_completeness`.

**`negotiation_response_breach`** — объявлялось так:

```
negotiation_response_breach == disagreements_received AND NOT timely_response_or_refusal
```

В модели нет: `timely_response_or_refusal`.

## Исполнение и средства защиты, статьи 309–328 и 393–406.1

**`counterperformance_suspension`** — объявлялось так:

```
counterperformance_suspension == reciprocal_due AND nonperformance_risk AND delivered_notice
```

В модели нет: `nonperformance_risk`.

**`damages`** — объявлялось так:

```
damages == breach AND claimed_loss AND proven_loss_type AND causation AND reasonable_amount_basis
```

В модели нет: `proven_loss_type`.

**`indemnity`** — объявлялось так:

```
indemnity == business_agreement AND clear_nonbreach_trigger AND occurred_loss AND amount_method AND NOT bad_faith
```

В модели нет: `business_agreement`, `clear_nonbreach_trigger`.

**`proper_performance`** — объявлялось так:

```
proper_performance == obligation_exists AND tendered AND conforming_subject_quality_quantity_time_place_recipient
```

В модели нет: `conforming_subject_quality_quantity_time_place_recipient`.

**`third_party_acceptance`** — объявлялось так:

```
third_party_acceptance == third_party_tendered AND statutory_acceptance_ground AND NOT personal_performance
```

В модели нет: `statutory_acceptance_ground`.

## Перемена лиц и прекращение обязательств, статьи 382–419

**`assignment_effective`** — объявлялось так:

```
assignment_effective == obligation_exists AND assignment_agreement AND form AND identifiable_claim AND transferable_claim AND required_consent
```

В модели нет: `transferable_claim`.

**`contract_transfer_effective`** — объявлялось так:

```
contract_transfer_effective == obligation_exists AND contract_transfer_agreed AND all_parties_consent AND required_forms
```

В модели нет: `required_forms`.

**`debt_forgiveness_effective`** — объявлялось так:

```
debt_forgiveness_effective == obligation_exists AND forgiveness_notice AND NOT objection AND NOT third_party_prejudice AND NOT commercial_gift_bar
```

В модели нет: `commercial_gift_bar`.

**`notary_deposit_discharge`** — объявлялось так:

```
notary_deposit_discharge == obligation_exists AND deposit_made AND statutory_deposit_ground
```

В модели нет: `statutory_deposit_ground`.

**`novation_effective`** — объявлялось так:

```
novation_effective == obligation_exists AND agreement AND clear_replacement_intent AND new_subject_or_basis AND new_terms AND form
```

В модели нет: `clear_replacement_intent`.

**`setoff_effective`** — объявлялось так:

```
setoff_effective == obligation_exists AND declaration_delivered AND mutual_homogeneous_due_claims AND amount_proven AND NOT bar
```

В модели нет: `bar`, `declaration_delivered`, `mutual_homogeneous_due_claims`.

## Обеспечение исполнения, статьи 329–381.2

**`accessory_security_displaced_by_main_invalidity`** — объявлялось так:

```
accessory_security_displaced_by_main_invalidity == main_obligation_invalid AND accessory_security_created
```

В модели нет: `accessory_security_created`.

**`guarantee_demand_payable`** — объявлялось так:

```
guarantee_demand_payable == effective_independent_guarantee AND timely_compliant_demand AND NOT abuse
```

В модели нет: `effective_independent_guarantee`, `timely_compliant_demand`.

**`penalty_security_enforceable`** — объявлялось так:

```
penalty_security_enforceable == valid_main_obligation AND breach AND written_penalty AND trigger
```

В модели нет: `valid_main_obligation`.

**`pledge_foreclosure_prerequisites`** — объявлялось так:

```
pledge_foreclosure_prerequisites == pledge_valid_between_parties AND breach AND foreclosure_ground AND amount_proven AND NOT bar
```

В модели нет: `bar`.

**`pledge_valid_between_parties`** — объявлялось так:

```
pledge_valid_between_parties == valid_main_obligation AND pledge_created AND form AND asset AND authority
```

В модели нет: `authority`, `valid_main_obligation`.

**`security_payment_credit_available`** — объявлялось так:

```
security_payment_credit_available == active_security_payment AND secured_event
```

В модели нет: `secured_event`.

**`surety_enforceable`** — объявлялось так:

```
surety_enforceable == valid_main_obligation AND written_surety AND scope AND NOT terminated
```

В модели нет: `valid_main_obligation`.

## Изменение и расторжение договора, статьи 450–453

**`judicial_termination_prerequisites`** — объявлялось так:

```
judicial_termination_prerequisites == contract_formed AND judicial_request_targets_termination AND pretrial_order_satisfied AND judicial_ground
```

В модели нет: `judicial_ground`.

