from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


PUBLIC_PROMISE_EVIDENCE_SCHEMA_VERSION = "contracts.public-promise-evidence.v0"
PUBLIC_PROMISE_MAPPING_VERSION = "contracts-reviewed-public-promise-to-facts-v0"
PUBLIC_PROMISE_MODEL_VERSION = "contracts-public-promise-articles-1055-1061-v0"


class PublicPromiseEvidencePredicate(str, Enum):
    # Публичное обещание награды и требования к объявлению (статья 1055 ГК РФ).
    PUBLIC_PROMISE_OR_CONTEST_DECLARED = "public_promise_or_contest_declared"
    PROMISE_ANNOUNCEMENT_REQUIREMENTS_BREACHED = "promise_announcement_requirements_breached"
    REWARD_AMOUNT_OR_DISTRIBUTION_BREACHED = "reward_amount_or_distribution_breached"
    # Отмена публичного обещания награды (статья 1056 ГК РФ).
    PROMISE_REVOCATION_RULES_BREACHED = "promise_revocation_rules_breached"
    REVOCATION_EXPENSE_COMPENSATION_NOT_APPLIED = "revocation_expense_compensation_not_applied"
    # Организация публичного конкурса (статья 1057 ГК РФ).
    CONTEST_ANNOUNCEMENT_TERMS_BREACHED = "contest_announcement_terms_breached"
    CONTEST_PUBLIC_PURPOSE_BREACHED = "contest_public_purpose_breached"
    # Изменение условий и отмена публичного конкурса (статья 1058 ГК РФ).
    CONTEST_CHANGE_OR_CANCELLATION_BREACHED = "contest_change_or_cancellation_breached"
    # Решение о выплате награды и использование удостоенных работ
    # (статьи 1059 и 1060 ГК РФ).
    CONTEST_AWARD_DECISION_BREACHED = "contest_award_decision_breached"
    # Возврат участникам конкурса представленных работ (статья 1061 ГК РФ).
    CONTEST_WORKS_RETURN_BREACHED = "contest_works_return_breached"


REQUIRED_PUBLIC_PROMISE_PREDICATES = frozenset(PublicPromiseEvidencePredicate)


class PublicPromiseEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: PublicPromiseEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedPublicPromiseEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = PUBLIC_PROMISE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[PublicPromiseEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedPublicPromiseEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Public-promise evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Public-promise evidence contains duplicate legal source refs.")
        return self


class PublicPromiseFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    public_promise_or_contest_declared: bool
    promise_announcement_requirements_breached: bool
    reward_amount_or_distribution_breached: bool
    promise_revocation_rules_breached: bool
    revocation_expense_compensation_not_applied: bool
    contest_announcement_terms_breached: bool
    contest_public_purpose_breached: bool
    contest_change_or_cancellation_breached: bool
    contest_award_decision_breached: bool
    contest_works_return_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "PublicPromiseFactSet":
        if (
            self.revocation_expense_compensation_not_applied
            and not self.promise_revocation_rules_breached
        ):
            raise ValueError(
                "Невозмещение расходов отозвавшимся лицам относится только к случаю, когда "
                "нарушение правил об отмене публичного обещания награды установлено."
            )
        if (
            self.promise_announcement_requirements_breached
            and not self.public_promise_or_contest_declared
        ):
            raise ValueError(
                "Нарушение требований к объявлению относится только к публичному обещанию "
                "награды или публичному конкурсу."
            )
        return self


class PublicPromiseFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class PublicPromiseEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: PublicPromiseFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[PublicPromiseFactProvenance] = Field(default_factory=list)


class PublicPromiseConstraintSet(BaseModel):
    id: str
    model_version: str = PUBLIC_PROMISE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class PublicPromiseEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    public_promise_qualified: bool
    announcement_requirements_duty_breached: bool
    reward_amount_and_distribution_duty_breached: bool
    promise_revocation_duty_breached: bool
    revocation_expense_compensation_breached: bool
    contest_terms_duty_breached: bool
    contest_public_purpose_duty_breached: bool
    contest_change_duty_breached: bool
    contest_award_decision_duty_breached: bool
    contest_works_duty_breached: bool
    requires_human_public_promise_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_public_promise_evidence(
    evidence: ReviewedPublicPromiseEvidence,
) -> PublicPromiseEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Public-promise evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Public-promise evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_PUBLIC_PROMISE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed public-promise evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_PUBLIC_PROMISE_PREDICATES
    }
    return PublicPromiseEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=PUBLIC_PROMISE_MAPPING_VERSION,
        facts=PublicPromiseFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            PublicPromiseFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_PUBLIC_PROMISE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_public_promise_constraint_set(
    mapping: PublicPromiseEvidenceMappingResult,
) -> PublicPromiseConstraintSet:
    return PublicPromiseConstraintSet(
        id=f"public-promise-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "public_promise_qualified == public_promise_or_contest_declared",
            "announcement_requirements_duty_breached == public_promise_qualified AND promise_announcement_requirements_breached",
            "reward_amount_and_distribution_duty_breached == public_promise_qualified AND reward_amount_or_distribution_breached",
            "promise_revocation_duty_breached == public_promise_qualified AND promise_revocation_rules_breached",
            "revocation_expense_compensation_breached == public_promise_qualified AND promise_revocation_rules_breached AND revocation_expense_compensation_not_applied",
            "contest_terms_duty_breached == public_promise_qualified AND contest_announcement_terms_breached",
            "contest_public_purpose_duty_breached == public_promise_qualified AND contest_public_purpose_breached",
            "contest_change_duty_breached == public_promise_qualified AND contest_change_or_cancellation_breached",
            "contest_award_decision_duty_breached == public_promise_qualified AND contest_award_decision_breached",
            "contest_works_duty_breached == public_promise_qualified AND contest_works_return_breached",
            "requires_human_public_promise_assessment == announcement_requirements_duty_breached OR reward_amount_and_distribution_duty_breached OR promise_revocation_duty_breached OR contest_terms_duty_breached OR contest_public_purpose_duty_breached OR contest_change_duty_breached OR contest_award_decision_duty_breached OR contest_works_duty_breached",
        ],
    )


def evaluate_public_promise_constraints(
    constraint_set: PublicPromiseConstraintSet,
    facts: PublicPromiseFactSet,
) -> PublicPromiseEvaluation:
    variables = {field_name: Bool(field_name) for field_name in PublicPromiseFactSet.model_fields}
    public_promise_qualified = Bool("public_promise_qualified")
    announcement_requirements_duty_breached = Bool("announcement_requirements_duty_breached")
    reward_amount_and_distribution_duty_breached = Bool(
        "reward_amount_and_distribution_duty_breached"
    )
    promise_revocation_duty_breached = Bool("promise_revocation_duty_breached")
    revocation_expense_compensation_breached = Bool("revocation_expense_compensation_breached")
    contest_terms_duty_breached = Bool("contest_terms_duty_breached")
    contest_public_purpose_duty_breached = Bool("contest_public_purpose_duty_breached")
    contest_change_duty_breached = Bool("contest_change_duty_breached")
    contest_award_decision_duty_breached = Bool("contest_award_decision_duty_breached")
    contest_works_duty_breached = Bool("contest_works_duty_breached")
    requires_human_public_promise_assessment = Bool("requires_human_public_promise_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(public_promise_qualified == variables["public_promise_or_contest_declared"])
    solver.add(
        announcement_requirements_duty_breached
        == And(public_promise_qualified, variables["promise_announcement_requirements_breached"])
    )
    solver.add(
        reward_amount_and_distribution_duty_breached
        == And(public_promise_qualified, variables["reward_amount_or_distribution_breached"])
    )
    solver.add(
        promise_revocation_duty_breached
        == And(public_promise_qualified, variables["promise_revocation_rules_breached"])
    )
    solver.add(
        revocation_expense_compensation_breached
        == And(
            public_promise_qualified,
            variables["promise_revocation_rules_breached"],
            variables["revocation_expense_compensation_not_applied"],
        )
    )
    solver.add(
        contest_terms_duty_breached
        == And(public_promise_qualified, variables["contest_announcement_terms_breached"])
    )
    solver.add(
        contest_public_purpose_duty_breached
        == And(public_promise_qualified, variables["contest_public_purpose_breached"])
    )
    solver.add(
        contest_change_duty_breached
        == And(public_promise_qualified, variables["contest_change_or_cancellation_breached"])
    )
    solver.add(
        contest_award_decision_duty_breached
        == And(public_promise_qualified, variables["contest_award_decision_breached"])
    )
    solver.add(
        contest_works_duty_breached
        == And(public_promise_qualified, variables["contest_works_return_breached"])
    )
    solver.add(
        requires_human_public_promise_assessment
        == Or(
            announcement_requirements_duty_breached,
            reward_amount_and_distribution_duty_breached,
            promise_revocation_duty_breached,
            contest_terms_duty_breached,
            contest_public_purpose_duty_breached,
            contest_change_duty_breached,
            contest_award_decision_duty_breached,
            contest_works_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return PublicPromiseEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            public_promise_qualified=False,
            announcement_requirements_duty_breached=False,
            reward_amount_and_distribution_duty_breached=False,
            promise_revocation_duty_breached=False,
            revocation_expense_compensation_breached=False,
            contest_terms_duty_breached=False,
            contest_public_purpose_duty_breached=False,
            contest_change_duty_breached=False,
            contest_award_decision_duty_breached=False,
            contest_works_duty_breached=False,
            requires_human_public_promise_assessment=True,
            reasons_ru=[
                "Набор фактов о публичном обещании награды и публичном конкурсе противоречив."
            ],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Отношения квалифицированы как публичное обещание награды или публичный конкурс: "
            "лицо, объявившее публично о выплате денежного вознаграждения или выдаче иной "
            "награды тому, кто совершит указанное в объявлении правомерное действие в "
            "указанный в нём срок, обязано выплатить обещанную награду любому, кто совершил "
            "соответствующее действие (статьи 1055 и 1057 ГК РФ)."
            if truth(public_promise_qualified)
            else (
                "Отношения не квалифицированы как публичное обещание награды или публичный конкурс."
            )
        ),
    ]
    if truth(announcement_requirements_duty_breached):
        reasons_ru.append(
            "Обязанность выплатить награду возникает при условии, что публичное обещание "
            "награды позволяет установить, кем она обещана; лицо, отозвавшееся на обещание, "
            "вправе требовать письменного подтверждения обещания и несёт риск последствий "
            "непредъявления такого требования (статья 1055 ГК РФ)."
        )
    if truth(reward_amount_and_distribution_duty_breached):
        reasons_ru.append(
            "Если размер награды в публичном обещании не указан, он определяется по соглашению "
            "с лицом, обещавшим награду, а при споре — судом; при совершении указанного "
            "действия несколькими лицами награда причитается тому, кто совершил его первым, "
            "либо распределяется между ними, если действие совершено одновременно или "
            "неделимо (статья 1055 ГК РФ)."
        )
    if truth(promise_revocation_duty_breached):
        reasons_ru.append(
            "Отказ от публичного обещания награды должен быть совершён в той же форме, в какой "
            "обещание было объявлено, и не допускается, если обещание содержит отказ от такой "
            "отмены, если дан срок для совершения действия либо если действие уже совершено "
            "(статья 1056 ГК РФ)."
        )
    if truth(revocation_expense_compensation_breached):
        reasons_ru.append(
            "Отмена публичного обещания награды не освобождает объявившее её лицо от "
            "возмещения отозвавшимся лицам расходов, понесённых ими в связи с совершением "
            "указанного в объявлении действия, в пределах указанной в объявлении награды "
            "(статья 1056 ГК РФ)."
        )
    if truth(contest_terms_duty_breached):
        reasons_ru.append(
            "Объявление о публичном конкурсе должно содержать существо задания, критерии и "
            "порядок оценки результатов, место, срок и порядок их представления, размер и "
            "форму награды, а также порядок и сроки объявления результатов конкурса "
            "(статья 1057 ГК РФ)."
        )
    if truth(contest_public_purpose_duty_breached):
        reasons_ru.append(
            "Публичный конкурс должен быть направлен на достижение каких-либо общественно "
            "полезных целей; он может быть открытым или закрытым, а при открытом конкурсе "
            "допускается предварительная квалификация участников (статья 1057 ГК РФ)."
        )
    if truth(contest_change_duty_breached):
        reasons_ru.append(
            "Изменение условий и отмена публичного конкурса допускаются только в течение первой "
            "половины установленного для представления работ срока, тем же способом, каким "
            "конкурс был объявлен, с возмещением расходов участникам, выполнившим работу до "
            "того, как им стало или должно было стать известно об изменении "
            "(статья 1058 ГК РФ)."
        )
    if truth(contest_award_decision_duty_breached):
        reasons_ru.append(
            "Решение о выплате награды принимается и сообщается участникам в порядке и в сроки, "
            "установленные в объявлении о конкурсе; при присуждении награды нескольким лицам "
            "она распределяется в соответствии с условиями конкурса, а использование "
            "удостоенных наград произведений науки, литературы и искусства подчиняется "
            "правилам статьи 1060 ГК РФ (статьи 1059 и 1060 ГК РФ)."
        )
    if truth(contest_works_duty_breached):
        reasons_ru.append(
            "Организатор публичного конкурса обязан возвратить участникам конкурса работы, не "
            "удостоенные награды, если иное не предусмотрено объявлением о конкурсе и не "
            "вытекает из характера выполненной работы (статья 1061 ГК РФ)."
        )
    return PublicPromiseEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        public_promise_qualified=truth(public_promise_qualified),
        announcement_requirements_duty_breached=truth(announcement_requirements_duty_breached),
        reward_amount_and_distribution_duty_breached=truth(
            reward_amount_and_distribution_duty_breached
        ),
        promise_revocation_duty_breached=truth(promise_revocation_duty_breached),
        revocation_expense_compensation_breached=truth(revocation_expense_compensation_breached),
        contest_terms_duty_breached=truth(contest_terms_duty_breached),
        contest_public_purpose_duty_breached=truth(contest_public_purpose_duty_breached),
        contest_change_duty_breached=truth(contest_change_duty_breached),
        contest_award_decision_duty_breached=truth(contest_award_decision_duty_breached),
        contest_works_duty_breached=truth(contest_works_duty_breached),
        requires_human_public_promise_assessment=truth(requires_human_public_promise_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о публичном обещании награды и "
            "публичном конкурсе и не заменяет судебную оценку.",
            "Существо конкурсного задания, общественная полезность цели конкурса и "
            "обоснованность оценки работ оцениваются экспертом и судом "
            "(статьи 1057 и 1059 ГК РФ).",
        ],
    )
