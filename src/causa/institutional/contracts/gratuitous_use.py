from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


GRATUITOUS_USE_EVIDENCE_SCHEMA_VERSION = "contracts.gratuitous-use-evidence.v0"
GRATUITOUS_USE_MAPPING_VERSION = "contracts-reviewed-gratuitous-use-to-facts-v0"
GRATUITOUS_USE_MODEL_VERSION = "contracts-gratuitous-use-articles-689-701-v0"


class GratuitousUseEvidencePredicate(str, Enum):
    # Понятие и ограничения субъектного состава (статьи 689 и 690 ГК РФ).
    THING_PROVIDED_FOR_FREE_TEMPORARY_USE = "thing_provided_for_free_temporary_use"
    LENDER_IS_ORGANIZATION_TRANSFERRING_TO_INSIDER = (
        "lender_is_organization_transferring_to_insider"
    )
    # Предоставление вещи и её недостатки (статьи 691, 692 и 693 ГК РФ).
    THING_NOT_PROVIDED_OR_INCOMPLETE = "thing_not_provided_or_incomplete"
    DEFECT_INTENTIONALLY_OR_GROSSLY_CONCEALED = "defect_intentionally_or_grossly_concealed"
    THIRD_PARTY_RIGHTS_NOT_DISCLOSED = "third_party_rights_not_disclosed"
    # Содержание вещи и риск (статьи 695 и 696 ГК РФ).
    MAINTENANCE_DUTY_NEGLECTED = "maintenance_duty_neglected"
    ACCIDENTAL_LOSS_RISK_MISALLOCATED = "accidental_loss_risk_misallocated"
    # Досрочное расторжение и отказ (статьи 698, 699 и 700 ГК РФ).
    EARLY_TERMINATION_GROUND_PRESENT = "early_termination_ground_present"
    WITHDRAWAL_NOTICE_PERIOD_NOT_OBSERVED = "withdrawal_notice_period_not_observed"
    THING_ALIENATED_WITHOUT_PRESERVING_USE = "thing_alienated_without_preserving_use"


REQUIRED_GRATUITOUS_USE_PREDICATES = frozenset(GratuitousUseEvidencePredicate)


class GratuitousUseEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: GratuitousUseEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedGratuitousUseEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = GRATUITOUS_USE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[GratuitousUseEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedGratuitousUseEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Gratuitous-use evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Gratuitous-use evidence contains duplicate legal source refs.")
        return self


class GratuitousUseFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    thing_provided_for_free_temporary_use: bool
    lender_is_organization_transferring_to_insider: bool
    thing_not_provided_or_incomplete: bool
    defect_intentionally_or_grossly_concealed: bool
    third_party_rights_not_disclosed: bool
    maintenance_duty_neglected: bool
    accidental_loss_risk_misallocated: bool
    early_termination_ground_present: bool
    withdrawal_notice_period_not_observed: bool
    thing_alienated_without_preserving_use: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "GratuitousUseFactSet":
        if (
            self.lender_is_organization_transferring_to_insider
            and not self.thing_provided_for_free_temporary_use
        ):
            raise ValueError(
                "Запрет передачи вещи учредителю, руководителю или члену органов управления "
                "относится только к договору безвозмездного пользования."
            )
        return self


class GratuitousUseFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class GratuitousUseEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: GratuitousUseFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[GratuitousUseFactProvenance] = Field(default_factory=list)


class GratuitousUseConstraintSet(BaseModel):
    id: str
    model_version: str = GRATUITOUS_USE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class GratuitousUseEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    gratuitous_use_qualified: bool
    prohibited_transfer_to_insider: bool
    delivery_obligation_breached: bool
    lender_liable_for_concealed_defect: bool
    undisclosed_third_party_rights: bool
    maintenance_duty_breached: bool
    accidental_loss_risk_misassigned: bool
    early_termination_available: bool
    withdrawal_notice_period_breached: bool
    use_right_not_preserved_after_transfer: bool
    requires_human_gratuitous_use_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_gratuitous_use_evidence(
    evidence: ReviewedGratuitousUseEvidence,
) -> GratuitousUseEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Gratuitous-use evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Gratuitous-use evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_GRATUITOUS_USE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed gratuitous-use evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_GRATUITOUS_USE_PREDICATES
    }
    return GratuitousUseEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=GRATUITOUS_USE_MAPPING_VERSION,
        facts=GratuitousUseFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            GratuitousUseFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_GRATUITOUS_USE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_gratuitous_use_constraint_set(
    mapping: GratuitousUseEvidenceMappingResult,
) -> GratuitousUseConstraintSet:
    return GratuitousUseConstraintSet(
        id=f"gratuitous-use-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "gratuitous_use_qualified == thing_provided_for_free_temporary_use",
            "prohibited_transfer_to_insider == gratuitous_use_qualified AND lender_is_organization_transferring_to_insider",
            "delivery_obligation_breached == gratuitous_use_qualified AND thing_not_provided_or_incomplete",
            "lender_liable_for_concealed_defect == gratuitous_use_qualified AND defect_intentionally_or_grossly_concealed",
            "undisclosed_third_party_rights == gratuitous_use_qualified AND third_party_rights_not_disclosed",
            "maintenance_duty_breached == gratuitous_use_qualified AND maintenance_duty_neglected",
            "accidental_loss_risk_misassigned == gratuitous_use_qualified AND accidental_loss_risk_misallocated",
            "early_termination_available == gratuitous_use_qualified AND early_termination_ground_present",
            "withdrawal_notice_period_breached == gratuitous_use_qualified AND withdrawal_notice_period_not_observed",
            "use_right_not_preserved_after_transfer == gratuitous_use_qualified AND thing_alienated_without_preserving_use",
            "requires_human_gratuitous_use_assessment == prohibited_transfer_to_insider OR delivery_obligation_breached OR lender_liable_for_concealed_defect OR undisclosed_third_party_rights OR maintenance_duty_breached OR accidental_loss_risk_misassigned OR early_termination_available OR withdrawal_notice_period_breached OR use_right_not_preserved_after_transfer",
        ],
    )


def evaluate_gratuitous_use_constraints(
    constraint_set: GratuitousUseConstraintSet,
    facts: GratuitousUseFactSet,
) -> GratuitousUseEvaluation:
    variables = {field_name: Bool(field_name) for field_name in GratuitousUseFactSet.model_fields}
    gratuitous_use_qualified = Bool("gratuitous_use_qualified")
    prohibited_transfer_to_insider = Bool("prohibited_transfer_to_insider")
    delivery_obligation_breached = Bool("delivery_obligation_breached")
    lender_liable_for_concealed_defect = Bool("lender_liable_for_concealed_defect")
    undisclosed_third_party_rights = Bool("undisclosed_third_party_rights")
    maintenance_duty_breached = Bool("maintenance_duty_breached")
    accidental_loss_risk_misassigned = Bool("accidental_loss_risk_misassigned")
    early_termination_available = Bool("early_termination_available")
    withdrawal_notice_period_breached = Bool("withdrawal_notice_period_breached")
    use_right_not_preserved_after_transfer = Bool("use_right_not_preserved_after_transfer")
    requires_human_gratuitous_use_assessment = Bool("requires_human_gratuitous_use_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(gratuitous_use_qualified == variables["thing_provided_for_free_temporary_use"])
    solver.add(
        prohibited_transfer_to_insider
        == And(
            gratuitous_use_qualified,
            variables["lender_is_organization_transferring_to_insider"],
        )
    )
    solver.add(
        delivery_obligation_breached
        == And(gratuitous_use_qualified, variables["thing_not_provided_or_incomplete"])
    )
    solver.add(
        lender_liable_for_concealed_defect
        == And(gratuitous_use_qualified, variables["defect_intentionally_or_grossly_concealed"])
    )
    solver.add(
        undisclosed_third_party_rights
        == And(gratuitous_use_qualified, variables["third_party_rights_not_disclosed"])
    )
    solver.add(
        maintenance_duty_breached
        == And(gratuitous_use_qualified, variables["maintenance_duty_neglected"])
    )
    solver.add(
        accidental_loss_risk_misassigned
        == And(gratuitous_use_qualified, variables["accidental_loss_risk_misallocated"])
    )
    solver.add(
        early_termination_available
        == And(gratuitous_use_qualified, variables["early_termination_ground_present"])
    )
    solver.add(
        withdrawal_notice_period_breached
        == And(gratuitous_use_qualified, variables["withdrawal_notice_period_not_observed"])
    )
    solver.add(
        use_right_not_preserved_after_transfer
        == And(gratuitous_use_qualified, variables["thing_alienated_without_preserving_use"])
    )
    solver.add(
        requires_human_gratuitous_use_assessment
        == Or(
            prohibited_transfer_to_insider,
            delivery_obligation_breached,
            lender_liable_for_concealed_defect,
            undisclosed_third_party_rights,
            maintenance_duty_breached,
            accidental_loss_risk_misassigned,
            early_termination_available,
            withdrawal_notice_period_breached,
            use_right_not_preserved_after_transfer,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return GratuitousUseEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            gratuitous_use_qualified=False,
            prohibited_transfer_to_insider=False,
            delivery_obligation_breached=False,
            lender_liable_for_concealed_defect=False,
            undisclosed_third_party_rights=False,
            maintenance_duty_breached=False,
            accidental_loss_risk_misassigned=False,
            early_termination_available=False,
            withdrawal_notice_period_breached=False,
            use_right_not_preserved_after_transfer=False,
            requires_human_gratuitous_use_assessment=True,
            reasons_ru=["Набор фактов о безвозмездном пользовании противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как безвозмездное пользование (ссуда): ссудодатель обязуется "
            "передать или передаёт вещь в безвозмездное временное пользование ссудополучателю, "
            "который обязуется вернуть её в том состоянии, в каком получил, с учётом нормального "
            "износа (статья 689 ГК РФ)."
            if truth(gratuitous_use_qualified)
            else "Отношения не квалифицированы как договор безвозмездного пользования."
        ),
    ]
    if truth(prohibited_transfer_to_insider):
        reasons_ru.append(
            "Коммерческая организация не вправе передавать имущество в безвозмездное пользование "
            "своему учредителю, участнику, руководителю, члену её органов управления или "
            "контроля (статья 690 ГК РФ)."
        )
    if truth(delivery_obligation_breached):
        reasons_ru.append(
            "Вещь не предоставлена в состоянии, соответствующем условиям договора и её "
            "назначению, либо предоставлена без принадлежностей и документов; ссудополучатель "
            "вправе потребовать расторжения договора и возмещения реального ущерба "
            "(статьи 691 и 692 ГК РФ)."
        )
    if truth(lender_liable_for_concealed_defect):
        reasons_ru.append(
            "Ссудодатель отвечает за недостатки вещи, которые он умышленно или по грубой "
            "неосторожности не оговорил при заключении договора (статья 693 ГК РФ)."
        )
    if truth(undisclosed_third_party_rights):
        reasons_ru.append(
            "Передача вещи в безвозмездное пользование не является основанием для изменения или "
            "прекращения прав третьих лиц на неё; ссудодатель обязан предупредить о таких правах "
            "(статья 694 ГК РФ)."
        )
    if truth(maintenance_duty_breached):
        reasons_ru.append(
            "Ссудополучатель обязан поддерживать вещь в исправном состоянии, включая "
            "осуществление текущего и капитального ремонта, и нести все расходы на её "
            "содержание, если иное не предусмотрено договором (статья 695 ГК РФ)."
        )
    if truth(accidental_loss_risk_misassigned):
        reasons_ru.append(
            "Риск случайной гибели или повреждения вещи распределён неверно: он несётся "
            "ссудополучателем в установленных законом случаях, включая использование не в "
            "соответствии с договором или передачу третьему лицу без согласия ссудодателя "
            "(статья 696 ГК РФ)."
        )
    if truth(early_termination_available):
        reasons_ru.append(
            "Имеется установленное основание для досрочного расторжения договора "
            "безвозмездного пользования по требованию стороны (статья 698 ГК РФ)."
        )
    if truth(withdrawal_notice_period_breached):
        reasons_ru.append(
            "Отказ от договора безвозмездного пользования требует извещения другой стороны за "
            "один месяц, если договором не предусмотрен иной срок (статья 699 ГК РФ)."
        )
    if truth(use_right_not_preserved_after_transfer):
        reasons_ru.append(
            "При отчуждении вещи или передаче её в возмездное пользование третьему лицу к новому "
            "собственнику или пользователю переходят права по ранее заключённому договору "
            "безвозмездного пользования, а его права обременяются правами ссудополучателя "
            "(статья 700 ГК РФ)."
        )
    return GratuitousUseEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        gratuitous_use_qualified=truth(gratuitous_use_qualified),
        prohibited_transfer_to_insider=truth(prohibited_transfer_to_insider),
        delivery_obligation_breached=truth(delivery_obligation_breached),
        lender_liable_for_concealed_defect=truth(lender_liable_for_concealed_defect),
        undisclosed_third_party_rights=truth(undisclosed_third_party_rights),
        maintenance_duty_breached=truth(maintenance_duty_breached),
        accidental_loss_risk_misassigned=truth(accidental_loss_risk_misassigned),
        early_termination_available=truth(early_termination_available),
        withdrawal_notice_period_breached=truth(withdrawal_notice_period_breached),
        use_right_not_preserved_after_transfer=truth(use_right_not_preserved_after_transfer),
        requires_human_gratuitous_use_assessment=truth(requires_human_gratuitous_use_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о безвозмездном пользовании и не "
            "заменяет судебную оценку.",
            "Состояние вещи, характер недостатков, объём расходов на содержание и основания "
            "досрочного расторжения оцениваются экспертом и судом (статьи 691, 695 и 698 ГК РФ).",
        ],
    )
