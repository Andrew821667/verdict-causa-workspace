"""Формальная модель возложения ответственности и просрочки сторон.

Статьи 402–406 ГК РФ: ответственность должника за действия своих работников
(402), ответственность должника за действия третьих лиц, на которых возложено
исполнение (403), вина кредитора и её влияние на размер ответственности (404),
просрочка должника (405) и просрочка кредитора (406).

**Почему институт появился.** Пробел нашла реальная судебная практика, а не
разбор кодекса. Измерение покрытия сопоставило статьи, на которые сослались суды
в полученной выгрузке, с диапазонами институтов пакета — и статьи 402–406
оказались не покрыты ничем: модель ответственности заявляет статьи 333–401 и
останавливается перед ними, модель средств защиты берёт из главы 25 только
статьи 393 и 406.1. Между ними лежала полоса из пяти статей, на которые суды
ссылались дважды в пятидесяти делах.

**Два вывода, меняющие судьбу требования по праву:**

- `debtor_answerable_for_third_party` — возложение исполнения на третье лицо не
  переносит ответственность: за неисполнение отвечает должник, если законом не
  установлено, что отвечает непосредственный исполнитель (статья 403);
- `creditor_delay_excuses_debtor` — просрочка кредитора освобождает должника от
  ответственности за своё последующее нарушение и снимает основание считать его
  просрочившим (статьи 405 п. 3 и 406).

**Оговорка, установленная измерением.** При выпуске института здесь было
написано, что эти выводы модель «даёт слою общих положений». Это неверно:
прогон реальных дел через весь конвейер показал, что среди пятнадцати входов
слоя нет ни одного поля этой модели. Выводы меняют оценку самого института и
поднимают флаг экспертизы, но до итоговых выводов, которые читает юрист, не
доходят. Недоходимость измеряется в
[`real_case_pipeline`](real_case_pipeline.py) и остаётся открытой.

**Чего модель не делает.** Она не определяет размер ответственности. Статья 404
даёт суду право уменьшить размер, а не обязанность в заранее известной
пропорции; степень вины каждой стороны — вопрос судебной оценки. Модель лишь
называет установленным факт вины кредитора и поднимает флаг экспертизы.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

ATTRIBUTION_DELAY_EVIDENCE_SCHEMA_VERSION = "contracts.attribution-delay-evidence.v0"
ATTRIBUTION_DELAY_MAPPING_VERSION = "contracts-reviewed-attribution-delay-to-facts-v0"
ATTRIBUTION_DELAY_MODEL_VERSION = "contracts-attribution-delay-articles-402-406-v0"


class AttributionDelayEvidencePredicate(str, Enum):
    # Квалификация: нарушение обязательства, к которому относятся статьи 402–406.
    OBLIGATION_BREACH_ASSERTED = "obligation_breach_asserted"
    # Возложение исполнения (статьи 402–403 ГК РФ).
    BREACH_CAUSED_BY_DEBTOR_EMPLOYEES = "breach_caused_by_debtor_employees"
    PERFORMANCE_ENTRUSTED_TO_THIRD_PARTY = "performance_entrusted_to_third_party"
    THIRD_PARTY_CAUSED_BREACH = "third_party_caused_breach"
    LAW_ASSIGNS_LIABILITY_TO_PERFORMER = "law_assigns_liability_to_performer"
    # Вина кредитора (статья 404 ГК РФ).
    CREDITOR_FAULT_CONTRIBUTED_TO_BREACH = "creditor_fault_contributed_to_breach"
    CREDITOR_FAILED_TO_MITIGATE_LOSS = "creditor_failed_to_mitigate_loss"
    # Просрочка сторон (статьи 405–406 ГК РФ).
    DEBTOR_DELAY_ESTABLISHED = "debtor_delay_established"
    PERFORMANCE_LOST_INTEREST_FOR_CREDITOR = "performance_lost_interest_for_creditor"
    CREDITOR_DELAY_ESTABLISHED = "creditor_delay_established"


REQUIRED_ATTRIBUTION_DELAY_PREDICATES = frozenset(AttributionDelayEvidencePredicate)


class AttributionDelayEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: AttributionDelayEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedAttributionDelayEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = ATTRIBUTION_DELAY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[AttributionDelayEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedAttributionDelayEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Attribution and delay evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Attribution and delay evidence contains duplicate legal source refs.")
        return self


class AttributionDelayFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    obligation_breach_asserted: bool
    breach_caused_by_debtor_employees: bool
    performance_entrusted_to_third_party: bool
    third_party_caused_breach: bool
    law_assigns_liability_to_performer: bool
    creditor_fault_contributed_to_breach: bool
    creditor_failed_to_mitigate_loss: bool
    debtor_delay_established: bool
    performance_lost_interest_for_creditor: bool
    creditor_delay_established: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "AttributionDelayFactSet":
        if self.third_party_caused_breach and not self.performance_entrusted_to_third_party:
            raise ValueError(
                "Нарушение третьим лицом относится только к случаю, когда на него было "
                "возложено исполнение обязательства (статья 403 ГК РФ)."
            )
        if self.performance_lost_interest_for_creditor and not self.debtor_delay_established:
            raise ValueError(
                "Утрата интереса кредитора к исполнению относится только к просрочке "
                "должника (статья 405 ГК РФ)."
            )
        return self


class AttributionDelayFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class AttributionDelayEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: AttributionDelayFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[AttributionDelayFactProvenance] = Field(default_factory=list)


class AttributionDelayConstraintSet(BaseModel):
    id: str
    model_version: str = ATTRIBUTION_DELAY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class AttributionDelayEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    attribution_qualified: bool
    debtor_answerable_for_employees: bool
    # Ключевой вывод для слоя общих положений: возложение исполнения на третье
    # лицо не переносит ответственность (статья 403 ГК РФ).
    debtor_answerable_for_third_party: bool
    liability_shifted_to_performer: bool
    creditor_fault_established: bool
    liability_reducible_for_creditor_fault: bool
    debtor_in_delay: bool
    creditor_may_refuse_performance: bool
    creditor_in_delay: bool
    # Ключевой вывод для слоя общих положений: просрочка кредитора освобождает
    # должника от ответственности за последующее нарушение (статьи 405, 406).
    creditor_delay_excuses_debtor: bool
    requires_human_attribution_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_attribution_delay_evidence(
    evidence: ReviewedAttributionDelayEvidence,
) -> AttributionDelayEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Attribution and delay evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Attribution and delay evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_ATTRIBUTION_DELAY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed attribution and delay evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_ATTRIBUTION_DELAY_PREDICATES
    }
    return AttributionDelayEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=ATTRIBUTION_DELAY_MAPPING_VERSION,
        facts=AttributionDelayFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            AttributionDelayFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_ATTRIBUTION_DELAY_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_attribution_delay_constraint_set(
    mapping: AttributionDelayEvidenceMappingResult,
) -> AttributionDelayConstraintSet:
    return AttributionDelayConstraintSet(
        id=f"attribution-delay-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "attribution_qualified == obligation_breach_asserted",
            "debtor_answerable_for_employees == attribution_qualified AND breach_caused_by_debtor_employees",
            "liability_shifted_to_performer == attribution_qualified AND performance_entrusted_to_third_party AND third_party_caused_breach AND law_assigns_liability_to_performer",
            "debtor_answerable_for_third_party == attribution_qualified AND performance_entrusted_to_third_party AND third_party_caused_breach AND NOT law_assigns_liability_to_performer",
            "creditor_fault_established == attribution_qualified AND (creditor_fault_contributed_to_breach OR creditor_failed_to_mitigate_loss)",
            "liability_reducible_for_creditor_fault == creditor_fault_established",
            "debtor_in_delay == attribution_qualified AND debtor_delay_established AND NOT creditor_delay_established",
            "creditor_may_refuse_performance == debtor_in_delay AND performance_lost_interest_for_creditor",
            "creditor_in_delay == attribution_qualified AND creditor_delay_established",
            "creditor_delay_excuses_debtor == creditor_in_delay",
            "requires_human_attribution_assessment == debtor_answerable_for_employees OR debtor_answerable_for_third_party OR liability_shifted_to_performer OR creditor_fault_established OR debtor_in_delay OR creditor_in_delay",
        ],
    )


def evaluate_attribution_delay_constraints(
    constraint_set: AttributionDelayConstraintSet,
    facts: AttributionDelayFactSet,
) -> AttributionDelayEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in AttributionDelayFactSet.model_fields
    }
    attribution_qualified = Bool("attribution_qualified")
    debtor_answerable_for_employees = Bool("debtor_answerable_for_employees")
    debtor_answerable_for_third_party = Bool("debtor_answerable_for_third_party")
    liability_shifted_to_performer = Bool("liability_shifted_to_performer")
    creditor_fault_established = Bool("creditor_fault_established")
    liability_reducible_for_creditor_fault = Bool("liability_reducible_for_creditor_fault")
    debtor_in_delay = Bool("debtor_in_delay")
    creditor_may_refuse_performance = Bool("creditor_may_refuse_performance")
    creditor_in_delay = Bool("creditor_in_delay")
    creditor_delay_excuses_debtor = Bool("creditor_delay_excuses_debtor")
    requires_human_attribution_assessment = Bool("requires_human_attribution_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(attribution_qualified == variables["obligation_breach_asserted"])
    solver.add(
        debtor_answerable_for_employees
        == And(attribution_qualified, variables["breach_caused_by_debtor_employees"])
    )
    solver.add(
        liability_shifted_to_performer
        == And(
            attribution_qualified,
            variables["performance_entrusted_to_third_party"],
            variables["third_party_caused_breach"],
            variables["law_assigns_liability_to_performer"],
        )
    )
    solver.add(
        debtor_answerable_for_third_party
        == And(
            attribution_qualified,
            variables["performance_entrusted_to_third_party"],
            variables["third_party_caused_breach"],
            Not(variables["law_assigns_liability_to_performer"]),
        )
    )
    solver.add(
        creditor_fault_established
        == And(
            attribution_qualified,
            Or(
                variables["creditor_fault_contributed_to_breach"],
                variables["creditor_failed_to_mitigate_loss"],
            ),
        )
    )
    solver.add(liability_reducible_for_creditor_fault == creditor_fault_established)
    solver.add(
        debtor_in_delay
        == And(
            attribution_qualified,
            variables["debtor_delay_established"],
            Not(variables["creditor_delay_established"]),
        )
    )
    solver.add(
        creditor_may_refuse_performance
        == And(debtor_in_delay, variables["performance_lost_interest_for_creditor"])
    )
    solver.add(
        creditor_in_delay == And(attribution_qualified, variables["creditor_delay_established"])
    )
    solver.add(creditor_delay_excuses_debtor == creditor_in_delay)
    solver.add(
        requires_human_attribution_assessment
        == Or(
            debtor_answerable_for_employees,
            debtor_answerable_for_third_party,
            liability_shifted_to_performer,
            creditor_fault_established,
            debtor_in_delay,
            creditor_in_delay,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return AttributionDelayEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            attribution_qualified=False,
            debtor_answerable_for_employees=False,
            debtor_answerable_for_third_party=False,
            liability_shifted_to_performer=False,
            creditor_fault_established=False,
            liability_reducible_for_creditor_fault=False,
            debtor_in_delay=False,
            creditor_may_refuse_performance=False,
            creditor_in_delay=False,
            creditor_delay_excuses_debtor=False,
            requires_human_attribution_assessment=True,
            reasons_ru=["Набор фактов о возложении ответственности и просрочке противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Заявлено нарушение обязательства, к которому применяются правила о "
            "возложении ответственности и просрочке сторон (статьи 402–406 ГК РФ)."
            if truth(attribution_qualified)
            else "Нарушение обязательства в деле не заявлено."
        ),
    ]
    if truth(debtor_answerable_for_employees):
        reasons_ru.append(
            "Действия работников должника по исполнению его обязательства считаются "
            "действиями должника, и должник отвечает за эти действия, если они повлекли "
            "неисполнение или ненадлежащее исполнение обязательства (статья 402 ГК РФ)."
        )
    if truth(debtor_answerable_for_third_party):
        reasons_ru.append(
            "Исполнение обязательства возложено на третье лицо, и нарушение вызвано его "
            "действиями, однако ответственность за неисполнение или ненадлежащее исполнение "
            "несёт должник: возложение исполнения не переносит ответственность "
            "(статья 403 ГК РФ)."
        )
    if truth(liability_shifted_to_performer):
        reasons_ru.append(
            "Законом установлено, что ответственность несёт являющееся непосредственным "
            "исполнителем третье лицо, поэтому должник за его действия не отвечает "
            "(статья 403 ГК РФ)."
        )
    if truth(creditor_fault_established):
        reasons_ru.append(
            "Установлена вина кредитора: неисполнение или ненадлежащее исполнение произошло "
            "по вине обеих сторон либо кредитор умышленно или по неосторожности "
            "содействовал увеличению размера убытков либо не принял разумных мер к их "
            "уменьшению. Суд вправе уменьшить размер ответственности должника "
            "(статья 404 ГК РФ)."
        )
    if truth(debtor_in_delay):
        reasons_ru.append(
            "Должник просрочил исполнение и отвечает перед кредитором за убытки, "
            "причинённые просрочкой, и за последствия случайно наступившей во время "
            "просрочки невозможности исполнения (статья 405 ГК РФ)."
        )
    if truth(creditor_may_refuse_performance):
        reasons_ru.append(
            "Вследствие просрочки должника исполнение утратило интерес для кредитора, "
            "поэтому кредитор вправе отказаться от принятия исполнения и требовать "
            "возмещения убытков (статья 405 ГК РФ)."
        )
    if truth(creditor_in_delay):
        reasons_ru.append(
            "Кредитор просрочил принятие исполнения либо не совершил действий, до "
            "совершения которых должник не мог исполнить обязательство (статья 406 ГК РФ)."
        )
    if truth(creditor_delay_excuses_debtor):
        reasons_ru.append(
            "Должник не считается просрочившим, пока обязательство не может быть исполнено "
            "вследствие просрочки кредитора; ответственность за последующее нарушение на "
            "должника не возлагается (статьи 405 и 406 ГК РФ)."
        )
    return AttributionDelayEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        attribution_qualified=truth(attribution_qualified),
        debtor_answerable_for_employees=truth(debtor_answerable_for_employees),
        debtor_answerable_for_third_party=truth(debtor_answerable_for_third_party),
        liability_shifted_to_performer=truth(liability_shifted_to_performer),
        creditor_fault_established=truth(creditor_fault_established),
        liability_reducible_for_creditor_fault=truth(liability_reducible_for_creditor_fault),
        debtor_in_delay=truth(debtor_in_delay),
        creditor_may_refuse_performance=truth(creditor_may_refuse_performance),
        creditor_in_delay=truth(creditor_in_delay),
        creditor_delay_excuses_debtor=truth(creditor_delay_excuses_debtor),
        requires_human_attribution_assessment=truth(requires_human_attribution_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель называет основания ответственности и просрочки, но не определяет её "
            "размер: уменьшение размера при вине кредитора — право суда, а не расчёт по "
            "заранее известной пропорции (статья 404 ГК РФ).",
            "Утрата интереса кредитора к исполнению и разумность мер к уменьшению убытков "
            "оцениваются экспертом и судом (статьи 404 и 405 ГК РФ).",
        ],
    )
