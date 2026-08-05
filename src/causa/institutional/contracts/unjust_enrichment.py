from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


UNJUST_ENRICHMENT_EVIDENCE_SCHEMA_VERSION = "contracts.unjust-enrichment-evidence.v0"
UNJUST_ENRICHMENT_MAPPING_VERSION = "contracts-reviewed-unjust-enrichment-to-facts-v0"
UNJUST_ENRICHMENT_MODEL_VERSION = "contracts-unjust-enrichment-articles-1102-1109-v0"


class UnjustEnrichmentEvidencePredicate(str, Enum):
    # Обязанность возвратить неосновательное обогащение (статья 1102 ГК РФ).
    UNJUST_ENRICHMENT_ESTABLISHED = "unjust_enrichment_established"
    RESTITUTION_DUTY_BREACHED = "restitution_duty_breached"
    IRRELEVANCE_OF_CAUSE_DISREGARDED = "irrelevance_of_cause_disregarded"
    # Соотношение с другими требованиями о защите прав (статья 1103 ГК РФ).
    SUBSIDIARY_APPLICATION_RULES_BREACHED = "subsidiary_application_rules_breached"
    # Возвращение неосновательного обогащения в натуре и возмещение стоимости
    # (статьи 1104 и 1105 ГК РФ).
    RETURN_IN_KIND_RULES_BREACHED = "return_in_kind_rules_breached"
    VALUE_COMPENSATION_RULES_BREACHED = "value_compensation_rules_breached"
    # Последствия неосновательной передачи права другому лицу (статья 1106 ГК РФ).
    TRANSFERRED_RIGHT_RESTORATION_BREACHED = "transferred_right_restoration_breached"
    # Возмещение доходов и затрат на имущество (статьи 1107 и 1108 ГК РФ).
    INCOME_AND_INTEREST_RULES_BREACHED = "income_and_interest_rules_breached"
    MAINTENANCE_COSTS_REIMBURSEMENT_BREACHED = "maintenance_costs_reimbursement_breached"
    # Неосновательное обогащение, не подлежащее возврату (статья 1109 ГК РФ).
    NON_RETURNABLE_ENRICHMENT_NOT_APPLIED = "non_returnable_enrichment_not_applied"


REQUIRED_UNJUST_ENRICHMENT_PREDICATES = frozenset(UnjustEnrichmentEvidencePredicate)


class UnjustEnrichmentEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: UnjustEnrichmentEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedUnjustEnrichmentEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = UNJUST_ENRICHMENT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[UnjustEnrichmentEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedUnjustEnrichmentEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Unjust-enrichment evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Unjust-enrichment evidence contains duplicate legal source refs.")
        return self


class UnjustEnrichmentFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    unjust_enrichment_established: bool
    restitution_duty_breached: bool
    irrelevance_of_cause_disregarded: bool
    subsidiary_application_rules_breached: bool
    return_in_kind_rules_breached: bool
    value_compensation_rules_breached: bool
    transferred_right_restoration_breached: bool
    income_and_interest_rules_breached: bool
    maintenance_costs_reimbursement_breached: bool
    non_returnable_enrichment_not_applied: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "UnjustEnrichmentFactSet":
        if self.non_returnable_enrichment_not_applied and not self.restitution_duty_breached:
            raise ValueError(
                "Неприменение правил об имуществе, не подлежащем возврату, относится только к "
                "случаю, когда нарушение обязанности возвратить неосновательное обогащение "
                "установлено."
            )
        if self.irrelevance_of_cause_disregarded and not self.unjust_enrichment_established:
            raise ValueError(
                "Неучёт независимости обязанности возврата от причин обогащения относится "
                "только к случаю, когда неосновательное обогащение установлено."
            )
        return self


class UnjustEnrichmentFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class UnjustEnrichmentEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: UnjustEnrichmentFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[UnjustEnrichmentFactProvenance] = Field(default_factory=list)


class UnjustEnrichmentConstraintSet(BaseModel):
    id: str
    model_version: str = UNJUST_ENRICHMENT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class UnjustEnrichmentEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    unjust_enrichment_qualified: bool
    restitution_duty_breach_established: bool
    irrelevance_of_cause_duty_breached: bool
    subsidiary_application_duty_breached: bool
    return_in_kind_duty_breached: bool
    value_compensation_duty_breached: bool
    transferred_right_duty_breached: bool
    income_and_interest_duty_breached: bool
    maintenance_costs_duty_breached: bool
    non_returnable_enrichment_breached: bool
    requires_human_unjust_enrichment_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_unjust_enrichment_evidence(
    evidence: ReviewedUnjustEnrichmentEvidence,
) -> UnjustEnrichmentEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Unjust-enrichment evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Unjust-enrichment evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_UNJUST_ENRICHMENT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed unjust-enrichment evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_UNJUST_ENRICHMENT_PREDICATES
    }
    return UnjustEnrichmentEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=UNJUST_ENRICHMENT_MAPPING_VERSION,
        facts=UnjustEnrichmentFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            UnjustEnrichmentFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_UNJUST_ENRICHMENT_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_unjust_enrichment_constraint_set(
    mapping: UnjustEnrichmentEvidenceMappingResult,
) -> UnjustEnrichmentConstraintSet:
    return UnjustEnrichmentConstraintSet(
        id=f"unjust-enrichment-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "unjust_enrichment_qualified == unjust_enrichment_established",
            "restitution_duty_breach_established == unjust_enrichment_qualified AND restitution_duty_breached",
            "irrelevance_of_cause_duty_breached == unjust_enrichment_qualified AND irrelevance_of_cause_disregarded",
            "subsidiary_application_duty_breached == unjust_enrichment_qualified AND subsidiary_application_rules_breached",
            "return_in_kind_duty_breached == unjust_enrichment_qualified AND return_in_kind_rules_breached",
            "value_compensation_duty_breached == unjust_enrichment_qualified AND value_compensation_rules_breached",
            "transferred_right_duty_breached == unjust_enrichment_qualified AND transferred_right_restoration_breached",
            "income_and_interest_duty_breached == unjust_enrichment_qualified AND income_and_interest_rules_breached",
            "maintenance_costs_duty_breached == unjust_enrichment_qualified AND maintenance_costs_reimbursement_breached",
            "non_returnable_enrichment_breached == unjust_enrichment_qualified AND restitution_duty_breached AND non_returnable_enrichment_not_applied",
            "requires_human_unjust_enrichment_assessment == restitution_duty_breach_established OR irrelevance_of_cause_duty_breached OR subsidiary_application_duty_breached OR return_in_kind_duty_breached OR value_compensation_duty_breached OR transferred_right_duty_breached OR income_and_interest_duty_breached OR maintenance_costs_duty_breached",
        ],
    )


def evaluate_unjust_enrichment_constraints(
    constraint_set: UnjustEnrichmentConstraintSet,
    facts: UnjustEnrichmentFactSet,
) -> UnjustEnrichmentEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in UnjustEnrichmentFactSet.model_fields
    }
    unjust_enrichment_qualified = Bool("unjust_enrichment_qualified")
    restitution_duty_breach_established = Bool("restitution_duty_breach_established")
    irrelevance_of_cause_duty_breached = Bool("irrelevance_of_cause_duty_breached")
    subsidiary_application_duty_breached = Bool("subsidiary_application_duty_breached")
    return_in_kind_duty_breached = Bool("return_in_kind_duty_breached")
    value_compensation_duty_breached = Bool("value_compensation_duty_breached")
    transferred_right_duty_breached = Bool("transferred_right_duty_breached")
    income_and_interest_duty_breached = Bool("income_and_interest_duty_breached")
    maintenance_costs_duty_breached = Bool("maintenance_costs_duty_breached")
    non_returnable_enrichment_breached = Bool("non_returnable_enrichment_breached")
    requires_human_unjust_enrichment_assessment = Bool(
        "requires_human_unjust_enrichment_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(unjust_enrichment_qualified == variables["unjust_enrichment_established"])
    solver.add(
        restitution_duty_breach_established
        == And(unjust_enrichment_qualified, variables["restitution_duty_breached"])
    )
    solver.add(
        irrelevance_of_cause_duty_breached
        == And(unjust_enrichment_qualified, variables["irrelevance_of_cause_disregarded"])
    )
    solver.add(
        subsidiary_application_duty_breached
        == And(unjust_enrichment_qualified, variables["subsidiary_application_rules_breached"])
    )
    solver.add(
        return_in_kind_duty_breached
        == And(unjust_enrichment_qualified, variables["return_in_kind_rules_breached"])
    )
    solver.add(
        value_compensation_duty_breached
        == And(unjust_enrichment_qualified, variables["value_compensation_rules_breached"])
    )
    solver.add(
        transferred_right_duty_breached
        == And(unjust_enrichment_qualified, variables["transferred_right_restoration_breached"])
    )
    solver.add(
        income_and_interest_duty_breached
        == And(unjust_enrichment_qualified, variables["income_and_interest_rules_breached"])
    )
    solver.add(
        maintenance_costs_duty_breached
        == And(unjust_enrichment_qualified, variables["maintenance_costs_reimbursement_breached"])
    )
    solver.add(
        non_returnable_enrichment_breached
        == And(
            unjust_enrichment_qualified,
            variables["restitution_duty_breached"],
            variables["non_returnable_enrichment_not_applied"],
        )
    )
    solver.add(
        requires_human_unjust_enrichment_assessment
        == Or(
            restitution_duty_breach_established,
            irrelevance_of_cause_duty_breached,
            subsidiary_application_duty_breached,
            return_in_kind_duty_breached,
            value_compensation_duty_breached,
            transferred_right_duty_breached,
            income_and_interest_duty_breached,
            maintenance_costs_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return UnjustEnrichmentEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            unjust_enrichment_qualified=False,
            restitution_duty_breach_established=False,
            irrelevance_of_cause_duty_breached=False,
            subsidiary_application_duty_breached=False,
            return_in_kind_duty_breached=False,
            value_compensation_duty_breached=False,
            transferred_right_duty_breached=False,
            income_and_interest_duty_breached=False,
            maintenance_costs_duty_breached=False,
            non_returnable_enrichment_breached=False,
            requires_human_unjust_enrichment_assessment=True,
            reasons_ru=["Набор фактов о неосновательном обогащении противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Установлено неосновательное обогащение: лицо, которое без установленных законом, "
            "иными правовыми актами или сделкой оснований приобрело или сберегло имущество за "
            "счёт другого лица, обязано возвратить последнему неосновательно приобретённое или "
            "сбережённое имущество (статья 1102 ГК РФ)."
            if truth(unjust_enrichment_qualified)
            else "Неосновательное обогащение не установлено."
        ),
    ]
    if truth(restitution_duty_breach_established):
        reasons_ru.append(
            "Приобретатель обязан возвратить потерпевшему неосновательно приобретённое или "
            "сбережённое имущество за исключением случаев, предусмотренных статьёй 1109 ГК РФ "
            "(статья 1102 ГК РФ)."
        )
    if truth(irrelevance_of_cause_duty_breached):
        reasons_ru.append(
            "Правила о неосновательном обогащении применяются независимо от того, явилось ли "
            "неосновательное обогащение результатом поведения приобретателя имущества, самого "
            "потерпевшего, третьих лиц или произошло помимо их воли (статья 1102 ГК РФ)."
        )
    if truth(subsidiary_application_duty_breached):
        reasons_ru.append(
            "Правила о неосновательном обогащении подлежат применению также к требованиям о "
            "возврате исполненного по недействительной сделке, об истребовании имущества "
            "собственником из чужого незаконного владения, одной стороны обязательства к "
            "другой о возврате исполненного и о возмещении вреда, если иное не установлено "
            "законом и не вытекает из существа отношений (статья 1103 ГК РФ)."
        )
    if truth(return_in_kind_duty_breached):
        reasons_ru.append(
            "Имущество, составляющее неосновательное обогащение приобретателя, должно быть "
            "возвращено потерпевшему в натуре, а приобретатель отвечает за всякие недостачу или "
            "ухудшение такого имущества после того, как узнал или должен был узнать о "
            "неосновательности обогащения (статья 1104 ГК РФ)."
        )
    if truth(value_compensation_duty_breached):
        reasons_ru.append(
            "При невозможности возвратить в натуре неосновательно полученное или сбережённое "
            "имущество приобретатель должен возместить потерпевшему действительную стоимость "
            "этого имущества на момент его приобретения, а также убытки, вызванные последующим "
            "изменением стоимости имущества (статья 1105 ГК РФ)."
        )
    if truth(transferred_right_duty_breached):
        reasons_ru.append(
            "Лицо, передавшее путём уступки требования или иным образом принадлежащее ему право "
            "другому лицу на основании несуществующего или недействительного обязательства, "
            "вправе требовать восстановления прежнего положения, в том числе возвращения ему "
            "документов, удостоверяющих переданное право (статья 1106 ГК РФ)."
        )
    if truth(income_and_interest_duty_breached):
        reasons_ru.append(
            "Приобретатель обязан возвратить или возместить потерпевшему все доходы, которые он "
            "извлёк или должен был извлечь из имущества с того времени, когда узнал или должен "
            "был узнать о неосновательности обогащения; на сумму неосновательного денежного "
            "обогащения подлежат начислению проценты за пользование чужими средствами "
            "(статья 1107 ГК РФ)."
        )
    if truth(maintenance_costs_duty_breached):
        reasons_ru.append(
            "При возврате неосновательно полученного или сбережённого имущества приобретатель "
            "вправе требовать от потерпевшего возмещения понесённых необходимых затрат на "
            "содержание и сохранение имущества с того времени, с которого он обязан возвратить "
            "доходы, с зачётом полученных им выгод (статья 1108 ГК РФ)."
        )
    if truth(non_returnable_enrichment_breached):
        reasons_ru.append(
            "Не подлежат возврату в качестве неосновательного обогащения имущество, переданное "
            "во исполнение обязательства до наступления срока исполнения, имущество, переданное "
            "во исполнение обязательства по истечении срока исковой давности, заработная плата "
            "и приравненные к ней платежи при отсутствии недобросовестности и счётной ошибки, а "
            "также денежные суммы и иное имущество, предоставленные во исполнение "
            "несуществующего обязательства, если приобретатель докажет, что лицо, требующее "
            "возврата, знало об отсутствии обязательства либо предоставило имущество в целях "
            "благотворительности (статья 1109 ГК РФ)."
        )
    return UnjustEnrichmentEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        unjust_enrichment_qualified=truth(unjust_enrichment_qualified),
        restitution_duty_breach_established=truth(restitution_duty_breach_established),
        irrelevance_of_cause_duty_breached=truth(irrelevance_of_cause_duty_breached),
        subsidiary_application_duty_breached=truth(subsidiary_application_duty_breached),
        return_in_kind_duty_breached=truth(return_in_kind_duty_breached),
        value_compensation_duty_breached=truth(value_compensation_duty_breached),
        transferred_right_duty_breached=truth(transferred_right_duty_breached),
        income_and_interest_duty_breached=truth(income_and_interest_duty_breached),
        maintenance_costs_duty_breached=truth(maintenance_costs_duty_breached),
        non_returnable_enrichment_breached=truth(non_returnable_enrichment_breached),
        requires_human_unjust_enrichment_assessment=truth(
            requires_human_unjust_enrichment_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о неосновательном обогащении и не "
            "заменяет судебную оценку.",
            "Наличие правового основания приобретения имущества, его действительная стоимость и "
            "добросовестность приобретателя оцениваются экспертом и судом "
            "(статьи 1102, 1105 и 1109 ГК РФ).",
        ],
    )
