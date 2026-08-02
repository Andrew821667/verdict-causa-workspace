from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


DESIGN_WORK_EVIDENCE_SCHEMA_VERSION = "contracts.design-work-evidence.v0"
DESIGN_WORK_MAPPING_VERSION = "contracts-reviewed-design-work-to-facts-v0"
DESIGN_WORK_MODEL_VERSION = "contracts-design-work-articles-758-762-v0"


class DesignWorkEvidencePredicate(str, Enum):
    # Понятие подряда на проектные и изыскательские работы и исходные данные (статьи 758 и 759).
    DESIGN_OR_SURVEY_WORK_PERFORMED_FOR_FEE = "design_or_survey_work_performed_for_fee"
    ASSIGNMENT_OR_INITIAL_DATA_NOT_PROVIDED = "assignment_or_initial_data_not_provided"
    ASSIGNMENT_REQUIREMENTS_DEVIATED_WITHOUT_CONSENT = (
        "assignment_requirements_deviated_without_consent"
    )
    # Обязанности подрядчика по согласованию и сохранению документации (статья 760).
    DOCUMENTATION_NOT_AGREED_WITH_AUTHORITIES = "documentation_not_agreed_with_authorities"
    DOCUMENTATION_DISCLOSED_TO_THIRD_PARTY_WITHOUT_CONSENT = (
        "documentation_disclosed_to_third_party_without_consent"
    )
    THIRD_PARTY_RIGHT_OBSTRUCTS_WORK = "third_party_right_obstructs_work"
    # Ответственность подрядчика за недостатки документации и работ (статья 761).
    DOCUMENTATION_OR_SURVEY_DEFECTIVE = "documentation_or_survey_defective"
    DEFECT_REVEALED_DURING_CONSTRUCTION_OR_USE = "defect_revealed_during_construction_or_use"
    # Обязанности заказчика (статья 762).
    CUSTOMER_PAYMENT_OR_ASSISTANCE_DUTY_UNMET = "customer_payment_or_assistance_duty_unmet"
    EXTRA_COSTS_FROM_CHANGED_INITIAL_DATA_NOT_COMPENSATED = (
        "extra_costs_from_changed_initial_data_not_compensated"
    )


REQUIRED_DESIGN_WORK_PREDICATES = frozenset(DesignWorkEvidencePredicate)


class DesignWorkEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: DesignWorkEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedDesignWorkEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = DESIGN_WORK_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[DesignWorkEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedDesignWorkEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Design-work evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Design-work evidence contains duplicate legal source refs.")
        return self


class DesignWorkFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    design_or_survey_work_performed_for_fee: bool
    assignment_or_initial_data_not_provided: bool
    assignment_requirements_deviated_without_consent: bool
    documentation_not_agreed_with_authorities: bool
    documentation_disclosed_to_third_party_without_consent: bool
    third_party_right_obstructs_work: bool
    documentation_or_survey_defective: bool
    defect_revealed_during_construction_or_use: bool
    customer_payment_or_assistance_duty_unmet: bool
    extra_costs_from_changed_initial_data_not_compensated: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "DesignWorkFactSet":
        if self.defect_revealed_during_construction_or_use and not (
            self.documentation_or_survey_defective
        ):
            raise ValueError(
                "Выявление недостатка в ходе строительства или эксплуатации относится только к "
                "случаю, когда недостаток технической документации или изыскательских работ "
                "установлен."
            )
        if self.assignment_requirements_deviated_without_consent and not (
            self.design_or_survey_work_performed_for_fee
        ):
            raise ValueError(
                "Отступление от требований задания относится только к договору подряда на "
                "выполнение проектных и изыскательских работ."
            )
        return self


class DesignWorkFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class DesignWorkEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: DesignWorkFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[DesignWorkFactProvenance] = Field(default_factory=list)


class DesignWorkConstraintSet(BaseModel):
    id: str
    model_version: str = DESIGN_WORK_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class DesignWorkEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    design_work_qualified: bool
    initial_data_duty_breached: bool
    assignment_deviation_unauthorized: bool
    approval_duty_breached: bool
    documentation_confidentiality_breached: bool
    third_party_obstruction_risk: bool
    designer_liable_for_defects: bool
    later_discovered_defect_claim: bool
    customer_payment_or_assistance_breached: bool
    extra_costs_compensation_due: bool
    requires_human_design_work_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_design_work_evidence(
    evidence: ReviewedDesignWorkEvidence,
) -> DesignWorkEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Design-work evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Design-work evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_DESIGN_WORK_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed design-work evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_DESIGN_WORK_PREDICATES
    }
    return DesignWorkEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=DESIGN_WORK_MAPPING_VERSION,
        facts=DesignWorkFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            DesignWorkFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_DESIGN_WORK_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_design_work_constraint_set(
    mapping: DesignWorkEvidenceMappingResult,
) -> DesignWorkConstraintSet:
    return DesignWorkConstraintSet(
        id=f"design-work-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "design_work_qualified == design_or_survey_work_performed_for_fee",
            "initial_data_duty_breached == design_work_qualified AND assignment_or_initial_data_not_provided",
            "assignment_deviation_unauthorized == design_work_qualified AND assignment_requirements_deviated_without_consent",
            "approval_duty_breached == design_work_qualified AND documentation_not_agreed_with_authorities",
            "documentation_confidentiality_breached == design_work_qualified AND documentation_disclosed_to_third_party_without_consent",
            "third_party_obstruction_risk == design_work_qualified AND third_party_right_obstructs_work",
            "designer_liable_for_defects == design_work_qualified AND documentation_or_survey_defective",
            "later_discovered_defect_claim == design_work_qualified AND documentation_or_survey_defective AND defect_revealed_during_construction_or_use",
            "customer_payment_or_assistance_breached == design_work_qualified AND customer_payment_or_assistance_duty_unmet",
            "extra_costs_compensation_due == design_work_qualified AND extra_costs_from_changed_initial_data_not_compensated",
            "requires_human_design_work_assessment == initial_data_duty_breached OR assignment_deviation_unauthorized OR approval_duty_breached OR documentation_confidentiality_breached OR third_party_obstruction_risk OR designer_liable_for_defects OR customer_payment_or_assistance_breached OR extra_costs_compensation_due",
        ],
    )


def evaluate_design_work_constraints(
    constraint_set: DesignWorkConstraintSet,
    facts: DesignWorkFactSet,
) -> DesignWorkEvaluation:
    variables = {field_name: Bool(field_name) for field_name in DesignWorkFactSet.model_fields}
    design_work_qualified = Bool("design_work_qualified")
    initial_data_duty_breached = Bool("initial_data_duty_breached")
    assignment_deviation_unauthorized = Bool("assignment_deviation_unauthorized")
    approval_duty_breached = Bool("approval_duty_breached")
    documentation_confidentiality_breached = Bool("documentation_confidentiality_breached")
    third_party_obstruction_risk = Bool("third_party_obstruction_risk")
    designer_liable_for_defects = Bool("designer_liable_for_defects")
    later_discovered_defect_claim = Bool("later_discovered_defect_claim")
    customer_payment_or_assistance_breached = Bool("customer_payment_or_assistance_breached")
    extra_costs_compensation_due = Bool("extra_costs_compensation_due")
    requires_human_design_work_assessment = Bool("requires_human_design_work_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(design_work_qualified == variables["design_or_survey_work_performed_for_fee"])
    solver.add(
        initial_data_duty_breached
        == And(design_work_qualified, variables["assignment_or_initial_data_not_provided"])
    )
    solver.add(
        assignment_deviation_unauthorized
        == And(design_work_qualified, variables["assignment_requirements_deviated_without_consent"])
    )
    solver.add(
        approval_duty_breached
        == And(design_work_qualified, variables["documentation_not_agreed_with_authorities"])
    )
    solver.add(
        documentation_confidentiality_breached
        == And(
            design_work_qualified,
            variables["documentation_disclosed_to_third_party_without_consent"],
        )
    )
    solver.add(
        third_party_obstruction_risk
        == And(design_work_qualified, variables["third_party_right_obstructs_work"])
    )
    solver.add(
        designer_liable_for_defects
        == And(design_work_qualified, variables["documentation_or_survey_defective"])
    )
    solver.add(
        later_discovered_defect_claim
        == And(
            design_work_qualified,
            variables["documentation_or_survey_defective"],
            variables["defect_revealed_during_construction_or_use"],
        )
    )
    solver.add(
        customer_payment_or_assistance_breached
        == And(design_work_qualified, variables["customer_payment_or_assistance_duty_unmet"])
    )
    solver.add(
        extra_costs_compensation_due
        == And(
            design_work_qualified,
            variables["extra_costs_from_changed_initial_data_not_compensated"],
        )
    )
    solver.add(
        requires_human_design_work_assessment
        == Or(
            initial_data_duty_breached,
            assignment_deviation_unauthorized,
            approval_duty_breached,
            documentation_confidentiality_breached,
            third_party_obstruction_risk,
            designer_liable_for_defects,
            customer_payment_or_assistance_breached,
            extra_costs_compensation_due,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return DesignWorkEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            design_work_qualified=False,
            initial_data_duty_breached=False,
            assignment_deviation_unauthorized=False,
            approval_duty_breached=False,
            documentation_confidentiality_breached=False,
            third_party_obstruction_risk=False,
            designer_liable_for_defects=False,
            later_discovered_defect_claim=False,
            customer_payment_or_assistance_breached=False,
            extra_costs_compensation_due=False,
            requires_human_design_work_assessment=True,
            reasons_ru=["Набор фактов о проектных и изыскательских работах противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как подряд на выполнение проектных и изыскательских работ: "
            "подрядчик обязуется по заданию заказчика разработать техническую документацию или "
            "выполнить изыскательские работы, а заказчик — принять и оплатить их результат "
            "(статья 758 ГК РФ)."
            if truth(design_work_qualified)
            else (
                "Отношения не квалифицированы как договор подряда на выполнение проектных и "
                "изыскательских работ."
            )
        ),
    ]
    if truth(initial_data_duty_breached):
        reasons_ru.append(
            "Заказчик обязан передать подрядчику задание на проектирование и иные исходные "
            "данные, необходимые для составления технической документации (статья 759 ГК РФ)."
        )
    if truth(assignment_deviation_unauthorized):
        reasons_ru.append(
            "Подрядчик обязан соблюдать требования задания и других исходных данных и вправе "
            "отступить от них только с согласия заказчика (статья 759 ГК РФ)."
        )
    if truth(approval_duty_breached):
        reasons_ru.append(
            "Подрядчик обязан согласовать готовую техническую документацию с заказчиком и "
            "совместно с ним — с компетентными государственными органами и органами местного "
            "самоуправления (статья 760 ГК РФ)."
        )
    if truth(documentation_confidentiality_breached):
        reasons_ru.append(
            "Техническая документация передана третьим лицам без согласия другой стороны, что "
            "нарушает обязанности подрядчика и заказчика (статьи 760 и 762 ГК РФ)."
        )
    if truth(third_party_obstruction_risk):
        reasons_ru.append(
            "Не гарантировано отсутствие у третьих лиц права воспрепятствовать выполнению работ "
            "или ограничить их выполнение на основе подготовленной документации "
            "(статья 760 ГК РФ)."
        )
    if truth(designer_liable_for_defects):
        reasons_ru.append(
            "Подрядчик отвечает за ненадлежащее составление технической документации и выполнение "
            "изыскательских работ: он обязан безвозмездно переделать документацию, произвести "
            "необходимые дополнительные работы и возместить убытки (статья 761 ГК РФ)."
        )
    if truth(later_discovered_defect_claim):
        reasons_ru.append(
            "Недостатки выявлены впоследствии в ходе строительства или эксплуатации созданного на "
            "основе документации объекта, что сохраняет ответственность подрядчика "
            "(статья 761 ГК РФ)."
        )
    if truth(customer_payment_or_assistance_breached):
        reasons_ru.append(
            "Заказчик обязан уплатить подрядчику установленную цену и оказывать содействие в "
            "выполнении работ, включая участие в согласовании документации с компетентными "
            "органами (статья 762 ГК РФ)."
        )
    if truth(extra_costs_compensation_due):
        reasons_ru.append(
            "Заказчик обязан возместить подрядчику дополнительные расходы, вызванные изменением "
            "исходных данных вследствие обстоятельств, за которые подрядчик не отвечает "
            "(статья 762 ГК РФ)."
        )
    return DesignWorkEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        design_work_qualified=truth(design_work_qualified),
        initial_data_duty_breached=truth(initial_data_duty_breached),
        assignment_deviation_unauthorized=truth(assignment_deviation_unauthorized),
        approval_duty_breached=truth(approval_duty_breached),
        documentation_confidentiality_breached=truth(documentation_confidentiality_breached),
        third_party_obstruction_risk=truth(third_party_obstruction_risk),
        designer_liable_for_defects=truth(designer_liable_for_defects),
        later_discovered_defect_claim=truth(later_discovered_defect_claim),
        customer_payment_or_assistance_breached=truth(customer_payment_or_assistance_breached),
        extra_costs_compensation_due=truth(extra_costs_compensation_due),
        requires_human_design_work_assessment=truth(requires_human_design_work_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о проектных и изыскательских работах и не "
            "заменяет судебную оценку.",
            "Полнота исходных данных, характер недостатков документации и объём дополнительных "
            "расходов оцениваются экспертом и судом (статьи 759, 761 и 762 ГК РФ).",
        ],
    )
