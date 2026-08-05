from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


AGENCY_EVIDENCE_SCHEMA_VERSION = "contracts.agency-evidence.v0"
AGENCY_MAPPING_VERSION = "contracts-reviewed-agency-to-facts-v0"
AGENCY_MODEL_VERSION = "contracts-agency-articles-1005-1011-v0"


class AgencyEvidencePredicate(str, Enum):
    # Агентский договор и правовое положение агента (статья 1005 ГК РФ).
    AGENCY_CONTRACT_CONCLUDED = "agency_contract_concluded"
    AGENT_ACTING_CAPACITY_MISIDENTIFIED = "agent_acting_capacity_misidentified"
    # Агентское вознаграждение (статья 1006 ГК РФ).
    AGENCY_REMUNERATION_RULES_BREACHED = "agency_remuneration_rules_breached"
    # Ограничения прав принципала и агента (статья 1007 ГК РФ).
    AGENCY_EXCLUSIVITY_RESTRICTIONS_BREACHED = "agency_exclusivity_restrictions_breached"
    RESTRICTIONS_AGAINST_CONSUMERS_IMPOSED = "restrictions_against_consumers_imposed"
    # Отчёты агента и возражения принципала (статья 1008 ГК РФ).
    AGENT_REPORT_NOT_SUBMITTED = "agent_report_not_submitted"
    REPORT_OBJECTIONS_PERIOD_DISREGARDED = "report_objections_period_disregarded"
    # Субагентский договор (статья 1009 ГК РФ).
    SUBAGENCY_RULES_BREACHED = "subagency_rules_breached"
    # Прекращение договора и применимые правила (статьи 1010 и 1011 ГК РФ).
    AGENCY_TERMINATION_RULES_BREACHED = "agency_termination_rules_breached"
    APPLICABLE_RULES_SELECTION_BREACHED = "applicable_rules_selection_breached"


REQUIRED_AGENCY_PREDICATES = frozenset(AgencyEvidencePredicate)


class AgencyEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: AgencyEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedAgencyEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = AGENCY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[AgencyEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedAgencyEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Agency evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Agency evidence contains duplicate legal source refs.")
        return self


class AgencyFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    agency_contract_concluded: bool
    agent_acting_capacity_misidentified: bool
    agency_remuneration_rules_breached: bool
    agency_exclusivity_restrictions_breached: bool
    restrictions_against_consumers_imposed: bool
    agent_report_not_submitted: bool
    report_objections_period_disregarded: bool
    subagency_rules_breached: bool
    agency_termination_rules_breached: bool
    applicable_rules_selection_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "AgencyFactSet":
        if (
            self.restrictions_against_consumers_imposed
            and not self.agency_exclusivity_restrictions_breached
        ):
            raise ValueError(
                "Ограничения в отношении определённой категории покупателей относятся только к "
                "случаю, когда нарушение ограничений прав принципала и агента установлено."
            )
        if self.agency_remuneration_rules_breached and not self.agency_contract_concluded:
            raise ValueError(
                "Нарушение правил об агентском вознаграждении относится только к агентскому "
                "договору."
            )
        return self


class AgencyFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class AgencyEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: AgencyFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[AgencyFactProvenance] = Field(default_factory=list)


class AgencyConstraintSet(BaseModel):
    id: str
    model_version: str = AGENCY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class AgencyEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    agency_qualified: bool
    acting_capacity_duty_breached: bool
    remuneration_duty_breached: bool
    exclusivity_restrictions_duty_breached: bool
    consumer_restrictions_void: bool
    report_duty_breached: bool
    report_objections_duty_breached: bool
    subagency_duty_breached: bool
    termination_duty_breached: bool
    applicable_rules_duty_breached: bool
    requires_human_agency_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_agency_evidence(
    evidence: ReviewedAgencyEvidence,
) -> AgencyEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Agency evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Agency evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_AGENCY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed agency evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_AGENCY_PREDICATES
    }
    return AgencyEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=AGENCY_MAPPING_VERSION,
        facts=AgencyFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            AgencyFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_AGENCY_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_agency_constraint_set(
    mapping: AgencyEvidenceMappingResult,
) -> AgencyConstraintSet:
    return AgencyConstraintSet(
        id=f"agency-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "agency_qualified == agency_contract_concluded",
            "acting_capacity_duty_breached == agency_qualified AND agent_acting_capacity_misidentified",
            "remuneration_duty_breached == agency_qualified AND agency_remuneration_rules_breached",
            "exclusivity_restrictions_duty_breached == agency_qualified AND agency_exclusivity_restrictions_breached",
            "consumer_restrictions_void == agency_qualified AND agency_exclusivity_restrictions_breached AND restrictions_against_consumers_imposed",
            "report_duty_breached == agency_qualified AND agent_report_not_submitted",
            "report_objections_duty_breached == agency_qualified AND report_objections_period_disregarded",
            "subagency_duty_breached == agency_qualified AND subagency_rules_breached",
            "termination_duty_breached == agency_qualified AND agency_termination_rules_breached",
            "applicable_rules_duty_breached == agency_qualified AND applicable_rules_selection_breached",
            "requires_human_agency_assessment == acting_capacity_duty_breached OR remuneration_duty_breached OR exclusivity_restrictions_duty_breached OR report_duty_breached OR report_objections_duty_breached OR subagency_duty_breached OR termination_duty_breached OR applicable_rules_duty_breached",
        ],
    )


def evaluate_agency_constraints(
    constraint_set: AgencyConstraintSet,
    facts: AgencyFactSet,
) -> AgencyEvaluation:
    variables = {field_name: Bool(field_name) for field_name in AgencyFactSet.model_fields}
    agency_qualified = Bool("agency_qualified")
    acting_capacity_duty_breached = Bool("acting_capacity_duty_breached")
    remuneration_duty_breached = Bool("remuneration_duty_breached")
    exclusivity_restrictions_duty_breached = Bool("exclusivity_restrictions_duty_breached")
    consumer_restrictions_void = Bool("consumer_restrictions_void")
    report_duty_breached = Bool("report_duty_breached")
    report_objections_duty_breached = Bool("report_objections_duty_breached")
    subagency_duty_breached = Bool("subagency_duty_breached")
    termination_duty_breached = Bool("termination_duty_breached")
    applicable_rules_duty_breached = Bool("applicable_rules_duty_breached")
    requires_human_agency_assessment = Bool("requires_human_agency_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(agency_qualified == variables["agency_contract_concluded"])
    solver.add(
        acting_capacity_duty_breached
        == And(agency_qualified, variables["agent_acting_capacity_misidentified"])
    )
    solver.add(
        remuneration_duty_breached
        == And(agency_qualified, variables["agency_remuneration_rules_breached"])
    )
    solver.add(
        exclusivity_restrictions_duty_breached
        == And(agency_qualified, variables["agency_exclusivity_restrictions_breached"])
    )
    solver.add(
        consumer_restrictions_void
        == And(
            agency_qualified,
            variables["agency_exclusivity_restrictions_breached"],
            variables["restrictions_against_consumers_imposed"],
        )
    )
    solver.add(
        report_duty_breached == And(agency_qualified, variables["agent_report_not_submitted"])
    )
    solver.add(
        report_objections_duty_breached
        == And(agency_qualified, variables["report_objections_period_disregarded"])
    )
    solver.add(
        subagency_duty_breached == And(agency_qualified, variables["subagency_rules_breached"])
    )
    solver.add(
        termination_duty_breached
        == And(agency_qualified, variables["agency_termination_rules_breached"])
    )
    solver.add(
        applicable_rules_duty_breached
        == And(agency_qualified, variables["applicable_rules_selection_breached"])
    )
    solver.add(
        requires_human_agency_assessment
        == Or(
            acting_capacity_duty_breached,
            remuneration_duty_breached,
            exclusivity_restrictions_duty_breached,
            report_duty_breached,
            report_objections_duty_breached,
            subagency_duty_breached,
            termination_duty_breached,
            applicable_rules_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return AgencyEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            agency_qualified=False,
            acting_capacity_duty_breached=False,
            remuneration_duty_breached=False,
            exclusivity_restrictions_duty_breached=False,
            consumer_restrictions_void=False,
            report_duty_breached=False,
            report_objections_duty_breached=False,
            subagency_duty_breached=False,
            termination_duty_breached=False,
            applicable_rules_duty_breached=False,
            requires_human_agency_assessment=True,
            reasons_ru=["Набор фактов об агентировании противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как агентский договор: агент обязуется за вознаграждение "
            "совершать по поручению принципала юридические и иные действия от своего имени, но за "
            "счёт принципала либо от имени и за счёт принципала (статья 1005 ГК РФ)."
            if truth(agency_qualified)
            else "Отношения не квалифицированы как агентский договор."
        ),
    ]
    if truth(acting_capacity_duty_breached):
        reasons_ru.append(
            "По сделке, совершённой агентом от своего имени и за счёт принципала, приобретает "
            "права и становится обязанным агент; по сделке, совершённой от имени и за счёт "
            "принципала, права и обязанности возникают непосредственно у принципала "
            "(статья 1005 ГК РФ)."
        )
    if truth(remuneration_duty_breached):
        reasons_ru.append(
            "Принципал обязан уплатить агенту вознаграждение в размере и порядке, установленных "
            "в агентском договоре; при отсутствии в договоре условий о размере вознаграждение "
            "определяется по правилам о цене (статья 1006 ГК РФ)."
        )
    if truth(exclusivity_restrictions_duty_breached):
        reasons_ru.append(
            "Агентским договором могут быть предусмотрены обязательства принципала не заключать "
            "аналогичных договоров с другими агентами на определённой территории и обязательства "
            "агента не заключать аналогичных договоров с другими принципалами "
            "(статья 1007 ГК РФ)."
        )
    if truth(consumer_restrictions_void):
        reasons_ru.append(
            "Условия агентского договора, в силу которых агент вправе продавать товары, выполнять "
            "работы или оказывать услуги исключительно определённой категории покупателей либо "
            "покупателям, имеющим место нахождения или жительства на определённой территории, "
            "ничтожны (статья 1007 ГК РФ)."
        )
    if truth(report_duty_breached):
        reasons_ru.append(
            "В ходе исполнения агентского договора агент обязан представлять принципалу отчёты в "
            "порядке и в сроки, предусмотренные договором, с приложением доказательств "
            "произведённых за счёт принципала расходов (статья 1008 ГК РФ)."
        )
    if truth(report_objections_duty_breached):
        reasons_ru.append(
            "Принципал, имеющий возражения по отчёту агента, должен сообщить о них агенту в "
            "течение тридцати дней со дня получения отчёта, если соглашением не установлен иной "
            "срок; в противном случае отчёт считается принятым (статья 1008 ГК РФ)."
        )
    if truth(subagency_duty_breached):
        reasons_ru.append(
            "Если иное не предусмотрено агентским договором, агент вправе заключить субагентский "
            "договор, оставаясь ответственным за действия субагента перед принципалом "
            "(статья 1009 ГК РФ)."
        )
    if truth(termination_duty_breached):
        reasons_ru.append(
            "Агентский договор прекращается вследствие отказа стороны от исполнения договора, "
            "заключённого без определения срока окончания, смерти агента, признания его "
            "недееспособным или банкротства (статья 1010 ГК РФ)."
        )
    if truth(applicable_rules_duty_breached):
        reasons_ru.append(
            "К отношениям, вытекающим из агентского договора, применяются правила о поручении или "
            "о комиссии в зависимости от того, действует агент от имени принципала или от своего "
            "имени, если эти правила не противоречат существу агентского договора "
            "(статья 1011 ГК РФ)."
        )
    return AgencyEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        agency_qualified=truth(agency_qualified),
        acting_capacity_duty_breached=truth(acting_capacity_duty_breached),
        remuneration_duty_breached=truth(remuneration_duty_breached),
        exclusivity_restrictions_duty_breached=truth(exclusivity_restrictions_duty_breached),
        consumer_restrictions_void=truth(consumer_restrictions_void),
        report_duty_breached=truth(report_duty_breached),
        report_objections_duty_breached=truth(report_objections_duty_breached),
        subagency_duty_breached=truth(subagency_duty_breached),
        termination_duty_breached=truth(termination_duty_breached),
        applicable_rules_duty_breached=truth(applicable_rules_duty_breached),
        requires_human_agency_assessment=truth(requires_human_agency_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила об агентировании и не заменяет судебную "
            "оценку.",
            "Существо агентского договора, допустимость договорных ограничений и обоснованность "
            "возражений по отчёту оцениваются экспертом и судом "
            "(статьи 1007, 1008 и 1011 ГК РФ).",
        ],
    )
