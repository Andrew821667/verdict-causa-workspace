from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


GIFT_EVIDENCE_SCHEMA_VERSION = "contracts.gift-evidence.v0"
GIFT_MAPPING_VERSION = "contracts-reviewed-gift-to-facts-v0"
GIFT_MODEL_VERSION = "contracts-gift-articles-572-582-v0"


class GiftEvidencePredicate(str, Enum):
    # Понятие договора дарения (статья 572 ГК РФ).
    GRATUITOUS_TRANSFER_OR_PROMISE = "gratuitous_transfer_or_promise"
    COUNTER_OBLIGATION_PRESENT = "counter_obligation_present"
    # Форма договора дарения (статья 574 ГК РФ).
    WRITTEN_FORM_REQUIRED = "written_form_required"
    WRITTEN_FORM_SATISFIED = "written_form_satisfied"
    # Запрещение и ограничения дарения (статьи 575 и 576 ГК РФ).
    DONATION_STATUTORILY_PROHIBITED = "donation_statutorily_prohibited"
    RESTRICTION_CONSENT_MISSING = "restriction_consent_missing"
    # Отказ одаряемого и отмена дарения (статьи 573, 577–579 ГК РФ).
    DONEE_REFUSED_BEFORE_DELIVERY = "donee_refused_before_delivery"
    DONOR_REVOCATION_GROUND_PRESENT = "donor_revocation_ground_present"
    ORDINARY_LOW_VALUE_GIFT = "ordinary_low_value_gift"
    # Пожертвование (статья 582 ГК РФ).
    CHARITABLE_DONATION_PURPOSE_VIOLATED = "charitable_donation_purpose_violated"


REQUIRED_GIFT_PREDICATES = frozenset(GiftEvidencePredicate)


class GiftEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: GiftEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedGiftEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = GIFT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[GiftEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedGiftEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Gift evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Gift evidence contains duplicate legal source refs.")
        return self


class GiftFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    gratuitous_transfer_or_promise: bool
    counter_obligation_present: bool
    written_form_required: bool
    written_form_satisfied: bool
    donation_statutorily_prohibited: bool
    restriction_consent_missing: bool
    donee_refused_before_delivery: bool
    donor_revocation_ground_present: bool
    ordinary_low_value_gift: bool
    charitable_donation_purpose_violated: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "GiftFactSet":
        if self.charitable_donation_purpose_violated and not self.gratuitous_transfer_or_promise:
            raise ValueError(
                "Нарушение назначения пожертвования учитывается только при безвозмездной передаче."
            )
        if self.donee_refused_before_delivery and not self.gratuitous_transfer_or_promise:
            raise ValueError(
                "Отказ одаряемого от дара учитывается только при безвозмездной передаче."
            )
        return self


class GiftFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class GiftEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: GiftFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[GiftFactProvenance] = Field(default_factory=list)


class GiftConstraintSet(BaseModel):
    id: str
    model_version: str = GIFT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class GiftEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    gift_qualified: bool
    sham_due_to_counter_obligation: bool
    form_defect_makes_void: bool
    donation_prohibited: bool
    restriction_violated: bool
    donee_refusal_terminates: bool
    revocation_available: bool
    charitable_revocation_available: bool
    requires_human_gift_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_gift_evidence(
    evidence: ReviewedGiftEvidence,
) -> GiftEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Gift evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Gift evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(predicate.value for predicate in REQUIRED_GIFT_PREDICATES - assertions.keys())
    if missing:
        raise ValueError(
            "Reviewed gift evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_GIFT_PREDICATES
    }
    return GiftEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=GIFT_MAPPING_VERSION,
        facts=GiftFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            GiftFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_GIFT_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_gift_constraint_set(
    mapping: GiftEvidenceMappingResult,
) -> GiftConstraintSet:
    return GiftConstraintSet(
        id=f"gift-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "gift_qualified == gratuitous_transfer_or_promise AND NOT counter_obligation_present",
            "sham_due_to_counter_obligation == gratuitous_transfer_or_promise AND counter_obligation_present",
            "form_defect_makes_void == written_form_required AND NOT written_form_satisfied",
            "donation_prohibited == gift_qualified AND donation_statutorily_prohibited AND NOT ordinary_low_value_gift",
            "restriction_violated == gift_qualified AND restriction_consent_missing",
            "donee_refusal_terminates == gift_qualified AND donee_refused_before_delivery",
            "revocation_available == gift_qualified AND donor_revocation_ground_present AND NOT ordinary_low_value_gift",
            "charitable_revocation_available == gift_qualified AND charitable_donation_purpose_violated",
            "requires_human_gift_assessment == sham_due_to_counter_obligation OR form_defect_makes_void OR donation_prohibited OR restriction_violated OR revocation_available OR charitable_revocation_available",
        ],
    )


def evaluate_gift_constraints(
    constraint_set: GiftConstraintSet,
    facts: GiftFactSet,
) -> GiftEvaluation:
    variables = {field_name: Bool(field_name) for field_name in GiftFactSet.model_fields}
    gift_qualified = Bool("gift_qualified")
    sham_due_to_counter_obligation = Bool("sham_due_to_counter_obligation")
    form_defect_makes_void = Bool("form_defect_makes_void")
    donation_prohibited = Bool("donation_prohibited")
    restriction_violated = Bool("restriction_violated")
    donee_refusal_terminates = Bool("donee_refusal_terminates")
    revocation_available = Bool("revocation_available")
    charitable_revocation_available = Bool("charitable_revocation_available")
    requires_human_gift_assessment = Bool("requires_human_gift_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        gift_qualified
        == And(
            variables["gratuitous_transfer_or_promise"],
            Not(variables["counter_obligation_present"]),
        )
    )
    solver.add(
        sham_due_to_counter_obligation
        == And(
            variables["gratuitous_transfer_or_promise"],
            variables["counter_obligation_present"],
        )
    )
    solver.add(
        form_defect_makes_void
        == And(variables["written_form_required"], Not(variables["written_form_satisfied"]))
    )
    solver.add(
        donation_prohibited
        == And(
            gift_qualified,
            variables["donation_statutorily_prohibited"],
            Not(variables["ordinary_low_value_gift"]),
        )
    )
    solver.add(
        restriction_violated == And(gift_qualified, variables["restriction_consent_missing"])
    )
    solver.add(
        donee_refusal_terminates == And(gift_qualified, variables["donee_refused_before_delivery"])
    )
    solver.add(
        revocation_available
        == And(
            gift_qualified,
            variables["donor_revocation_ground_present"],
            Not(variables["ordinary_low_value_gift"]),
        )
    )
    solver.add(
        charitable_revocation_available
        == And(gift_qualified, variables["charitable_donation_purpose_violated"])
    )
    solver.add(
        requires_human_gift_assessment
        == Or(
            sham_due_to_counter_obligation,
            form_defect_makes_void,
            donation_prohibited,
            restriction_violated,
            revocation_available,
            charitable_revocation_available,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return GiftEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            gift_qualified=False,
            sham_due_to_counter_obligation=False,
            form_defect_makes_void=False,
            donation_prohibited=False,
            restriction_violated=False,
            donee_refusal_terminates=False,
            revocation_available=False,
            charitable_revocation_available=False,
            requires_human_gift_assessment=True,
            reasons_ru=["Набор фактов о дарении противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как дарение: даритель безвозмездно передаёт или обязуется "
            "передать одаряемому вещь или имущественное право либо освобождает от обязанности "
            "(статья 572 ГК РФ)."
            if truth(gift_qualified)
            else "Отношения не квалифицированы как договор дарения."
        ),
    ]
    if truth(sham_due_to_counter_obligation):
        reasons_ru.append(
            "При наличии встречной передачи вещи или права либо встречного обязательства "
            "договор не признаётся дарением (притворная сделка) (статья 572 ГК РФ)."
        )
    if truth(form_defect_makes_void):
        reasons_ru.append(
            "Несоблюдение требуемой письменной формы договора дарения влечёт его ничтожность "
            "(статья 574 ГК РФ)."
        )
    if truth(donation_prohibited):
        reasons_ru.append(
            "Дарение запрещено по статье 575 ГК РФ и не относится к обычным подаркам небольшой "
            "стоимости."
        )
    if truth(restriction_violated):
        reasons_ru.append(
            "Ограничение дарения нарушено: не получено необходимое согласие собственника или "
            "участников общей собственности (статья 576 ГК РФ)."
        )
    if truth(donee_refusal_terminates):
        reasons_ru.append(
            "Одаряемый отказался принять дар до его передачи; договор считается расторгнутым "
            "(статья 573 ГК РФ)."
        )
    if truth(revocation_available):
        reasons_ru.append(
            "Имеется основание для отказа от исполнения или отмены дарения; к обычным подаркам "
            "небольшой стоимости эти правила не применяются (статьи 577–579 ГК РФ)."
        )
    if truth(charitable_revocation_available):
        reasons_ru.append(
            "При использовании пожертвованного имущества не по назначению жертвователь вправе "
            "требовать отмены пожертвования (статья 582 ГК РФ)."
        )
    return GiftEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        gift_qualified=truth(gift_qualified),
        sham_due_to_counter_obligation=truth(sham_due_to_counter_obligation),
        form_defect_makes_void=truth(form_defect_makes_void),
        donation_prohibited=truth(donation_prohibited),
        restriction_violated=truth(restriction_violated),
        donee_refusal_terminates=truth(donee_refusal_terminates),
        revocation_available=truth(revocation_available),
        charitable_revocation_available=truth(charitable_revocation_available),
        requires_human_gift_assessment=truth(requires_human_gift_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о дарении и не заменяет судебную оценку.",
            "Стоимость дара, наличие оснований отмены и возмещение вреда от недостатков "
            "подаренной вещи оцениваются экспертом и судом (статьи 580–581 ГК РФ).",
        ],
    )
