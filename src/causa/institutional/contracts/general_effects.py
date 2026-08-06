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
- статья 183 ГК РФ — при отсутствии полномочий сделка считается заключённой от
  имени совершившего её лица, пока представляемый её не одобрит;
- статья 1103 ГК РФ — применение правил о неосновательном обогащении к
  требованиям о возврате исполненного по недействительной сделке.
"""

from pydantic import BaseModel, ConfigDict, Field
from z3 import And, Bool, Not, Or, Solver, sat

GENERAL_EFFECTS_MODEL_VERSION = "contracts-general-part-effects-articles-167-183-199-432-v1"


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
    # Представительство: сделка неуполномоченного лица (статья 183 ГК РФ).
    unauthorized_representation_detected: bool
    # Нарушение обязательства и прекращение договора (статьи 309–328, 450–453).
    breach_issue: bool
    effective_termination: bool


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
    # Возможность судебной защиты.
    judicial_protection_available: bool
    claims_barred_by_limitation: bool
    # Совокупный эффект для требований из договора.
    contractual_claims_enforceable: bool
    institute_conclusions_displaced: bool
    breach_findings_without_effect: bool
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
    constraint_evaluation,
    termination_evaluation,
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
        breach_issue=constraint_evaluation.breach_issue,
        effective_termination=termination_evaluation.effective_termination,
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
            "constraint_evaluation",
            "termination_evaluation",
        ],
        expressions=[
            "formation_defect_displaces_contract == NOT contract_concluded_prerequisites",
            "invalidity_displaces_contract == contractual_effect_displaced",
            "form_defect_displaces_contract == transaction_void_for_form",
            "unauthorized_representation_displaces_contract == unauthorized_representation_detected",
            "contract_legally_effective == contract_concluded_prerequisites AND NOT contractual_effect_displaced AND NOT transaction_void_for_form AND NOT unauthorized_representation_detected",
            "judicial_protection_available == claim_not_subject_to_limitation OR NOT limitation_defense_available",
            "claims_barred_by_limitation == contract_legally_effective AND NOT judicial_protection_available",
            "contractual_claims_enforceable == contract_legally_effective AND judicial_protection_available",
            "institute_conclusions_displaced == NOT contract_legally_effective",
            "breach_findings_without_effect == breach_issue AND NOT contractual_claims_enforceable",
            "restitution_regime_applies == contractual_effect_displaced AND restitution_required",
            "requires_human_general_effects_assessment == institute_conclusions_displaced OR claims_barred_by_limitation OR breach_findings_without_effect OR restitution_regime_applies",
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
    judicial_protection_available = Bool("judicial_protection_available")
    claims_barred_by_limitation = Bool("claims_barred_by_limitation")
    contractual_claims_enforceable = Bool("contractual_claims_enforceable")
    institute_conclusions_displaced = Bool("institute_conclusions_displaced")
    breach_findings_without_effect = Bool("breach_findings_without_effect")
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
    solver.add(
        contract_legally_effective
        == And(
            variables["contract_concluded_prerequisites"],
            Not(variables["contractual_effect_displaced"]),
            Not(variables["transaction_void_for_form"]),
            Not(variables["unauthorized_representation_detected"]),
        )
    )
    solver.add(
        judicial_protection_available
        == Or(
            variables["claim_not_subject_to_limitation"],
            Not(variables["limitation_defense_available"]),
        )
    )
    solver.add(
        claims_barred_by_limitation
        == And(contract_legally_effective, Not(judicial_protection_available))
    )
    solver.add(
        contractual_claims_enforceable
        == And(contract_legally_effective, judicial_protection_available)
    )
    solver.add(institute_conclusions_displaced == Not(contract_legally_effective))
    solver.add(
        breach_findings_without_effect
        == And(variables["breach_issue"], Not(contractual_claims_enforceable))
    )
    solver.add(
        restitution_regime_applies
        == And(variables["contractual_effect_displaced"], variables["restitution_required"])
    )
    solver.add(
        requires_human_general_effects_assessment
        == Or(
            institute_conclusions_displaced,
            claims_barred_by_limitation,
            breach_findings_without_effect,
            restitution_regime_applies,
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
            judicial_protection_available=False,
            claims_barred_by_limitation=False,
            contractual_claims_enforceable=False,
            institute_conclusions_displaced=True,
            breach_findings_without_effect=False,
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
    if truth(claims_barred_by_limitation):
        reasons_ru.append(
            "Истечение срока исковой давности, о применении которой заявлено стороной спора, "
            "является самостоятельным основанием к вынесению судом решения об отказе в иске "
            "(статья 199 ГК РФ)."
        )
    if truth(breach_findings_without_effect):
        reasons_ru.append(
            "Установленное нарушение обязательства не влечёт удовлетворения требований: "
            "договор не порождает последствий либо в судебной защите отказано, поэтому выводы "
            "специальных институтов о нарушении его условий не могут быть положены в основание "
            "присуждения (статьи 167, 199 и 432 ГК РФ)."
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
        judicial_protection_available=truth(judicial_protection_available),
        claims_barred_by_limitation=truth(claims_barred_by_limitation),
        contractual_claims_enforceable=truth(contractual_claims_enforceable),
        institute_conclusions_displaced=truth(institute_conclusions_displaced),
        breach_findings_without_effect=truth(breach_findings_without_effect),
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
