from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


PARTNERSHIP_EVIDENCE_SCHEMA_VERSION = "contracts.partnership-evidence.v0"
PARTNERSHIP_MAPPING_VERSION = "contracts-reviewed-partnership-to-facts-v0"
PARTNERSHIP_MODEL_VERSION = "contracts-partnership-articles-1041-1054-v0"


class PartnershipEvidencePredicate(str, Enum):
    # Договор простого товарищества, стороны и цель (статья 1041 ГК РФ).
    PARTNERSHIP_CONTRACT_CONCLUDED = "partnership_contract_concluded"
    PARTNERSHIP_PARTIES_OR_PURPOSE_BREACHED = "partnership_parties_or_purpose_breached"
    # Вклады товарищей и общее имущество (статьи 1042 и 1043 ГК РФ).
    CONTRIBUTIONS_OR_COMMON_PROPERTY_BREACHED = "contributions_or_common_property_breached"
    # Ведение общих дел товарищей (статья 1044 ГК РФ).
    COMMON_AFFAIRS_CONDUCT_BREACHED = "common_affairs_conduct_breached"
    # Право на информацию, общие расходы и убытки (статьи 1045 и 1046 ГК РФ).
    INFORMATION_OR_EXPENSE_SHARING_BREACHED = "information_or_expense_sharing_breached"
    # Ответственность товарищей по общим обязательствам (статья 1047 ГК РФ).
    PARTNERS_LIABILITY_RULES_BREACHED = "partners_liability_rules_breached"
    # Распределение прибыли и ничтожность отстранения от неё (статья 1048 ГК РФ).
    PROFIT_DISTRIBUTION_RULES_BREACHED = "profit_distribution_rules_breached"
    PROFIT_EXCLUSION_VOID_NOT_APPLIED = "profit_exclusion_void_not_applied"
    # Выдел доли, прекращение договора и выход товарища (статьи 1049–1053 ГК РФ).
    TERMINATION_OR_WITHDRAWAL_RULES_BREACHED = "termination_or_withdrawal_rules_breached"
    # Негласное товарищество (статья 1054 ГК РФ).
    UNDISCLOSED_PARTNERSHIP_RULES_BREACHED = "undisclosed_partnership_rules_breached"


REQUIRED_PARTNERSHIP_PREDICATES = frozenset(PartnershipEvidencePredicate)


class PartnershipEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: PartnershipEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedPartnershipEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = PARTNERSHIP_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[PartnershipEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedPartnershipEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Partnership evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Partnership evidence contains duplicate legal source refs.")
        return self


class PartnershipFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    partnership_contract_concluded: bool
    partnership_parties_or_purpose_breached: bool
    contributions_or_common_property_breached: bool
    common_affairs_conduct_breached: bool
    information_or_expense_sharing_breached: bool
    partners_liability_rules_breached: bool
    profit_distribution_rules_breached: bool
    profit_exclusion_void_not_applied: bool
    termination_or_withdrawal_rules_breached: bool
    undisclosed_partnership_rules_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "PartnershipFactSet":
        if self.profit_exclusion_void_not_applied and not self.profit_distribution_rules_breached:
            raise ValueError(
                "Неприменение ничтожности соглашения об устранении товарища от участия в прибыли "
                "относится только к случаю, когда нарушение правил о распределении прибыли "
                "установлено."
            )
        if self.partnership_parties_or_purpose_breached and not self.partnership_contract_concluded:
            raise ValueError(
                "Нарушение состава сторон и цели совместной деятельности относится только к "
                "договору простого товарищества."
            )
        return self


class PartnershipFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class PartnershipEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: PartnershipFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[PartnershipFactProvenance] = Field(default_factory=list)


class PartnershipConstraintSet(BaseModel):
    id: str
    model_version: str = PARTNERSHIP_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class PartnershipEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    partnership_qualified: bool
    parties_and_purpose_duty_breached: bool
    contributions_and_common_property_duty_breached: bool
    common_affairs_duty_breached: bool
    information_and_expenses_duty_breached: bool
    partners_liability_duty_breached: bool
    profit_distribution_duty_breached: bool
    profit_exclusion_void_breached: bool
    termination_and_withdrawal_duty_breached: bool
    undisclosed_partnership_duty_breached: bool
    requires_human_partnership_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_partnership_evidence(
    evidence: ReviewedPartnershipEvidence,
) -> PartnershipEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Partnership evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Partnership evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_PARTNERSHIP_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed partnership evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_PARTNERSHIP_PREDICATES
    }
    return PartnershipEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=PARTNERSHIP_MAPPING_VERSION,
        facts=PartnershipFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            PartnershipFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_PARTNERSHIP_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_partnership_constraint_set(
    mapping: PartnershipEvidenceMappingResult,
) -> PartnershipConstraintSet:
    return PartnershipConstraintSet(
        id=f"partnership-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "partnership_qualified == partnership_contract_concluded",
            "parties_and_purpose_duty_breached == partnership_qualified AND partnership_parties_or_purpose_breached",
            "contributions_and_common_property_duty_breached == partnership_qualified AND contributions_or_common_property_breached",
            "common_affairs_duty_breached == partnership_qualified AND common_affairs_conduct_breached",
            "information_and_expenses_duty_breached == partnership_qualified AND information_or_expense_sharing_breached",
            "partners_liability_duty_breached == partnership_qualified AND partners_liability_rules_breached",
            "profit_distribution_duty_breached == partnership_qualified AND profit_distribution_rules_breached",
            "profit_exclusion_void_breached == partnership_qualified AND profit_distribution_rules_breached AND profit_exclusion_void_not_applied",
            "termination_and_withdrawal_duty_breached == partnership_qualified AND termination_or_withdrawal_rules_breached",
            "undisclosed_partnership_duty_breached == partnership_qualified AND undisclosed_partnership_rules_breached",
            "requires_human_partnership_assessment == parties_and_purpose_duty_breached OR contributions_and_common_property_duty_breached OR common_affairs_duty_breached OR information_and_expenses_duty_breached OR partners_liability_duty_breached OR profit_distribution_duty_breached OR termination_and_withdrawal_duty_breached OR undisclosed_partnership_duty_breached",
        ],
    )


def evaluate_partnership_constraints(
    constraint_set: PartnershipConstraintSet,
    facts: PartnershipFactSet,
) -> PartnershipEvaluation:
    variables = {field_name: Bool(field_name) for field_name in PartnershipFactSet.model_fields}
    partnership_qualified = Bool("partnership_qualified")
    parties_and_purpose_duty_breached = Bool("parties_and_purpose_duty_breached")
    contributions_and_common_property_duty_breached = Bool(
        "contributions_and_common_property_duty_breached"
    )
    common_affairs_duty_breached = Bool("common_affairs_duty_breached")
    information_and_expenses_duty_breached = Bool("information_and_expenses_duty_breached")
    partners_liability_duty_breached = Bool("partners_liability_duty_breached")
    profit_distribution_duty_breached = Bool("profit_distribution_duty_breached")
    profit_exclusion_void_breached = Bool("profit_exclusion_void_breached")
    termination_and_withdrawal_duty_breached = Bool("termination_and_withdrawal_duty_breached")
    undisclosed_partnership_duty_breached = Bool("undisclosed_partnership_duty_breached")
    requires_human_partnership_assessment = Bool("requires_human_partnership_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(partnership_qualified == variables["partnership_contract_concluded"])
    solver.add(
        parties_and_purpose_duty_breached
        == And(partnership_qualified, variables["partnership_parties_or_purpose_breached"])
    )
    solver.add(
        contributions_and_common_property_duty_breached
        == And(partnership_qualified, variables["contributions_or_common_property_breached"])
    )
    solver.add(
        common_affairs_duty_breached
        == And(partnership_qualified, variables["common_affairs_conduct_breached"])
    )
    solver.add(
        information_and_expenses_duty_breached
        == And(partnership_qualified, variables["information_or_expense_sharing_breached"])
    )
    solver.add(
        partners_liability_duty_breached
        == And(partnership_qualified, variables["partners_liability_rules_breached"])
    )
    solver.add(
        profit_distribution_duty_breached
        == And(partnership_qualified, variables["profit_distribution_rules_breached"])
    )
    solver.add(
        profit_exclusion_void_breached
        == And(
            partnership_qualified,
            variables["profit_distribution_rules_breached"],
            variables["profit_exclusion_void_not_applied"],
        )
    )
    solver.add(
        termination_and_withdrawal_duty_breached
        == And(partnership_qualified, variables["termination_or_withdrawal_rules_breached"])
    )
    solver.add(
        undisclosed_partnership_duty_breached
        == And(partnership_qualified, variables["undisclosed_partnership_rules_breached"])
    )
    solver.add(
        requires_human_partnership_assessment
        == Or(
            parties_and_purpose_duty_breached,
            contributions_and_common_property_duty_breached,
            common_affairs_duty_breached,
            information_and_expenses_duty_breached,
            partners_liability_duty_breached,
            profit_distribution_duty_breached,
            termination_and_withdrawal_duty_breached,
            undisclosed_partnership_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return PartnershipEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            partnership_qualified=False,
            parties_and_purpose_duty_breached=False,
            contributions_and_common_property_duty_breached=False,
            common_affairs_duty_breached=False,
            information_and_expenses_duty_breached=False,
            partners_liability_duty_breached=False,
            profit_distribution_duty_breached=False,
            profit_exclusion_void_breached=False,
            termination_and_withdrawal_duty_breached=False,
            undisclosed_partnership_duty_breached=False,
            requires_human_partnership_assessment=True,
            reasons_ru=["Набор фактов о простом товариществе противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как договор простого товарищества (о совместной "
            "деятельности): двое или несколько лиц обязуются соединить свои вклады и совместно "
            "действовать без образования юридического лица для извлечения прибыли или "
            "достижения иной не противоречащей закону цели (статья 1041 ГК РФ)."
            if truth(partnership_qualified)
            else "Отношения не квалифицированы как договор простого товарищества."
        ),
    ]
    if truth(parties_and_purpose_duty_breached):
        reasons_ru.append(
            "Сторонами договора простого товарищества, заключаемого для осуществления "
            "предпринимательской деятельности, могут быть только индивидуальные "
            "предприниматели и коммерческие организации, а цель совместной деятельности не "
            "должна противоречить закону (статья 1041 ГК РФ)."
        )
    if truth(contributions_and_common_property_duty_breached):
        reasons_ru.append(
            "Вкладом товарища признаётся всё, что он вносит в общее дело, включая деньги, иное "
            "имущество, профессиональные и иные знания, навыки, умения, деловую репутацию и "
            "деловые связи; внесённое имущество и полученные доходы по общему правилу "
            "признаются общей долевой собственностью товарищей (статьи 1042 и 1043 ГК РФ)."
        )
    if truth(common_affairs_duty_breached):
        reasons_ru.append(
            "Ведение общих дел товарищей осуществляется по общему правилу каждым товарищем от "
            "имени всех либо специально уполномоченным товарищем; полномочие подтверждается "
            "доверенностью или письменным договором, а ограничения прав товарища на ведение "
            "общих дел не могут противопоставляться третьим лицам, не знавшим о них "
            "(статья 1044 ГК РФ)."
        )
    if truth(information_and_expenses_duty_breached):
        reasons_ru.append(
            "Каждый товарищ независимо от того, уполномочен ли он вести общие дела, вправе "
            "знакомиться со всей документацией по ведению дел, и отказ от этого права или его "
            "ограничение, в том числе по соглашению товарищей, ничтожны; общие расходы и "
            "убытки покрываются в порядке, определённом соглашением, а при его отсутствии — "
            "соразмерно стоимости вклада (статьи 1045 и 1046 ГК РФ)."
        )
    if truth(partners_liability_duty_breached):
        reasons_ru.append(
            "По общим договорным обязательствам, не связанным с предпринимательской "
            "деятельностью, товарищи отвечают всем своим имуществом пропорционально стоимости "
            "вклада в общее дело, а по договору, заключённому для осуществления "
            "предпринимательской деятельности, товарищи отвечают солидарно по всем общим "
            "обязательствам (статья 1047 ГК РФ)."
        )
    if truth(profit_distribution_duty_breached):
        reasons_ru.append(
            "Прибыль, полученная товарищами в результате совместной деятельности, "
            "распределяется пропорционально стоимости вкладов в общее дело, если иное не "
            "предусмотрено договором простого товарищества или иным соглашением товарищей "
            "(статья 1048 ГК РФ)."
        )
    if truth(profit_exclusion_void_breached):
        reasons_ru.append(
            "Соглашение об устранении кого-либо из товарищей от участия в прибыли ничтожно "
            "(статья 1048 ГК РФ)."
        )
    if truth(termination_and_withdrawal_duty_breached):
        reasons_ru.append(
            "Выдел доли товарища по требованию его кредитора, основания прекращения договора "
            "простого товарищества, отказ от бессрочного договора, расторжение договора по "
            "требованию стороны и ответственность товарища, в отношении которого договор "
            "расторгнут, подчиняются правилам статей 1049–1053 ГК РФ."
        )
    if truth(undisclosed_partnership_duty_breached):
        reasons_ru.append(
            "Договором простого товарищества может быть предусмотрено, что его существование не "
            "раскрывается для третьих лиц (негласное товарищество); в отношениях с третьими "
            "лицами каждый из участников отвечает всем своим имуществом по сделкам, которые он "
            "заключил от своего имени в общих интересах товарищей (статья 1054 ГК РФ)."
        )
    return PartnershipEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        partnership_qualified=truth(partnership_qualified),
        parties_and_purpose_duty_breached=truth(parties_and_purpose_duty_breached),
        contributions_and_common_property_duty_breached=truth(
            contributions_and_common_property_duty_breached
        ),
        common_affairs_duty_breached=truth(common_affairs_duty_breached),
        information_and_expenses_duty_breached=truth(information_and_expenses_duty_breached),
        partners_liability_duty_breached=truth(partners_liability_duty_breached),
        profit_distribution_duty_breached=truth(profit_distribution_duty_breached),
        profit_exclusion_void_breached=truth(profit_exclusion_void_breached),
        termination_and_withdrawal_duty_breached=truth(termination_and_withdrawal_duty_breached),
        undisclosed_partnership_duty_breached=truth(undisclosed_partnership_duty_breached),
        requires_human_partnership_assessment=truth(requires_human_partnership_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о простом товариществе и не заменяет "
            "судебную оценку.",
            "Стоимость вкладов товарищей, содержание общей цели и добросовестность ведения "
            "общих дел оцениваются экспертом и судом (статьи 1042, 1044 и 1048 ГК РФ).",
        ],
    )
