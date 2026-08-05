from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


TORT_GENERAL_EVIDENCE_SCHEMA_VERSION = "contracts.tort-general-evidence.v0"
TORT_GENERAL_MAPPING_VERSION = "contracts-reviewed-tort-general-to-facts-v0"
TORT_GENERAL_MODEL_VERSION = "contracts-tort-general-articles-1064-1083-v0"


class TortGeneralEvidencePredicate(str, Enum):
    # Общие основания ответственности за причинение вреда (статья 1064 ГК РФ).
    HARM_CAUSED_ESTABLISHED = "harm_caused_established"
    FULL_COMPENSATION_RULE_BREACHED = "full_compensation_rule_breached"
    FAULT_PRESUMPTION_BREACHED = "fault_presumption_breached"
    # Причинение вреда в состоянии необходимой обороны и крайней необходимости
    # (статьи 1066 и 1067 ГК РФ).
    LAWFUL_OR_DEFENSIVE_HARM_RULES_BREACHED = "lawful_or_defensive_harm_rules_breached"
    # Ответственность за вред, причинённый другими лицами
    # (статьи 1068–1070 и 1073–1078 ГК РФ).
    LIABILITY_FOR_OTHERS_BREACHED = "liability_for_others_breached"
    # Ответственность за вред, причинённый источником повышенной опасности
    # (статья 1079 ГК РФ).
    HIGH_RISK_SOURCE_LIABILITY_BREACHED = "high_risk_source_liability_breached"
    # Совместное причинение вреда и право регресса (статьи 1080 и 1081 ГК РФ).
    JOINT_LIABILITY_AND_RECOURSE_BREACHED = "joint_liability_and_recourse_breached"
    # Способ и размер возмещения вреда (статья 1082 ГК РФ).
    COMPENSATION_METHOD_OR_AMOUNT_BREACHED = "compensation_method_or_amount_breached"
    # Учёт вины потерпевшего и имущественного положения причинителя
    # (статья 1083 ГК РФ).
    VICTIM_FAULT_OR_CAUSER_MEANS_DISREGARDED = "victim_fault_or_causer_means_disregarded"
    GROSS_NEGLIGENCE_REDUCTION_NOT_APPLIED = "gross_negligence_reduction_not_applied"


REQUIRED_TORT_GENERAL_PREDICATES = frozenset(TortGeneralEvidencePredicate)


class TortGeneralEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: TortGeneralEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedTortGeneralEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = TORT_GENERAL_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[TortGeneralEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedTortGeneralEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Tort-general evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Tort-general evidence contains duplicate legal source refs.")
        return self


class TortGeneralFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    harm_caused_established: bool
    full_compensation_rule_breached: bool
    fault_presumption_breached: bool
    lawful_or_defensive_harm_rules_breached: bool
    liability_for_others_breached: bool
    high_risk_source_liability_breached: bool
    joint_liability_and_recourse_breached: bool
    compensation_method_or_amount_breached: bool
    victim_fault_or_causer_means_disregarded: bool
    gross_negligence_reduction_not_applied: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "TortGeneralFactSet":
        if (
            self.gross_negligence_reduction_not_applied
            and not self.victim_fault_or_causer_means_disregarded
        ):
            raise ValueError(
                "Неприменение уменьшения размера возмещения при грубой неосторожности "
                "потерпевшего относится только к случаю, когда нарушение учёта вины "
                "потерпевшего или имущественного положения причинителя установлено."
            )
        if self.full_compensation_rule_breached and not self.harm_caused_established:
            raise ValueError(
                "Нарушение правила о возмещении вреда в полном объёме относится только к "
                "случаю, когда причинение вреда установлено."
            )
        return self


class TortGeneralFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class TortGeneralEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: TortGeneralFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[TortGeneralFactProvenance] = Field(default_factory=list)


class TortGeneralConstraintSet(BaseModel):
    id: str
    model_version: str = TORT_GENERAL_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class TortGeneralEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    tort_qualified: bool
    full_compensation_duty_breached: bool
    fault_presumption_duty_breached: bool
    lawful_harm_duty_breached: bool
    liability_for_others_duty_breached: bool
    high_risk_source_duty_breached: bool
    joint_liability_duty_breached: bool
    compensation_method_duty_breached: bool
    victim_fault_duty_breached: bool
    gross_negligence_reduction_breached: bool
    requires_human_tort_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_tort_general_evidence(
    evidence: ReviewedTortGeneralEvidence,
) -> TortGeneralEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Tort-general evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Tort-general evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_TORT_GENERAL_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed tort-general evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_TORT_GENERAL_PREDICATES
    }
    return TortGeneralEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=TORT_GENERAL_MAPPING_VERSION,
        facts=TortGeneralFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            TortGeneralFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_TORT_GENERAL_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_tort_general_constraint_set(
    mapping: TortGeneralEvidenceMappingResult,
) -> TortGeneralConstraintSet:
    return TortGeneralConstraintSet(
        id=f"tort-general-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "tort_qualified == harm_caused_established",
            "full_compensation_duty_breached == tort_qualified AND full_compensation_rule_breached",
            "fault_presumption_duty_breached == tort_qualified AND fault_presumption_breached",
            "lawful_harm_duty_breached == tort_qualified AND lawful_or_defensive_harm_rules_breached",
            "liability_for_others_duty_breached == tort_qualified AND liability_for_others_breached",
            "high_risk_source_duty_breached == tort_qualified AND high_risk_source_liability_breached",
            "joint_liability_duty_breached == tort_qualified AND joint_liability_and_recourse_breached",
            "compensation_method_duty_breached == tort_qualified AND compensation_method_or_amount_breached",
            "victim_fault_duty_breached == tort_qualified AND victim_fault_or_causer_means_disregarded",
            "gross_negligence_reduction_breached == tort_qualified AND victim_fault_or_causer_means_disregarded AND gross_negligence_reduction_not_applied",
            "requires_human_tort_assessment == full_compensation_duty_breached OR fault_presumption_duty_breached OR lawful_harm_duty_breached OR liability_for_others_duty_breached OR high_risk_source_duty_breached OR joint_liability_duty_breached OR compensation_method_duty_breached OR victim_fault_duty_breached",
        ],
    )


def evaluate_tort_general_constraints(
    constraint_set: TortGeneralConstraintSet,
    facts: TortGeneralFactSet,
) -> TortGeneralEvaluation:
    variables = {field_name: Bool(field_name) for field_name in TortGeneralFactSet.model_fields}
    tort_qualified = Bool("tort_qualified")
    full_compensation_duty_breached = Bool("full_compensation_duty_breached")
    fault_presumption_duty_breached = Bool("fault_presumption_duty_breached")
    lawful_harm_duty_breached = Bool("lawful_harm_duty_breached")
    liability_for_others_duty_breached = Bool("liability_for_others_duty_breached")
    high_risk_source_duty_breached = Bool("high_risk_source_duty_breached")
    joint_liability_duty_breached = Bool("joint_liability_duty_breached")
    compensation_method_duty_breached = Bool("compensation_method_duty_breached")
    victim_fault_duty_breached = Bool("victim_fault_duty_breached")
    gross_negligence_reduction_breached = Bool("gross_negligence_reduction_breached")
    requires_human_tort_assessment = Bool("requires_human_tort_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(tort_qualified == variables["harm_caused_established"])
    solver.add(
        full_compensation_duty_breached
        == And(tort_qualified, variables["full_compensation_rule_breached"])
    )
    solver.add(
        fault_presumption_duty_breached
        == And(tort_qualified, variables["fault_presumption_breached"])
    )
    solver.add(
        lawful_harm_duty_breached
        == And(tort_qualified, variables["lawful_or_defensive_harm_rules_breached"])
    )
    solver.add(
        liability_for_others_duty_breached
        == And(tort_qualified, variables["liability_for_others_breached"])
    )
    solver.add(
        high_risk_source_duty_breached
        == And(tort_qualified, variables["high_risk_source_liability_breached"])
    )
    solver.add(
        joint_liability_duty_breached
        == And(tort_qualified, variables["joint_liability_and_recourse_breached"])
    )
    solver.add(
        compensation_method_duty_breached
        == And(tort_qualified, variables["compensation_method_or_amount_breached"])
    )
    solver.add(
        victim_fault_duty_breached
        == And(tort_qualified, variables["victim_fault_or_causer_means_disregarded"])
    )
    solver.add(
        gross_negligence_reduction_breached
        == And(
            tort_qualified,
            variables["victim_fault_or_causer_means_disregarded"],
            variables["gross_negligence_reduction_not_applied"],
        )
    )
    solver.add(
        requires_human_tort_assessment
        == Or(
            full_compensation_duty_breached,
            fault_presumption_duty_breached,
            lawful_harm_duty_breached,
            liability_for_others_duty_breached,
            high_risk_source_duty_breached,
            joint_liability_duty_breached,
            compensation_method_duty_breached,
            victim_fault_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return TortGeneralEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            tort_qualified=False,
            full_compensation_duty_breached=False,
            fault_presumption_duty_breached=False,
            lawful_harm_duty_breached=False,
            liability_for_others_duty_breached=False,
            high_risk_source_duty_breached=False,
            joint_liability_duty_breached=False,
            compensation_method_duty_breached=False,
            victim_fault_duty_breached=False,
            gross_negligence_reduction_breached=False,
            requires_human_tort_assessment=True,
            reasons_ru=["Набор фактов о возмещении причинённого вреда противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Установлено причинение вреда: вред, причинённый личности или имуществу гражданина, "
            "а также имуществу юридического лица, подлежит возмещению в полном объёме лицом, "
            "причинившим вред (статья 1064 ГК РФ)."
            if truth(tort_qualified)
            else "Причинение вреда не установлено."
        ),
    ]
    if truth(full_compensation_duty_breached):
        reasons_ru.append(
            "Вред возмещается в полном объёме; законом обязанность возмещения может быть "
            "возложена на лицо, не являющееся причинителем вреда, а законом или договором может "
            "быть установлена обязанность выплатить компенсацию сверх возмещения вреда "
            "(статья 1064 ГК РФ)."
        )
    if truth(fault_presumption_duty_breached):
        reasons_ru.append(
            "Лицо, причинившее вред, освобождается от возмещения, если докажет, что вред "
            "причинён не по его вине; законом может быть предусмотрено возмещение вреда и при "
            "отсутствии вины причинителя (статья 1064 ГК РФ)."
        )
    if truth(lawful_harm_duty_breached):
        reasons_ru.append(
            "Вред, причинённый в состоянии необходимой обороны, не подлежит возмещению, если её "
            "пределы не были превышены; вред, причинённый в состоянии крайней необходимости, "
            "возмещается причинившим его лицом, однако суд вправе возложить возмещение на "
            "третье лицо, в интересах которого действовал причинитель, либо освободить от "
            "возмещения полностью или частично (статьи 1066 и 1067 ГК РФ)."
        )
    if truth(liability_for_others_duty_breached):
        reasons_ru.append(
            "Юридическое лицо или гражданин возмещает вред, причинённый его работником при "
            "исполнении трудовых обязанностей; вред, причинённый государственными органами, "
            "органами местного самоуправления и их должностными лицами, а также вред, "
            "причинённый несовершеннолетними, недееспособными и лицами, не способными понимать "
            "значение своих действий, возмещается по специальным правилам "
            "(статьи 1068–1070 и 1073–1078 ГК РФ)."
        )
    if truth(high_risk_source_duty_breached):
        reasons_ru.append(
            "Юридические лица и граждане, деятельность которых связана с повышенной опасностью "
            "для окружающих, обязаны возместить вред, причинённый источником повышенной "
            "опасности, если не докажут, что вред возник вследствие непреодолимой силы или "
            "умысла потерпевшего; обязанность возмещения возлагается на владельца источника "
            "повышенной опасности (статья 1079 ГК РФ)."
        )
    if truth(joint_liability_duty_breached):
        reasons_ru.append(
            "Лица, совместно причинившие вред, отвечают перед потерпевшим солидарно; лицо, "
            "возместившее вред, причинённый другим лицом, имеет право обратного требования "
            "(регресса) к этому лицу в размере выплаченного возмещения "
            "(статьи 1080 и 1081 ГК РФ)."
        )
    if truth(compensation_method_duty_breached):
        reasons_ru.append(
            "Удовлетворяя требование о возмещении вреда, суд обязывает возместить вред в натуре "
            "либо возместить причинённые убытки в соответствии с правилами статьи 15 ГК РФ "
            "(статья 1082 ГК РФ)."
        )
    if truth(victim_fault_duty_breached):
        reasons_ru.append(
            "Вред, возникший вследствие умысла потерпевшего, возмещению не подлежит; суд может "
            "уменьшить размер возмещения с учётом имущественного положения "
            "гражданина-причинителя, за исключением случаев умышленного причинения вреда "
            "(статья 1083 ГК РФ)."
        )
    if truth(gross_negligence_reduction_breached):
        reasons_ru.append(
            "Если грубая неосторожность потерпевшего содействовала возникновению или увеличению "
            "вреда, размер возмещения должен быть уменьшен в зависимости от степени вины "
            "потерпевшего и причинителя вреда (статья 1083 ГК РФ)."
        )
    return TortGeneralEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        tort_qualified=truth(tort_qualified),
        full_compensation_duty_breached=truth(full_compensation_duty_breached),
        fault_presumption_duty_breached=truth(fault_presumption_duty_breached),
        lawful_harm_duty_breached=truth(lawful_harm_duty_breached),
        liability_for_others_duty_breached=truth(liability_for_others_duty_breached),
        high_risk_source_duty_breached=truth(high_risk_source_duty_breached),
        joint_liability_duty_breached=truth(joint_liability_duty_breached),
        compensation_method_duty_breached=truth(compensation_method_duty_breached),
        victim_fault_duty_breached=truth(victim_fault_duty_breached),
        gross_negligence_reduction_breached=truth(gross_negligence_reduction_breached),
        requires_human_tort_assessment=truth(requires_human_tort_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные общие правила о возмещении вреда и не заменяет "
            "судебную оценку.",
            "Наличие вины причинителя, причинная связь, степень вины потерпевшего и размер "
            "убытков оцениваются экспертом и судом (статьи 1064, 1079 и 1083 ГК РФ).",
        ],
    )
