from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


STORAGE_EVIDENCE_SCHEMA_VERSION = "contracts.storage-evidence.v0"
STORAGE_MAPPING_VERSION = "contracts-reviewed-storage-to-facts-v0"
STORAGE_MODEL_VERSION = "contracts-storage-articles-886-906-v0"


class StorageEvidencePredicate(str, Enum):
    # Договор хранения и его форма (статьи 886 и 887 ГК РФ).
    THING_ACCEPTED_FOR_STORAGE_AND_RETURN = "thing_accepted_for_storage_and_return"
    STORAGE_WRITTEN_FORM_NOT_OBSERVED = "storage_written_form_not_observed"
    # Принятие вещи на хранение и срок хранения (статьи 888 и 889 ГК РФ).
    ACCEPTANCE_OF_THING_REFUSED_WITHOUT_GROUNDS = "acceptance_of_thing_refused_without_grounds"
    STORAGE_PERIOD_RULES_BREACHED = "storage_period_rules_breached"
    # Обеспечение сохранности и пользование вещью (статьи 891 и 892 ГК РФ).
    SAFEKEEPING_MEASURES_NOT_TAKEN = "safekeeping_measures_not_taken"
    CUSTODIAN_USED_THING_WITHOUT_CONSENT = "custodian_used_thing_without_consent"
    # Изменение условий хранения и передача вещи третьему лицу (статьи 893 и 895 ГК РФ).
    STORAGE_CHANGE_OR_TRANSFER_NOT_NOTIFIED = "storage_change_or_transfer_not_notified"
    # Вознаграждение и расходы на хранение (статьи 896–898 ГК РФ).
    STORAGE_REMUNERATION_AND_EXPENSES_BREACHED = "storage_remuneration_and_expenses_breached"
    # Возврат вещи и ответственность хранителя (статьи 899–902 ГК РФ).
    THING_RETURN_DUTY_BREACHED = "thing_return_duty_breached"
    CUSTODIAN_LIABILITY_RULES_BREACHED = "custodian_liability_rules_breached"


REQUIRED_STORAGE_PREDICATES = frozenset(StorageEvidencePredicate)


class StorageEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: StorageEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedStorageEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = STORAGE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[StorageEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedStorageEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Storage evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Storage evidence contains duplicate legal source refs.")
        return self


class StorageFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    thing_accepted_for_storage_and_return: bool
    storage_written_form_not_observed: bool
    acceptance_of_thing_refused_without_grounds: bool
    storage_period_rules_breached: bool
    safekeeping_measures_not_taken: bool
    custodian_used_thing_without_consent: bool
    storage_change_or_transfer_not_notified: bool
    storage_remuneration_and_expenses_breached: bool
    thing_return_duty_breached: bool
    custodian_liability_rules_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "StorageFactSet":
        if self.custodian_liability_rules_breached and not self.safekeeping_measures_not_taken:
            raise ValueError(
                "Нарушение правил об ответственности хранителя относится только к случаю, когда "
                "непринятие мер по обеспечению сохранности вещи установлено."
            )
        if (
            self.storage_written_form_not_observed
            and not self.thing_accepted_for_storage_and_return
        ):
            raise ValueError("Несоблюдение письменной формы относится только к договору хранения.")
        return self


class StorageFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class StorageEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: StorageFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[StorageFactProvenance] = Field(default_factory=list)


class StorageConstraintSet(BaseModel):
    id: str
    model_version: str = STORAGE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class StorageEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    storage_qualified: bool
    storage_form_breached: bool
    acceptance_duty_breached: bool
    storage_period_duty_breached: bool
    safekeeping_duty_breached: bool
    unauthorised_use_established: bool
    storage_change_notice_duty_breached: bool
    remuneration_and_expenses_duty_breached: bool
    return_duty_breached: bool
    custodian_liability_breached: bool
    requires_human_storage_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_storage_evidence(
    evidence: ReviewedStorageEvidence,
) -> StorageEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Storage evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Storage evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_STORAGE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed storage evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_STORAGE_PREDICATES
    }
    return StorageEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=STORAGE_MAPPING_VERSION,
        facts=StorageFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            StorageFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_STORAGE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_storage_constraint_set(
    mapping: StorageEvidenceMappingResult,
) -> StorageConstraintSet:
    return StorageConstraintSet(
        id=f"storage-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "storage_qualified == thing_accepted_for_storage_and_return",
            "storage_form_breached == storage_qualified AND storage_written_form_not_observed",
            "acceptance_duty_breached == storage_qualified AND acceptance_of_thing_refused_without_grounds",
            "storage_period_duty_breached == storage_qualified AND storage_period_rules_breached",
            "safekeeping_duty_breached == storage_qualified AND safekeeping_measures_not_taken",
            "unauthorised_use_established == storage_qualified AND custodian_used_thing_without_consent",
            "storage_change_notice_duty_breached == storage_qualified AND storage_change_or_transfer_not_notified",
            "remuneration_and_expenses_duty_breached == storage_qualified AND storage_remuneration_and_expenses_breached",
            "return_duty_breached == storage_qualified AND thing_return_duty_breached",
            "custodian_liability_breached == storage_qualified AND safekeeping_measures_not_taken AND custodian_liability_rules_breached",
            "requires_human_storage_assessment == storage_form_breached OR acceptance_duty_breached OR storage_period_duty_breached OR safekeeping_duty_breached OR unauthorised_use_established OR storage_change_notice_duty_breached OR remuneration_and_expenses_duty_breached OR return_duty_breached",
        ],
    )


def evaluate_storage_constraints(
    constraint_set: StorageConstraintSet,
    facts: StorageFactSet,
) -> StorageEvaluation:
    variables = {field_name: Bool(field_name) for field_name in StorageFactSet.model_fields}
    storage_qualified = Bool("storage_qualified")
    storage_form_breached = Bool("storage_form_breached")
    acceptance_duty_breached = Bool("acceptance_duty_breached")
    storage_period_duty_breached = Bool("storage_period_duty_breached")
    safekeeping_duty_breached = Bool("safekeeping_duty_breached")
    unauthorised_use_established = Bool("unauthorised_use_established")
    storage_change_notice_duty_breached = Bool("storage_change_notice_duty_breached")
    remuneration_and_expenses_duty_breached = Bool("remuneration_and_expenses_duty_breached")
    return_duty_breached = Bool("return_duty_breached")
    custodian_liability_breached = Bool("custodian_liability_breached")
    requires_human_storage_assessment = Bool("requires_human_storage_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(storage_qualified == variables["thing_accepted_for_storage_and_return"])
    solver.add(
        storage_form_breached
        == And(storage_qualified, variables["storage_written_form_not_observed"])
    )
    solver.add(
        acceptance_duty_breached
        == And(storage_qualified, variables["acceptance_of_thing_refused_without_grounds"])
    )
    solver.add(
        storage_period_duty_breached
        == And(storage_qualified, variables["storage_period_rules_breached"])
    )
    solver.add(
        safekeeping_duty_breached
        == And(storage_qualified, variables["safekeeping_measures_not_taken"])
    )
    solver.add(
        unauthorised_use_established
        == And(storage_qualified, variables["custodian_used_thing_without_consent"])
    )
    solver.add(
        storage_change_notice_duty_breached
        == And(storage_qualified, variables["storage_change_or_transfer_not_notified"])
    )
    solver.add(
        remuneration_and_expenses_duty_breached
        == And(storage_qualified, variables["storage_remuneration_and_expenses_breached"])
    )
    solver.add(
        return_duty_breached == And(storage_qualified, variables["thing_return_duty_breached"])
    )
    solver.add(
        custodian_liability_breached
        == And(
            storage_qualified,
            variables["safekeeping_measures_not_taken"],
            variables["custodian_liability_rules_breached"],
        )
    )
    solver.add(
        requires_human_storage_assessment
        == Or(
            storage_form_breached,
            acceptance_duty_breached,
            storage_period_duty_breached,
            safekeeping_duty_breached,
            unauthorised_use_established,
            storage_change_notice_duty_breached,
            remuneration_and_expenses_duty_breached,
            return_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return StorageEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            storage_qualified=False,
            storage_form_breached=False,
            acceptance_duty_breached=False,
            storage_period_duty_breached=False,
            safekeeping_duty_breached=False,
            unauthorised_use_established=False,
            storage_change_notice_duty_breached=False,
            remuneration_and_expenses_duty_breached=False,
            return_duty_breached=False,
            custodian_liability_breached=False,
            requires_human_storage_assessment=True,
            reasons_ru=["Набор фактов о хранении противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как договор хранения: хранитель обязуется хранить вещь, "
            "переданную ему поклажедателем, и возвратить эту вещь в сохранности "
            "(статья 886 ГК РФ)."
            if truth(storage_qualified)
            else "Отношения не квалифицированы как договор хранения."
        ),
    ]
    if truth(storage_form_breached):
        reasons_ru.append(
            "Договор хранения должен быть заключён в письменной форме в предусмотренных законом "
            "случаях; простая письменная форма считается соблюдённой при выдаче сохранной "
            "расписки, квитанции, свидетельства или иного документа, подписанного хранителем "
            "(статья 887 ГК РФ)."
        )
    if truth(acceptance_duty_breached):
        reasons_ru.append(
            "Хранитель, обязавшийся принять вещь на хранение, не вправе требовать её передачи, "
            "однако поклажедатель, не передавший вещь в предусмотренный срок, отвечает за убытки, "
            "а хранитель освобождается от обязанности принять вещь в установленных случаях "
            "(статья 888 ГК РФ)."
        )
    if truth(storage_period_duty_breached):
        reasons_ru.append(
            "Хранитель обязан хранить вещь в течение обусловленного срока, а при отсутствии срока "
            "— до востребования вещи поклажедателем (статья 889 ГК РФ)."
        )
    if truth(safekeeping_duty_breached):
        reasons_ru.append(
            "Хранитель обязан принять все предусмотренные договором меры, а также меры, "
            "соответствующие обязательным нормам и обычаям делового оборота, чтобы обеспечить "
            "сохранность переданной на хранение вещи (статья 891 ГК РФ)."
        )
    if truth(unauthorised_use_established):
        reasons_ru.append(
            "Хранитель не вправе без согласия поклажедателя пользоваться переданной на хранение "
            "вещью и предоставлять возможность пользования ею третьим лицам, за исключением "
            "случаев, когда это необходимо для обеспечения сохранности вещи "
            "(статья 892 ГК РФ)."
        )
    if truth(storage_change_notice_duty_breached):
        reasons_ru.append(
            "Хранитель обязан незамедлительно уведомить поклажедателя об изменении условий "
            "хранения и вправе передать вещь на хранение третьему лицу только в предусмотренных "
            "законом случаях с извещением поклажедателя (статьи 893 и 895 ГК РФ)."
        )
    if truth(remuneration_and_expenses_duty_breached):
        reasons_ru.append(
            "Вознаграждение за хранение выплачивается по окончании хранения или по периодам, "
            "расходы на хранение включаются в вознаграждение, если иное не предусмотрено "
            "договором, а чрезвычайные расходы возмещаются в установленном порядке "
            "(статьи 896–898 ГК РФ)."
        )
    if truth(return_duty_breached):
        reasons_ru.append(
            "Поклажедатель обязан взять вещь обратно по истечении срока хранения, а хранитель "
            "обязан возвратить ту самую вещь в том состоянии, в каком она была принята, с учётом "
            "естественного ухудшения и естественной убыли (статьи 899 и 900 ГК РФ)."
        )
    if truth(custodian_liability_breached):
        reasons_ru.append(
            "Хранитель отвечает за утрату, недостачу или повреждение вещей по основаниям, "
            "предусмотренным статьёй 401 ГК РФ, а профессиональный хранитель — независимо от "
            "вины в установленных пределах; размер ответственности определяется статьёй 902 "
            "ГК РФ (статьи 901 и 902 ГК РФ)."
        )
    return StorageEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        storage_qualified=truth(storage_qualified),
        storage_form_breached=truth(storage_form_breached),
        acceptance_duty_breached=truth(acceptance_duty_breached),
        storage_period_duty_breached=truth(storage_period_duty_breached),
        safekeeping_duty_breached=truth(safekeeping_duty_breached),
        unauthorised_use_established=truth(unauthorised_use_established),
        storage_change_notice_duty_breached=truth(storage_change_notice_duty_breached),
        remuneration_and_expenses_duty_breached=truth(remuneration_and_expenses_duty_breached),
        return_duty_breached=truth(return_duty_breached),
        custodian_liability_breached=truth(custodian_liability_breached),
        requires_human_storage_assessment=truth(requires_human_storage_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только общие положения о хранении и не заменяет судебную оценку.",
            "Достаточность принятых мер по обеспечению сохранности, необходимость чрезвычайных "
            "расходов и наличие вины хранителя оцениваются экспертом и судом "
            "(статьи 891, 898 и 901 ГК РФ).",
        ],
    )
