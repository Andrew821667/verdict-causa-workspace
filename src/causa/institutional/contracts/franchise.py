from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


FRANCHISE_EVIDENCE_SCHEMA_VERSION = "contracts.franchise-evidence.v0"
FRANCHISE_MAPPING_VERSION = "contracts-reviewed-franchise-to-facts-v0"
FRANCHISE_MODEL_VERSION = "contracts-franchise-articles-1027-1040-v0"


class FranchiseEvidencePredicate(str, Enum):
    # Договор коммерческой концессии, объём прав и стороны (статья 1027 ГК РФ).
    FRANCHISE_CONTRACT_CONCLUDED = "franchise_contract_concluded"
    FRANCHISE_SCOPE_OR_PARTIES_BREACHED = "franchise_scope_or_parties_breached"
    # Форма и государственная регистрация предоставления права (статья 1028 ГК РФ).
    FRANCHISE_FORM_OR_REGISTRATION_BREACHED = "franchise_form_or_registration_breached"
    FORM_INVALIDITY_NOT_APPLIED = "form_invalidity_not_applied"
    # Коммерческая субконцессия (статья 1029 ГК РФ).
    COMMERCIAL_SUBCONCESSION_RULES_BREACHED = "commercial_subconcession_rules_breached"
    # Вознаграждение по договору (статья 1030 ГК РФ).
    FRANCHISE_REMUNERATION_RULES_BREACHED = "franchise_remuneration_rules_breached"
    # Обязанности правообладателя и пользователя (статьи 1031 и 1032 ГК РФ).
    RIGHTHOLDER_OBLIGATIONS_BREACHED = "rightholder_obligations_breached"
    USER_OBLIGATIONS_BREACHED = "user_obligations_breached"
    # Ограничения прав сторон и ничтожные условия (статья 1033 ГК РФ).
    FRANCHISE_RESTRICTIONS_RULES_BREACHED = "franchise_restrictions_rules_breached"
    # Ответственность правообладателя, изменение и прекращение договора
    # (статьи 1034, 1035 и 1037–1040 ГК РФ).
    LIABILITY_OR_TERMINATION_RULES_BREACHED = "liability_or_termination_rules_breached"


REQUIRED_FRANCHISE_PREDICATES = frozenset(FranchiseEvidencePredicate)


class FranchiseEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: FranchiseEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedFranchiseEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = FRANCHISE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[FranchiseEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedFranchiseEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Franchise evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Franchise evidence contains duplicate legal source refs.")
        return self


class FranchiseFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    franchise_contract_concluded: bool
    franchise_scope_or_parties_breached: bool
    franchise_form_or_registration_breached: bool
    form_invalidity_not_applied: bool
    commercial_subconcession_rules_breached: bool
    franchise_remuneration_rules_breached: bool
    rightholder_obligations_breached: bool
    user_obligations_breached: bool
    franchise_restrictions_rules_breached: bool
    liability_or_termination_rules_breached: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "FranchiseFactSet":
        if self.form_invalidity_not_applied and not self.franchise_form_or_registration_breached:
            raise ValueError(
                "Неприменение последствий несоблюдения формы относится только к случаю, когда "
                "нарушение письменной формы или государственной регистрации установлено."
            )
        if self.franchise_scope_or_parties_breached and not self.franchise_contract_concluded:
            raise ValueError(
                "Нарушение объёма предоставленных прав и состава сторон относится только к "
                "договору коммерческой концессии."
            )
        return self


class FranchiseFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class FranchiseEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: FranchiseFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[FranchiseFactProvenance] = Field(default_factory=list)


class FranchiseConstraintSet(BaseModel):
    id: str
    model_version: str = FRANCHISE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class FranchiseEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    franchise_qualified: bool
    scope_and_parties_duty_breached: bool
    form_and_registration_duty_breached: bool
    form_invalidity_breached: bool
    subconcession_duty_breached: bool
    remuneration_duty_breached: bool
    rightholder_obligations_duty_breached: bool
    user_obligations_duty_breached: bool
    restrictions_duty_breached: bool
    liability_and_termination_duty_breached: bool
    requires_human_franchise_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_franchise_evidence(
    evidence: ReviewedFranchiseEvidence,
) -> FranchiseEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Franchise evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Franchise evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_FRANCHISE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed franchise evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_FRANCHISE_PREDICATES
    }
    return FranchiseEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=FRANCHISE_MAPPING_VERSION,
        facts=FranchiseFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            FranchiseFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_FRANCHISE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_franchise_constraint_set(
    mapping: FranchiseEvidenceMappingResult,
) -> FranchiseConstraintSet:
    return FranchiseConstraintSet(
        id=f"franchise-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "franchise_qualified == franchise_contract_concluded",
            "scope_and_parties_duty_breached == franchise_qualified AND franchise_scope_or_parties_breached",
            "form_and_registration_duty_breached == franchise_qualified AND franchise_form_or_registration_breached",
            "form_invalidity_breached == franchise_qualified AND franchise_form_or_registration_breached AND form_invalidity_not_applied",
            "subconcession_duty_breached == franchise_qualified AND commercial_subconcession_rules_breached",
            "remuneration_duty_breached == franchise_qualified AND franchise_remuneration_rules_breached",
            "rightholder_obligations_duty_breached == franchise_qualified AND rightholder_obligations_breached",
            "user_obligations_duty_breached == franchise_qualified AND user_obligations_breached",
            "restrictions_duty_breached == franchise_qualified AND franchise_restrictions_rules_breached",
            "liability_and_termination_duty_breached == franchise_qualified AND liability_or_termination_rules_breached",
            "requires_human_franchise_assessment == scope_and_parties_duty_breached OR form_and_registration_duty_breached OR subconcession_duty_breached OR remuneration_duty_breached OR rightholder_obligations_duty_breached OR user_obligations_duty_breached OR restrictions_duty_breached OR liability_and_termination_duty_breached",
        ],
    )


def evaluate_franchise_constraints(
    constraint_set: FranchiseConstraintSet,
    facts: FranchiseFactSet,
) -> FranchiseEvaluation:
    variables = {field_name: Bool(field_name) for field_name in FranchiseFactSet.model_fields}
    franchise_qualified = Bool("franchise_qualified")
    scope_and_parties_duty_breached = Bool("scope_and_parties_duty_breached")
    form_and_registration_duty_breached = Bool("form_and_registration_duty_breached")
    form_invalidity_breached = Bool("form_invalidity_breached")
    subconcession_duty_breached = Bool("subconcession_duty_breached")
    remuneration_duty_breached = Bool("remuneration_duty_breached")
    rightholder_obligations_duty_breached = Bool("rightholder_obligations_duty_breached")
    user_obligations_duty_breached = Bool("user_obligations_duty_breached")
    restrictions_duty_breached = Bool("restrictions_duty_breached")
    liability_and_termination_duty_breached = Bool("liability_and_termination_duty_breached")
    requires_human_franchise_assessment = Bool("requires_human_franchise_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(franchise_qualified == variables["franchise_contract_concluded"])
    solver.add(
        scope_and_parties_duty_breached
        == And(franchise_qualified, variables["franchise_scope_or_parties_breached"])
    )
    solver.add(
        form_and_registration_duty_breached
        == And(franchise_qualified, variables["franchise_form_or_registration_breached"])
    )
    solver.add(
        form_invalidity_breached
        == And(
            franchise_qualified,
            variables["franchise_form_or_registration_breached"],
            variables["form_invalidity_not_applied"],
        )
    )
    solver.add(
        subconcession_duty_breached
        == And(franchise_qualified, variables["commercial_subconcession_rules_breached"])
    )
    solver.add(
        remuneration_duty_breached
        == And(franchise_qualified, variables["franchise_remuneration_rules_breached"])
    )
    solver.add(
        rightholder_obligations_duty_breached
        == And(franchise_qualified, variables["rightholder_obligations_breached"])
    )
    solver.add(
        user_obligations_duty_breached
        == And(franchise_qualified, variables["user_obligations_breached"])
    )
    solver.add(
        restrictions_duty_breached
        == And(franchise_qualified, variables["franchise_restrictions_rules_breached"])
    )
    solver.add(
        liability_and_termination_duty_breached
        == And(franchise_qualified, variables["liability_or_termination_rules_breached"])
    )
    solver.add(
        requires_human_franchise_assessment
        == Or(
            scope_and_parties_duty_breached,
            form_and_registration_duty_breached,
            subconcession_duty_breached,
            remuneration_duty_breached,
            rightholder_obligations_duty_breached,
            user_obligations_duty_breached,
            restrictions_duty_breached,
            liability_and_termination_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return FranchiseEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            franchise_qualified=False,
            scope_and_parties_duty_breached=False,
            form_and_registration_duty_breached=False,
            form_invalidity_breached=False,
            subconcession_duty_breached=False,
            remuneration_duty_breached=False,
            rightholder_obligations_duty_breached=False,
            user_obligations_duty_breached=False,
            restrictions_duty_breached=False,
            liability_and_termination_duty_breached=False,
            requires_human_franchise_assessment=True,
            reasons_ru=["Набор фактов о коммерческой концессии противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Договор квалифицирован как договор коммерческой концессии: правообладатель "
            "обязуется предоставить пользователю за вознаграждение на срок или без указания "
            "срока право использовать в предпринимательской деятельности комплекс "
            "принадлежащих правообладателю исключительных прав, включающий право на товарный "
            "знак, знак обслуживания, а также права на другие объекты исключительных прав "
            "(статья 1027 ГК РФ)."
            if truth(franchise_qualified)
            else "Отношения не квалифицированы как договор коммерческой концессии."
        ),
    ]
    if truth(scope_and_parties_duty_breached):
        reasons_ru.append(
            "Договор коммерческой концессии предусматривает использование комплекса "
            "исключительных прав, деловой репутации и коммерческого опыта правообладателя в "
            "определённом объёме, а сторонами договора могут быть только коммерческие "
            "организации и граждане, зарегистрированные в качестве индивидуальных "
            "предпринимателей (статья 1027 ГК РФ)."
        )
    if truth(form_and_registration_duty_breached):
        reasons_ru.append(
            "Договор коммерческой концессии заключается в письменной форме, а предоставление "
            "права использования комплекса исключительных прав подлежит государственной "
            "регистрации в федеральном органе исполнительной власти по интеллектуальной "
            "собственности (статья 1028 ГК РФ)."
        )
    if truth(form_invalidity_breached):
        reasons_ru.append(
            "Несоблюдение письменной формы договора коммерческой концессии влечёт его "
            "ничтожность, а при несоблюдении требования о государственной регистрации "
            "предоставление права использования считается несостоявшимся "
            "(статья 1028 ГК РФ)."
        )
    if truth(subconcession_duty_breached):
        reasons_ru.append(
            "Договором коммерческой концессии может быть предусмотрено право пользователя "
            "разрешать другим лицам использование комплекса исключительных прав на условиях "
            "субконцессии; договор субконцессии не может быть заключён на более длительный "
            "срок, чем основной договор (статья 1029 ГК РФ)."
        )
    if truth(remuneration_duty_breached):
        reasons_ru.append(
            "Вознаграждение по договору коммерческой концессии может выплачиваться "
            "пользователем в форме фиксированных разовых или периодических платежей, "
            "отчислений от выручки, наценки на оптовую цену товаров либо в иной форме, "
            "предусмотренной договором (статья 1030 ГК РФ)."
        )
    if truth(rightholder_obligations_duty_breached):
        reasons_ru.append(
            "Правообладатель обязан передать пользователю техническую и коммерческую "
            "документацию, проинструктировать пользователя и его работников, обеспечить "
            "государственную регистрацию предоставления права, оказывать постоянное "
            "техническое и консультативное содействие и контролировать качество товаров, "
            "работ и услуг (статья 1031 ГК РФ)."
        )
    if truth(user_obligations_duty_breached):
        reasons_ru.append(
            "Пользователь обязан использовать средства индивидуализации правообладателя "
            "указанным в договоре образом, обеспечивать соответствие качества товаров, работ и "
            "услуг, соблюдать инструкции правообладателя, оказывать покупателям "
            "дополнительные услуги, не разглашать секреты производства и информировать "
            "покупателей об использовании прав по договору концессии (статья 1032 ГК РФ)."
        )
    if truth(restrictions_duty_breached):
        reasons_ru.append(
            "Договором коммерческой концессии могут быть предусмотрены ограничения прав "
            "сторон, однако условия, по которым правообладатель определяет цену продажи "
            "товаров пользователем либо пользователь вправе продавать товары исключительно "
            "покупателям определённой категории или по месту жительства на закреплённой "
            "территории, являются ничтожными (статья 1033 ГК РФ)."
        )
    if truth(liability_and_termination_duty_breached):
        reasons_ru.append(
            "Правообладатель несёт субсидиарную, а по требованиям к пользователю как "
            "изготовителю продукции — солидарную ответственность за качество товаров, работ и "
            "услуг; изменение, прекращение и сохранение договора при переходе прав "
            "подчиняются правилам статей 1034, 1035 и 1037–1040 ГК РФ."
        )
    return FranchiseEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        franchise_qualified=truth(franchise_qualified),
        scope_and_parties_duty_breached=truth(scope_and_parties_duty_breached),
        form_and_registration_duty_breached=truth(form_and_registration_duty_breached),
        form_invalidity_breached=truth(form_invalidity_breached),
        subconcession_duty_breached=truth(subconcession_duty_breached),
        remuneration_duty_breached=truth(remuneration_duty_breached),
        rightholder_obligations_duty_breached=truth(rightholder_obligations_duty_breached),
        user_obligations_duty_breached=truth(user_obligations_duty_breached),
        restrictions_duty_breached=truth(restrictions_duty_breached),
        liability_and_termination_duty_breached=truth(liability_and_termination_duty_breached),
        requires_human_franchise_assessment=truth(requires_human_franchise_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о коммерческой концессии и не заменяет "
            "судебную оценку.",
            "Объём переданных исключительных прав, качество товаров пользователя и "
            "добросовестность сторон оцениваются экспертом и судом "
            "(статьи 1027, 1032 и 1034 ГК РФ).",
        ],
    )
