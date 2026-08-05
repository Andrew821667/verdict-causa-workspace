from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


MANDATE_EVIDENCE_SCHEMA_VERSION = "contracts.mandate-evidence.v0"
MANDATE_MAPPING_VERSION = "contracts-reviewed-mandate-to-facts-v0"
MANDATE_MODEL_VERSION = "contracts-mandate-articles-971-979-v0"


class MandateEvidencePredicate(str, Enum):
    # Договор поручения и вознаграждение поверенного (статьи 971 и 972 ГК РФ).
    MANDATE_CONTRACT_CONCLUDED = "mandate_contract_concluded"
    MANDATE_REMUNERATION_RULES_BREACHED = "mandate_remuneration_rules_breached"
    # Исполнение поручения и отступление от указаний (статья 973 ГК РФ).
    MANDATE_INSTRUCTIONS_NOT_FOLLOWED = "mandate_instructions_not_followed"
    DEVIATION_NOTICE_NOT_GIVEN = "deviation_notice_not_given"
    # Обязанности поверенного и передоверие (статьи 974 и 976 ГК РФ).
    ATTORNEY_PERSONAL_PERFORMANCE_BREACHED = "attorney_personal_performance_breached"
    ATTORNEY_REPORTING_DUTY_BREACHED = "attorney_reporting_duty_breached"
    # Обязанности доверителя (статья 975 ГК РФ).
    PRINCIPAL_DUTIES_BREACHED = "principal_duties_breached"
    # Прекращение договора поручения и его последствия (статьи 977–979 ГК РФ).
    MANDATE_TERMINATION_RULES_BREACHED = "mandate_termination_rules_breached"
    TERMINATION_CONSEQUENCES_NOT_APPLIED = "termination_consequences_not_applied"
    SUCCESSOR_DUTIES_BREACHED = "successor_duties_breached"


REQUIRED_MANDATE_PREDICATES = frozenset(MandateEvidencePredicate)


class MandateEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: MandateEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedMandateEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = MANDATE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[MandateEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedMandateEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Mandate evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Mandate evidence contains duplicate legal source refs.")
        return self


class MandateFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mandate_contract_concluded: bool
    mandate_remuneration_rules_breached: bool
    mandate_instructions_not_followed: bool
    deviation_notice_not_given: bool
    attorney_personal_performance_breached: bool
    attorney_reporting_duty_breached: bool
    principal_duties_breached: bool
    mandate_termination_rules_breached: bool
    termination_consequences_not_applied: bool
    successor_duties_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "MandateFactSet":
        if self.deviation_notice_not_given and not self.mandate_instructions_not_followed:
            raise ValueError(
                "Неуведомление об отступлении от указаний относится только к случаю, когда "
                "отступление поверенного от указаний доверителя установлено."
            )
        if self.mandate_remuneration_rules_breached and not self.mandate_contract_concluded:
            raise ValueError(
                "Нарушение правил о вознаграждении поверенного относится только к договору "
                "поручения."
            )
        return self


class MandateFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class MandateEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: MandateFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[MandateFactProvenance] = Field(default_factory=list)


class MandateConstraintSet(BaseModel):
    id: str
    model_version: str = MANDATE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class MandateEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    mandate_qualified: bool
    remuneration_duty_breached: bool
    instructions_duty_breached: bool
    deviation_notice_duty_breached: bool
    personal_performance_duty_breached: bool
    reporting_duty_breached: bool
    principal_duty_breached: bool
    termination_duty_breached: bool
    termination_consequences_breached: bool
    successor_duty_breached: bool
    requires_human_mandate_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_mandate_evidence(
    evidence: ReviewedMandateEvidence,
) -> MandateEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Mandate evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Mandate evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_MANDATE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed mandate evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_MANDATE_PREDICATES
    }
    return MandateEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=MANDATE_MAPPING_VERSION,
        facts=MandateFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            MandateFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_MANDATE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_mandate_constraint_set(
    mapping: MandateEvidenceMappingResult,
) -> MandateConstraintSet:
    return MandateConstraintSet(
        id=f"mandate-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "mandate_qualified == mandate_contract_concluded",
            "remuneration_duty_breached == mandate_qualified AND mandate_remuneration_rules_breached",
            "instructions_duty_breached == mandate_qualified AND mandate_instructions_not_followed",
            "deviation_notice_duty_breached == mandate_qualified AND mandate_instructions_not_followed AND deviation_notice_not_given",
            "personal_performance_duty_breached == mandate_qualified AND attorney_personal_performance_breached",
            "reporting_duty_breached == mandate_qualified AND attorney_reporting_duty_breached",
            "principal_duty_breached == mandate_qualified AND principal_duties_breached",
            "termination_duty_breached == mandate_qualified AND mandate_termination_rules_breached",
            "termination_consequences_breached == mandate_qualified AND termination_consequences_not_applied",
            "successor_duty_breached == mandate_qualified AND successor_duties_breached",
            "requires_human_mandate_assessment == remuneration_duty_breached OR instructions_duty_breached OR personal_performance_duty_breached OR reporting_duty_breached OR principal_duty_breached OR termination_duty_breached OR termination_consequences_breached OR successor_duty_breached",
        ],
    )


def evaluate_mandate_constraints(
    constraint_set: MandateConstraintSet,
    facts: MandateFactSet,
) -> MandateEvaluation:
    variables = {field_name: Bool(field_name) for field_name in MandateFactSet.model_fields}
    mandate_qualified = Bool("mandate_qualified")
    remuneration_duty_breached = Bool("remuneration_duty_breached")
    instructions_duty_breached = Bool("instructions_duty_breached")
    deviation_notice_duty_breached = Bool("deviation_notice_duty_breached")
    personal_performance_duty_breached = Bool("personal_performance_duty_breached")
    reporting_duty_breached = Bool("reporting_duty_breached")
    principal_duty_breached = Bool("principal_duty_breached")
    termination_duty_breached = Bool("termination_duty_breached")
    termination_consequences_breached = Bool("termination_consequences_breached")
    successor_duty_breached = Bool("successor_duty_breached")
    requires_human_mandate_assessment = Bool("requires_human_mandate_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(mandate_qualified == variables["mandate_contract_concluded"])
    solver.add(
        remuneration_duty_breached
        == And(mandate_qualified, variables["mandate_remuneration_rules_breached"])
    )
    solver.add(
        instructions_duty_breached
        == And(mandate_qualified, variables["mandate_instructions_not_followed"])
    )
    solver.add(
        deviation_notice_duty_breached
        == And(
            mandate_qualified,
            variables["mandate_instructions_not_followed"],
            variables["deviation_notice_not_given"],
        )
    )
    solver.add(
        personal_performance_duty_breached
        == And(mandate_qualified, variables["attorney_personal_performance_breached"])
    )
    solver.add(
        reporting_duty_breached
        == And(mandate_qualified, variables["attorney_reporting_duty_breached"])
    )
    solver.add(
        principal_duty_breached == And(mandate_qualified, variables["principal_duties_breached"])
    )
    solver.add(
        termination_duty_breached
        == And(mandate_qualified, variables["mandate_termination_rules_breached"])
    )
    solver.add(
        termination_consequences_breached
        == And(mandate_qualified, variables["termination_consequences_not_applied"])
    )
    solver.add(
        successor_duty_breached == And(mandate_qualified, variables["successor_duties_breached"])
    )
    solver.add(
        requires_human_mandate_assessment
        == Or(
            remuneration_duty_breached,
            instructions_duty_breached,
            personal_performance_duty_breached,
            reporting_duty_breached,
            principal_duty_breached,
            termination_duty_breached,
            termination_consequences_breached,
            successor_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return MandateEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            mandate_qualified=False,
            remuneration_duty_breached=False,
            instructions_duty_breached=False,
            deviation_notice_duty_breached=False,
            personal_performance_duty_breached=False,
            reporting_duty_breached=False,
            principal_duty_breached=False,
            termination_duty_breached=False,
            termination_consequences_breached=False,
            successor_duty_breached=False,
            requires_human_mandate_assessment=True,
            reasons_ru=["Набор фактов о поручении противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как договор поручения: поверенный обязуется совершить от "
            "имени и за счёт доверителя определённые юридические действия, права и обязанности "
            "по которым возникают непосредственно у доверителя (статья 971 ГК РФ)."
            if truth(mandate_qualified)
            else "Отношения не квалифицированы как договор поручения."
        ),
    ]
    if truth(remuneration_duty_breached):
        reasons_ru.append(
            "Доверитель обязан уплатить поверенному вознаграждение, если это предусмотрено "
            "законом, иными правовыми актами или договором; при осуществлении обеими сторонами "
            "предпринимательской деятельности договор предполагается возмездным "
            "(статья 972 ГК РФ)."
        )
    if truth(instructions_duty_breached):
        reasons_ru.append(
            "Поверенный обязан исполнять данное ему поручение в соответствии с указаниями "
            "доверителя, которые должны быть правомерными, осуществимыми и конкретными "
            "(статья 973 ГК РФ)."
        )
    if truth(deviation_notice_duty_breached):
        reasons_ru.append(
            "Поверенный вправе отступить от указаний доверителя, если это необходимо в интересах "
            "доверителя и он не мог предварительно запросить доверителя либо не получил "
            "своевременного ответа; о допущенных отступлениях поверенный обязан уведомить "
            "доверителя при первой возможности (статья 973 ГК РФ)."
        )
    if truth(personal_performance_duty_breached):
        reasons_ru.append(
            "Поверенный обязан исполнять поручение лично, за исключением случаев передоверия, "
            "предусмотренных законом; отвечает за выбор заместителя, если он поименован в "
            "договоре (статьи 974 и 976 ГК РФ)."
        )
    if truth(reporting_duty_breached):
        reasons_ru.append(
            "Поверенный обязан сообщать доверителю по его требованию все сведения о ходе "
            "исполнения поручения, передавать без промедления всё полученное по сделкам и "
            "представить отчёт с приложением оправдательных документов (статья 974 ГК РФ)."
        )
    if truth(principal_duty_breached):
        reasons_ru.append(
            "Доверитель обязан выдать поверенному доверенность, возмещать понесённые издержки, "
            "обеспечивать средствами, необходимыми для исполнения поручения, и без промедления "
            "принять всё исполненное поверенным (статья 975 ГК РФ)."
        )
    if truth(termination_duty_breached):
        reasons_ru.append(
            "Договор поручения прекращается вследствие отмены поручения доверителем, отказа "
            "поверенного, смерти или признания недееспособным одной из сторон; соглашение об "
            "отказе от этих прав ничтожно (статья 977 ГК РФ)."
        )
    if truth(termination_consequences_breached):
        reasons_ru.append(
            "При прекращении договора поручения до полного исполнения доверитель обязан "
            "возместить издержки и уплатить вознаграждение соразмерно выполненной работе, а "
            "отмена поручения по общему правилу не является основанием для возмещения убытков "
            "(статья 978 ГК РФ)."
        )
    if truth(successor_duty_breached):
        reasons_ru.append(
            "В случае смерти поверенного его наследники, а при ликвидации юридического лица — "
            "ликвидатор обязаны известить доверителя и принять меры для охраны его имущества "
            "(статья 979 ГК РФ)."
        )
    return MandateEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        mandate_qualified=truth(mandate_qualified),
        remuneration_duty_breached=truth(remuneration_duty_breached),
        instructions_duty_breached=truth(instructions_duty_breached),
        deviation_notice_duty_breached=truth(deviation_notice_duty_breached),
        personal_performance_duty_breached=truth(personal_performance_duty_breached),
        reporting_duty_breached=truth(reporting_duty_breached),
        principal_duty_breached=truth(principal_duty_breached),
        termination_duty_breached=truth(termination_duty_breached),
        termination_consequences_breached=truth(termination_consequences_breached),
        successor_duty_breached=truth(successor_duty_breached),
        requires_human_mandate_assessment=truth(requires_human_mandate_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о поручении и не заменяет судебную оценку.",
            "Правомерность и осуществимость указаний доверителя, необходимость отступления от них "
            "и соразмерность вознаграждения оцениваются экспертом и судом "
            "(статьи 973 и 978 ГК РФ).",
        ],
    )
