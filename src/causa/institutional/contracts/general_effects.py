"""Слой применения общих положений ГК РФ к выводам специальных институтов.

В отличие от институциональных моделей пакета, этот слой не принимает
отдельный проверенный контракт данных: его входы — уже вычисленные выводы
якорных моделей общей части (заключение договора, недействительность, форма,
исковая давность, нарушение обязательства и прекращение договора). Слой
выводит из них общеправовые последствия для всего дела и указывает, какие
выводы специальных институтов лишены правового эффекта.

Юридическое основание распространения:
- статья 432 ГК РФ — договор считается заключённым при согласовании
  существенных условий в требуемой форме;
- статьи 162 и 165 ГК РФ — последствия несоблюдения формы сделки;
- статья 167 ГК РФ — недействительная сделка не влечёт юридических
  последствий, за исключением связанных с её недействительностью;
- статья 199 ГК РФ — истечение срока исковой давности, о применении которой
  заявлено стороной, является основанием к вынесению судом решения об отказе
  в иске;
- статьи 190–194 ГК РФ — правила исчисления сроков, которым подчинён и срок
  исковой давности, поэтому порок исчисления обесценивает вывод о его
  истечении;
- статья 183 ГК РФ — при отсутствии полномочий сделка считается заключённой от
  имени совершившего её лица, пока представляемый её не одобрит;
- статья 10 ГК РФ — при злоупотреблении правом суд отказывает лицу в защите
  принадлежащего ему права полностью или частично;
- статья 173.1 ГК РФ — сделка, совершённая без необходимого в силу закона
  согласия третьего лица, органа юридического лица или государственного органа,
  является оспоримой;
- статья 171 ГК РФ — сделка, совершённая гражданином, признанным судом
  недееспособным, ничтожна;
- статьи 129 и 168 ГК РФ — объекты гражданских прав свободно отчуждаются, если
  они не ограничены в обороте, а сделка, нарушающая требования закона и
  посягающая при этом на публичные интересы, ничтожна;
- статья 209 ГК РФ — распоряжение имуществом принадлежит собственнику, поэтому
  отчуждение неуправомоченным лицом не переносит право на приобретателя;
- статья 1103 ГК РФ — применение правил о неосновательном обогащении к
  требованиям о возврате исполненного по недействительной сделке;
- статья 405 пункт 3 ГК РФ — должник не считается просрочившим, пока
  обязательство не может быть исполнено вследствие просрочки кредитора, поэтому
  вывод специального института о нарушении не может быть положен в основание
  присуждения;
- глава 26 ГК РФ (статьи 407–419) — прекращение обязательства зачётом,
  новацией, прощением долга, невозможностью исполнения и иными основаниями
  прекращает и требование о его исполнении, тогда как требования, возникшие до
  прекращения, сохраняются (статья 407 пункт 4);
- статья 181.1 ГК РФ — решение собрания порождает правовые последствия для всех
  лиц, имевших право участвовать в собрании, поэтому условие договора, принятое
  таким решением, связывает и голосовавших против;
- статьи 181.3 и 181.5 ГК РФ — недействительное решение собрания
  недействительно с момента принятия, а ничтожность по статье 181.5 не зависит
  от признания судом, поэтому договорное условие, которое держится на таком
  решении, лишается основания (дело 45-КГ23-2-К7);
- статья 453 ГК РФ — при расторжении договора обязательства сторон прекращаются
  (пункт 2), но стороны не вправе требовать возвращения исполненного до
  расторжения (пункт 4), а сторона, для которой основанием расторжения послужило
  существенное нарушение, вправе требовать возмещения убытков (пункт 5).

Расторжение поэтому прекращает требование об исполнении **на будущее** и не
трогает ни вывод о нарушении, совершённом до расторжения, ни требования,
возникшие до него. Смешать расторжение с недействительностью — типичная ошибка:
недействительная сделка возвращает стороны в первоначальное положение,
расторгнутый договор — нет.

Про условие, потерявшее основание, слой говорит ровно то, что знает: спорное
условие держалось на решении собрания, и этого решения в правовом смысле нет.
Он не отменяет вывод специального института о нарушении, потому что не знает, о
каком именно условии идёт спор, — он поднимает дело человеку.
"""

from pydantic import BaseModel, ConfigDict, Field
from z3 import And, Bool, Not, Or, Solver, sat

GENERAL_EFFECTS_MODEL_VERSION = (
    "contracts-general-part-effects-articles-10-129-167-171-173-1-181-1-181-5-183-190-199"
    "-209-405-407-432-453-v11"
)


class GeneralEffectsInputs(BaseModel):
    """Входы слоя — выводы якорных моделей общей части, а не факты дела."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Заключение договора (статьи 432–443 ГК РФ).
    contract_concluded_prerequisites: bool
    # Недействительность сделки (статьи 166–181 ГК РФ).
    contractual_effect_displaced: bool
    restitution_required: bool
    # Форма сделки (статьи 158–165 ГК РФ).
    transaction_void_for_form: bool
    # Исковая давность (статьи 195–208 ГК РФ).
    limitation_defense_available: bool
    claim_not_subject_to_limitation: bool
    # Исчисление сроков (статьи 190–194 ГК РФ).
    term_calculation_defective: bool
    # Представительство: сделка неуполномоченного лица (статья 183 ГК РФ).
    unauthorized_representation_detected: bool
    # Вещные права: распоряжение неуправомоченным лицом (статья 209 ГК РФ).
    unauthorized_disposal_detected: bool
    # Пределы осуществления гражданских прав (статья 10 ГК РФ).
    abuse_of_right_detected: bool
    # Сделки: отсутствие необходимого согласия (статьи 157.1 и 173.1 ГК РФ).
    consent_missing_for_transaction: bool
    # Лица: недееспособность стороны (статьи 29 и 171 ГК РФ).
    party_lacks_capacity: bool
    # Объекты: изъятие объекта из оборота (статьи 129 и 168 ГК РФ).
    object_excluded_from_circulation: bool
    # Нарушение обязательства и прекращение договора (статьи 309–328, 450–453).
    breach_issue: bool
    # Расторжение договора (статьи 450–453) и судьба возникших до него требований.
    effective_termination: bool
    claims_accrued_before_termination: bool
    # Просрочка кредитора снимает просрочку должника (статья 405 пункт 3).
    creditor_delay_excuses_debtor: bool
    # Прекращение обязательства по главе 26 и судьба возникших требований.
    obligation_discharged_full: bool
    accrued_claims_preserved: bool
    # Договорное условие, которое держится на решении собрания (глава 9.1).
    contract_term_lacks_meeting_basis: bool
    contract_term_basis_voidable: bool
    contract_term_binds_all_participants: bool


class GeneralEffectsConstraintSet(BaseModel):
    id: str
    model_version: str = GENERAL_EFFECTS_MODEL_VERSION
    source_evaluations: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class GeneralEffectsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    # Действие договора как основания требований.
    contract_legally_effective: bool
    formation_defect_displaces_contract: bool
    invalidity_displaces_contract: bool
    form_defect_displaces_contract: bool
    unauthorized_representation_displaces_contract: bool
    incapacity_voids_transaction: bool
    restricted_object_voids_transaction: bool
    # Возможность судебной защиты.
    judicial_protection_available: bool
    claims_barred_by_limitation: bool
    limitation_conclusion_unreliable: bool
    protection_refused_for_abuse: bool
    # Совокупный эффект для требований из договора.
    contractual_claims_enforceable: bool
    transaction_challengeable_for_missing_consent: bool
    title_transfer_defeated: bool
    institute_conclusions_displaced: bool
    breach_findings_without_effect: bool
    debtor_delay_excused_by_creditor: bool
    obligation_discharged_before_claim: bool
    termination_ends_future_performance: bool
    only_accrued_claims_survive_termination: bool
    term_deprived_of_meeting_basis: bool
    term_meeting_basis_challengeable: bool
    term_binding_on_all_participants: bool
    restitution_regime_applies: bool
    requires_human_general_effects_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def build_general_effects_inputs(
    formation_evaluation,
    invalidity_evaluation,
    form_evaluation,
    limitation_evaluation,
    representation_evaluation,
    property_rights_evaluation,
    civil_principles_evaluation,
    transactions_evaluation,
    terms_evaluation,
    persons_evaluation,
    objects_evaluation,
    constraint_evaluation,
    termination_evaluation,
    attribution_delay_evaluation,
    obligation_dynamics_evaluation,
    meeting_decisions_evaluation,
) -> GeneralEffectsInputs:
    """Собрать входы слоя из выводов якорных моделей общей части."""
    return GeneralEffectsInputs(
        contract_concluded_prerequisites=formation_evaluation.contract_concluded_prerequisites,
        contractual_effect_displaced=invalidity_evaluation.contractual_effect_displaced,
        restitution_required=invalidity_evaluation.restitution_required,
        transaction_void_for_form=form_evaluation.transaction_void_for_form,
        limitation_defense_available=limitation_evaluation.limitation_defense_available,
        claim_not_subject_to_limitation=limitation_evaluation.claim_not_subject_to_limitation,
        unauthorized_representation_detected=(
            representation_evaluation.unauthorized_representation_detected
        ),
        unauthorized_disposal_detected=(property_rights_evaluation.unauthorized_disposal_detected),
        abuse_of_right_detected=civil_principles_evaluation.abuse_of_right_detected,
        consent_missing_for_transaction=(transactions_evaluation.consent_missing_for_transaction),
        term_calculation_defective=terms_evaluation.term_calculation_defective,
        party_lacks_capacity=persons_evaluation.party_lacks_capacity,
        object_excluded_from_circulation=(objects_evaluation.object_excluded_from_circulation),
        breach_issue=constraint_evaluation.breach_issue,
        effective_termination=termination_evaluation.effective_termination,
        claims_accrued_before_termination=(termination_evaluation.accrued_claims_preserved),
        creditor_delay_excuses_debtor=(attribution_delay_evaluation.creditor_delay_excuses_debtor),
        obligation_discharged_full=obligation_dynamics_evaluation.obligation_discharged_full,
        accrued_claims_preserved=obligation_dynamics_evaluation.accrued_claims_preserved,
        contract_term_lacks_meeting_basis=(
            meeting_decisions_evaluation.contract_term_lacks_meeting_basis
        ),
        contract_term_basis_voidable=(meeting_decisions_evaluation.contract_term_basis_voidable),
        contract_term_binds_all_participants=(
            meeting_decisions_evaluation.contract_term_binds_all_participants
        ),
    )


def build_general_effects_constraint_set(
    inputs: GeneralEffectsInputs,
    case_id: str,
) -> GeneralEffectsConstraintSet:
    return GeneralEffectsConstraintSet(
        id=f"general-effects-constraint-set:{case_id}",
        source_evaluations=[
            "formation_evaluation",
            "invalidity_evaluation",
            "form_evaluation",
            "limitation_evaluation",
            "representation_evaluation",
            "property_rights_evaluation",
            "civil_principles_evaluation",
            "transactions_evaluation",
            "terms_evaluation",
            "persons_evaluation",
            "objects_evaluation",
            "constraint_evaluation",
            "termination_evaluation",
            "attribution_delay_evaluation",
            "obligation_dynamics_evaluation",
            "meeting_decisions_evaluation",
        ],
        expressions=[
            "formation_defect_displaces_contract == NOT contract_concluded_prerequisites",
            "invalidity_displaces_contract == contractual_effect_displaced",
            "form_defect_displaces_contract == transaction_void_for_form",
            "unauthorized_representation_displaces_contract == unauthorized_representation_detected",
            "incapacity_voids_transaction == party_lacks_capacity",
            "restricted_object_voids_transaction == object_excluded_from_circulation",
            "contract_legally_effective == contract_concluded_prerequisites AND NOT contractual_effect_displaced AND NOT transaction_void_for_form AND NOT unauthorized_representation_detected AND NOT party_lacks_capacity AND NOT object_excluded_from_circulation",
            "limitation_bars_protection == limitation_defense_available AND NOT claim_not_subject_to_limitation AND NOT term_calculation_defective",
            "limitation_conclusion_unreliable == limitation_defense_available AND term_calculation_defective",
            "judicial_protection_available == NOT limitation_bars_protection AND NOT abuse_of_right_detected",
            "claims_barred_by_limitation == contract_legally_effective AND limitation_bars_protection",
            "protection_refused_for_abuse == contract_legally_effective AND abuse_of_right_detected",
            "contractual_claims_enforceable == contract_legally_effective AND judicial_protection_available",
            "institute_conclusions_displaced == NOT contract_legally_effective",
            "debtor_delay_excused_by_creditor == breach_issue AND creditor_delay_excuses_debtor",
            "obligation_discharged_before_claim == obligation_discharged_full AND NOT accrued_claims_preserved",
            "breach_findings_without_effect == breach_issue AND (NOT contractual_claims_enforceable OR creditor_delay_excuses_debtor OR obligation_discharged_before_claim)",
            "termination_ends_future_performance == contract_legally_effective AND effective_termination",
            "only_accrued_claims_survive_termination == termination_ends_future_performance AND claims_accrued_before_termination",
            "term_deprived_of_meeting_basis == contract_legally_effective AND contract_term_lacks_meeting_basis",
            "term_meeting_basis_challengeable == contract_legally_effective AND contract_term_basis_voidable",
            "term_binding_on_all_participants == contractual_claims_enforceable AND contract_term_binds_all_participants",
            "transaction_challengeable_for_missing_consent == contract_legally_effective AND consent_missing_for_transaction",
            "title_transfer_defeated == unauthorized_disposal_detected",
            "restitution_regime_applies == contractual_effect_displaced AND restitution_required",
            "requires_human_general_effects_assessment == institute_conclusions_displaced OR claims_barred_by_limitation OR protection_refused_for_abuse OR breach_findings_without_effect OR restitution_regime_applies OR title_transfer_defeated OR transaction_challengeable_for_missing_consent OR limitation_conclusion_unreliable OR term_deprived_of_meeting_basis OR term_meeting_basis_challengeable OR termination_ends_future_performance",
        ],
    )


def evaluate_general_effects_constraints(
    constraint_set: GeneralEffectsConstraintSet,
    inputs: GeneralEffectsInputs,
) -> GeneralEffectsEvaluation:
    variables = {field_name: Bool(field_name) for field_name in GeneralEffectsInputs.model_fields}
    contract_legally_effective = Bool("contract_legally_effective")
    formation_defect_displaces_contract = Bool("formation_defect_displaces_contract")
    invalidity_displaces_contract = Bool("invalidity_displaces_contract")
    form_defect_displaces_contract = Bool("form_defect_displaces_contract")
    unauthorized_representation_displaces_contract = Bool(
        "unauthorized_representation_displaces_contract"
    )
    incapacity_voids_transaction = Bool("incapacity_voids_transaction")
    restricted_object_voids_transaction = Bool("restricted_object_voids_transaction")
    judicial_protection_available = Bool("judicial_protection_available")
    limitation_bars_protection = Bool("limitation_bars_protection")
    claims_barred_by_limitation = Bool("claims_barred_by_limitation")
    limitation_conclusion_unreliable = Bool("limitation_conclusion_unreliable")
    protection_refused_for_abuse = Bool("protection_refused_for_abuse")
    contractual_claims_enforceable = Bool("contractual_claims_enforceable")
    transaction_challengeable_for_missing_consent = Bool(
        "transaction_challengeable_for_missing_consent"
    )
    institute_conclusions_displaced = Bool("institute_conclusions_displaced")
    breach_findings_without_effect = Bool("breach_findings_without_effect")
    debtor_delay_excused_by_creditor = Bool("debtor_delay_excused_by_creditor")
    obligation_discharged_before_claim = Bool("obligation_discharged_before_claim")
    termination_ends_future_performance = Bool("termination_ends_future_performance")
    only_accrued_claims_survive_termination = Bool("only_accrued_claims_survive_termination")
    term_deprived_of_meeting_basis = Bool("term_deprived_of_meeting_basis")
    term_meeting_basis_challengeable = Bool("term_meeting_basis_challengeable")
    term_binding_on_all_participants = Bool("term_binding_on_all_participants")
    title_transfer_defeated = Bool("title_transfer_defeated")
    restitution_regime_applies = Bool("restitution_regime_applies")
    requires_human_general_effects_assessment = Bool("requires_human_general_effects_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(inputs, field_name))
    solver.add(
        formation_defect_displaces_contract == Not(variables["contract_concluded_prerequisites"])
    )
    solver.add(invalidity_displaces_contract == variables["contractual_effect_displaced"])
    solver.add(form_defect_displaces_contract == variables["transaction_void_for_form"])
    solver.add(
        unauthorized_representation_displaces_contract
        == variables["unauthorized_representation_detected"]
    )
    solver.add(incapacity_voids_transaction == variables["party_lacks_capacity"])
    solver.add(restricted_object_voids_transaction == variables["object_excluded_from_circulation"])
    solver.add(
        contract_legally_effective
        == And(
            variables["contract_concluded_prerequisites"],
            Not(variables["contractual_effect_displaced"]),
            Not(variables["transaction_void_for_form"]),
            Not(variables["unauthorized_representation_detected"]),
            Not(variables["party_lacks_capacity"]),
            Not(variables["object_excluded_from_circulation"]),
        )
    )
    solver.add(
        limitation_bars_protection
        == And(
            variables["limitation_defense_available"],
            Not(variables["claim_not_subject_to_limitation"]),
            Not(variables["term_calculation_defective"]),
        )
    )
    solver.add(
        limitation_conclusion_unreliable
        == And(
            variables["limitation_defense_available"],
            variables["term_calculation_defective"],
        )
    )
    solver.add(
        judicial_protection_available
        == And(
            Not(limitation_bars_protection),
            Not(variables["abuse_of_right_detected"]),
        )
    )
    solver.add(
        claims_barred_by_limitation == And(contract_legally_effective, limitation_bars_protection)
    )
    solver.add(
        protection_refused_for_abuse
        == And(contract_legally_effective, variables["abuse_of_right_detected"])
    )
    solver.add(
        contractual_claims_enforceable
        == And(contract_legally_effective, judicial_protection_available)
    )
    solver.add(institute_conclusions_displaced == Not(contract_legally_effective))
    solver.add(
        debtor_delay_excused_by_creditor
        == And(variables["breach_issue"], variables["creditor_delay_excuses_debtor"])
    )
    # Прекращение обязательства по главе 26 прекращает и требование о его
    # исполнении. Но требования, возникшие до прекращения, сохраняются
    # (статья 407 пункт 4), и тогда вывод о нарушении своего эффекта не теряет.
    solver.add(
        obligation_discharged_before_claim
        == And(
            variables["obligation_discharged_full"],
            Not(variables["accrued_claims_preserved"]),
        )
    )
    # Просрочка кредитора не отменяет договор и не лишает суда защиты: она
    # снимает основание считать должника просрочившим (статья 405 пункт 3), а
    # значит вывод института о нарушении не может лечь в основание присуждения.
    solver.add(
        breach_findings_without_effect
        == And(
            variables["breach_issue"],
            Or(
                Not(contractual_claims_enforceable),
                variables["creditor_delay_excuses_debtor"],
                obligation_discharged_before_claim,
            ),
        )
    )
    # При расторжении договора обязательства сторон прекращаются (статья 453
    # пункт 2): требовать исполнения на будущее нельзя. Вывод о нарушении при
    # этом своей силы не теряет — нарушение совершено до расторжения, и в
    # `breach_findings_without_effect` расторжение намеренно не входит.
    solver.add(
        termination_ends_future_performance
        == And(contract_legally_effective, variables["effective_termination"])
    )
    # Что именно переживает расторжение: требования, возникшие до него. Реституции
    # расторжение не влечёт — стороны не вправе требовать возвращения
    # исполненного до расторжения (статья 453 пункт 4), и этим оно отличается от
    # недействительности.
    solver.add(
        only_accrued_claims_survive_termination
        == And(
            termination_ends_future_performance,
            variables["claims_accrued_before_termination"],
        )
    )
    # Условие договора, принятое решением собрания, разделяет судьбу этого
    # решения (статьи 181.3 и 181.5). Смысл вывод имеет только там, где договор
    # вообще действует: если он вытеснен целиком, судьба отдельного условия уже
    # решена, и второй ответ был бы двойным счётом.
    solver.add(
        term_deprived_of_meeting_basis
        == And(contract_legally_effective, variables["contract_term_lacks_meeting_basis"])
    )
    solver.add(
        term_meeting_basis_challengeable
        == And(contract_legally_effective, variables["contract_term_basis_voidable"])
    )
    # Обратная сторона статьи 181.1: решение действительно, договор действует и
    # защита доступна — тогда условие связывает и того, кто голосовал против.
    solver.add(
        term_binding_on_all_participants
        == And(contractual_claims_enforceable, variables["contract_term_binds_all_participants"])
    )
    solver.add(
        transaction_challengeable_for_missing_consent
        == And(contract_legally_effective, variables["consent_missing_for_transaction"])
    )
    solver.add(title_transfer_defeated == variables["unauthorized_disposal_detected"])
    solver.add(
        restitution_regime_applies
        == And(variables["contractual_effect_displaced"], variables["restitution_required"])
    )
    solver.add(
        requires_human_general_effects_assessment
        == Or(
            institute_conclusions_displaced,
            claims_barred_by_limitation,
            protection_refused_for_abuse,
            breach_findings_without_effect,
            restitution_regime_applies,
            title_transfer_defeated,
            transaction_challengeable_for_missing_consent,
            limitation_conclusion_unreliable,
            term_deprived_of_meeting_basis,
            term_meeting_basis_challengeable,
            termination_ends_future_performance,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return GeneralEffectsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            contract_legally_effective=False,
            formation_defect_displaces_contract=False,
            invalidity_displaces_contract=False,
            form_defect_displaces_contract=False,
            unauthorized_representation_displaces_contract=False,
            incapacity_voids_transaction=False,
            restricted_object_voids_transaction=False,
            judicial_protection_available=False,
            claims_barred_by_limitation=False,
            limitation_conclusion_unreliable=False,
            protection_refused_for_abuse=False,
            contractual_claims_enforceable=False,
            transaction_challengeable_for_missing_consent=False,
            institute_conclusions_displaced=True,
            breach_findings_without_effect=False,
            debtor_delay_excused_by_creditor=False,
            obligation_discharged_before_claim=False,
            termination_ends_future_performance=False,
            only_accrued_claims_survive_termination=False,
            term_deprived_of_meeting_basis=False,
            term_meeting_basis_challengeable=False,
            term_binding_on_all_participants=False,
            title_transfer_defeated=False,
            restitution_regime_applies=False,
            requires_human_general_effects_assessment=True,
            reasons_ru=["Выводы моделей общей части противоречивы."],
            warnings_ru=["Требуется проверка исходных выводов юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор порождает правовые последствия: существенные условия согласованы в "
            "требуемой форме (статья 432 ГК РФ), основания недействительности не установлены "
            "(статьи 166–181 ГК РФ), порок формы отсутствует (статьи 162 и 165 ГК РФ)."
            if truth(contract_legally_effective)
            else (
                "Договор не порождает правовых последствий как основание требований сторон; "
                "выводы специальных институтов о нарушении его условий правового эффекта не "
                "имеют."
            )
        ),
    ]
    if truth(formation_defect_displaces_contract):
        reasons_ru.append(
            "Договор не считается заключённым: между сторонами не достигнуто соглашение по всем "
            "существенным условиям в требуемой форме, поэтому обязательства из него не "
            "возникли (статья 432 ГК РФ)."
        )
    if truth(invalidity_displaces_contract):
        reasons_ru.append(
            "Недействительная сделка не влечёт юридических последствий, за исключением тех, "
            "которые связаны с её недействительностью, и недействительна с момента её "
            "совершения (статья 167 ГК РФ)."
        )
    if truth(form_defect_displaces_contract):
        reasons_ru.append(
            "Несоблюдение установленной формы сделки влечёт её недействительность в случаях, "
            "прямо указанных в законе или в соглашении сторон (статьи 162 и 165 ГК РФ)."
        )
    if truth(unauthorized_representation_displaces_contract):
        reasons_ru.append(
            "Сделка совершена лицом без полномочий и не одобрена представляемым, поэтому она "
            "считается заключённой от имени и в интересах совершившего её лица и не связывает "
            "представляемого (статья 183 ГК РФ)."
        )
    if truth(incapacity_voids_transaction):
        reasons_ru.append(
            "Сторона признана судом недееспособной, поэтому совершённая ею сделка ничтожна и "
            "не влечёт юридических последствий; каждая из сторон обязана возвратить другой "
            "всё полученное, а дееспособная сторона возмещает реальный ущерб, если знала или "
            "должна была знать о недееспособности (статьи 29, 167 и 171 ГК РФ)."
        )
    if truth(restricted_object_voids_transaction):
        reasons_ru.append(
            "Объект сделки изъят из оборота либо его отчуждение ограничено законом, тогда как "
            "объекты гражданских прав могут свободно отчуждаться, если они не ограничены в "
            "обороте; сделка, нарушающая это требование закона и посягающая при этом на "
            "публичные интересы, ничтожна (статьи 129 и 168 ГК РФ)."
        )
    if truth(claims_barred_by_limitation):
        reasons_ru.append(
            "Истечение срока исковой давности, о применении которой заявлено стороной спора, "
            "является самостоятельным основанием к вынесению судом решения об отказе в иске "
            "(статья 199 ГК РФ)."
        )
    if truth(limitation_conclusion_unreliable):
        reasons_ru.append(
            "Вывод об истечении срока исковой давности не может быть положен в основание "
            "отказа в иске: срок исковой давности исчисляется по общим правилам об "
            "исчислении сроков, а они применены с нарушением, поэтому истечение срока не "
            "считается установленным (статьи 190–194 и 199 ГК РФ)."
        )
    if truth(protection_refused_for_abuse):
        reasons_ru.append(
            "Установлено злоупотребление правом, поэтому суд с учётом характера и последствий "
            "допущенного злоупотребления отказывает лицу в защите принадлежащего ему права "
            "полностью или частично (статья 10 ГК РФ)."
        )
    if truth(debtor_delay_excused_by_creditor):
        reasons_ru.append(
            "Кредитор просрочил принятие исполнения, поэтому должник не считается "
            "просрочившим, пока обязательство не может быть исполнено вследствие "
            "просрочки кредитора; вывод специального института о нарушении не "
            "может быть положен в основание присуждения (статья 405 пункт 3 ГК РФ)."
        )
    if truth(obligation_discharged_before_claim):
        reasons_ru.append(
            "Обязательство прекращено по основаниям главы 26 ГК РФ, и требований, "
            "возникших до прекращения, не сохранилось, поэтому требовать его "
            "исполнения нельзя, а вывод специального института о нарушении не "
            "может быть положен в основание присуждения (статьи 407–419 ГК РФ)."
        )
    if truth(breach_findings_without_effect):
        reasons_ru.append(
            "Установленное нарушение обязательства не влечёт удовлетворения требований: "
            "договор не порождает последствий либо в судебной защите отказано, поэтому выводы "
            "специальных институтов о нарушении его условий не могут быть положены в основание "
            "присуждения (статьи 167, 199 и 432 ГК РФ)."
        )
    if truth(termination_ends_future_performance):
        reasons_ru.append(
            "Договор расторгнут, поэтому обязательства сторон на будущее прекращены и "
            "требовать исполнения по нему нельзя. Это не отменяет вывод о нарушении, "
            "совершённом до расторжения, и не влечёт возврата исполненного: стороны не "
            "вправе требовать возвращения того, что было исполнено ими до расторжения, "
            "если иное не установлено законом или соглашением (статья 453 ГК РФ)."
        )
    if truth(only_accrued_claims_survive_termination):
        reasons_ru.append(
            "Расторжение пережили требования, возникшие до него: обязательства на будущее "
            "прекращены, но ответственность за нарушения, допущенные до расторжения, "
            "сохраняется, а сторона, для которой основанием расторжения послужило "
            "существенное нарушение договора, вправе требовать возмещения причинённых "
            "расторжением убытков (статья 453 ГК РФ)."
        )
    if truth(term_deprived_of_meeting_basis):
        reasons_ru.append(
            "Условие договора держится на решении общего собрания, которое ничтожно либо не "
            "принято, поэтому основания у этого условия нет: недействительное решение "
            "недействительно с момента его принятия, а ничтожность не зависит от признания "
            "судом. Требование, основанное на таком условии, не может быть удовлетворено в "
            "той части, в какой оно из этого условия следует; какое именно условие спорно, "
            "определяет юрист (статьи 181.1, 181.3 и 181.5 ГК РФ)."
        )
    if truth(term_meeting_basis_challengeable):
        reasons_ru.append(
            "Решение собрания, на котором держится условие договора, оспоримо: оно "
            "действует, пока не признано недействительным судом, поэтому условие сохраняет "
            "силу, но вывод по делу зависит от исхода оспаривания (статья 181.4 ГК РФ)."
        )
    if truth(term_binding_on_all_participants):
        reasons_ru.append(
            "Условие договора принято решением собрания и обязательно для всех лиц, имевших "
            "право участвовать в нём, в том числе для голосовавших против и не "
            "участвовавших; изменить его в одностороннем порядке вопреки решению нельзя "
            "(статьи 181.1 и 181.3 ГК РФ)."
        )
    if truth(transaction_challengeable_for_missing_consent):
        reasons_ru.append(
            "Сделка совершена без необходимого в силу закона согласия третьего лица, органа "
            "юридического лица или государственного органа, поэтому она является оспоримой и "
            "может быть признана недействительной судом по иску такого лица или иных лиц, "
            "указанных в законе; до признания её недействительной судом договор сохраняет "
            "действие (статьи 157.1, 166 и 173.1 ГК РФ)."
        )
    if truth(title_transfer_defeated):
        reasons_ru.append(
            "Имуществом распорядилось лицо, не управомоченное на его отчуждение, поэтому право "
            "собственности к приобретателю по общему правилу не перешло; требование о переходе "
            "титула не может быть удовлетворено, а защита добросовестного приобретателя "
            "оценивается по правилам статьи 302 ГК РФ (статьи 209 и 302 ГК РФ)."
        )
    if truth(restitution_regime_applies):
        reasons_ru.append(
            "Вместо договорных требований подлежат применению последствия недействительности "
            "сделки: каждая из сторон обязана возвратить другой всё полученное по сделке, а к "
            "требованиям о возврате исполненного применяются правила о неосновательном "
            "обогащении (статьи 167 и 1103 ГК РФ)."
        )
    if truth(contractual_claims_enforceable):
        reasons_ru.append(
            "Требования, основанные на договоре, могут быть предъявлены и рассмотрены по "
            "существу: договор действует и срок исковой давности не препятствует защите права."
        )
    return GeneralEffectsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        contract_legally_effective=truth(contract_legally_effective),
        formation_defect_displaces_contract=truth(formation_defect_displaces_contract),
        invalidity_displaces_contract=truth(invalidity_displaces_contract),
        form_defect_displaces_contract=truth(form_defect_displaces_contract),
        unauthorized_representation_displaces_contract=truth(
            unauthorized_representation_displaces_contract
        ),
        incapacity_voids_transaction=truth(incapacity_voids_transaction),
        restricted_object_voids_transaction=truth(restricted_object_voids_transaction),
        judicial_protection_available=truth(judicial_protection_available),
        claims_barred_by_limitation=truth(claims_barred_by_limitation),
        limitation_conclusion_unreliable=truth(limitation_conclusion_unreliable),
        protection_refused_for_abuse=truth(protection_refused_for_abuse),
        contractual_claims_enforceable=truth(contractual_claims_enforceable),
        transaction_challengeable_for_missing_consent=truth(
            transaction_challengeable_for_missing_consent
        ),
        institute_conclusions_displaced=truth(institute_conclusions_displaced),
        breach_findings_without_effect=truth(breach_findings_without_effect),
        debtor_delay_excused_by_creditor=truth(debtor_delay_excused_by_creditor),
        obligation_discharged_before_claim=truth(obligation_discharged_before_claim),
        termination_ends_future_performance=truth(termination_ends_future_performance),
        only_accrued_claims_survive_termination=truth(only_accrued_claims_survive_termination),
        term_deprived_of_meeting_basis=truth(term_deprived_of_meeting_basis),
        term_meeting_basis_challengeable=truth(term_meeting_basis_challengeable),
        term_binding_on_all_participants=truth(term_binding_on_all_participants),
        title_transfer_defeated=truth(title_transfer_defeated),
        restitution_regime_applies=truth(restitution_regime_applies),
        requires_human_general_effects_assessment=truth(requires_human_general_effects_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Слой применяет только формальные общие положения ГК РФ к выводам специальных "
            "институтов и не заменяет судебную оценку.",
            "Наличие оснований недействительности, уважительность причин пропуска срока "
            "исковой давности и состав подлежащего возврату по недействительной сделке "
            "оцениваются экспертом и судом (статьи 167, 199 и 205 ГК РФ).",
        ],
    )
