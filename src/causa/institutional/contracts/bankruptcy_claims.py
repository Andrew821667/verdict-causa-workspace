from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


BANKRUPTCY_CLAIMS_EVIDENCE_SCHEMA_VERSION = "contracts.bankruptcy-claims-evidence.v0"
BANKRUPTCY_CLAIMS_MAPPING_VERSION = "contracts-reviewed-bankruptcy-claims-to-facts-v0"
BANKRUPTCY_CLAIMS_MODEL_VERSION = "contracts-bankruptcy-claims-articles-5-63-127fz-v0"

# Дословный текст статей 5 и 63 127-ФЗ — synthetic_sources.py,
# synthetic-ru-127fz-5-current-payments-v1 и synthetic-ru-127fz-63-observation-effects-v1.
BANKRUPTCY_CLAIMS_LEGAL_SOURCE_REFS = (
    "synthetic-ru-127fz-5-current-payments-v1",
    "synthetic-ru-127fz-63-observation-effects-v1",
)


class BankruptcyClaimsEvidencePredicate(str, Enum):
    # Момент возникновения обязательства относительно даты принятия заявления
    # о банкротстве — единственное основание деления на текущие и реестровые
    # платежи (пункт 1 статьи 5 127-ФЗ).
    OBLIGATION_AROSE_BEFORE_PETITION_ACCEPTED = "obligation_arose_before_petition_accepted"
    # Введена ли процедура наблюдения (или последующая процедура), с которой
    # пункт 1 статьи 63 связывает ограничение индивидуального взыскания.
    OBSERVATION_INTRODUCED = "observation_introduced"
    # Кредитор пытается получить удовлетворение вне порядка предъявления
    # требований, установленного законом (отдельный иск, исполнительное
    # производство), а не через включение в реестр.
    CREDITOR_SEEKS_INDIVIDUAL_ENFORCEMENT = "creditor_seeks_individual_enforcement"
    # Узкое исключение абзаца четвёртого пункта 1 статьи 63: исполнительный
    # документ выдан на основании вступившего в силу до наблюдения судебного
    # акта о взыскании зарплаты, авторского вознаграждения, истребовании
    # имущества из чужого незаконного владения или о возмещении вреда жизни
    # или здоровью.
    ENFORCEMENT_DOCUMENT_PREDATES_OBSERVATION_AND_IS_EXEMPT_CATEGORY = (
        "enforcement_document_predates_observation_and_is_exempt_category"
    )


REQUIRED_BANKRUPTCY_CLAIMS_PREDICATES = frozenset(BankruptcyClaimsEvidencePredicate)


class BankruptcyClaimsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: BankruptcyClaimsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedBankruptcyClaimsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = BANKRUPTCY_CLAIMS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[BankruptcyClaimsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedBankruptcyClaimsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Bankruptcy-claims evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Bankruptcy-claims evidence contains duplicate legal source refs.")
        return self


class BankruptcyClaimsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    obligation_arose_before_petition_accepted: bool
    observation_introduced: bool
    creditor_seeks_individual_enforcement: bool
    enforcement_document_predates_observation_and_is_exempt_category: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "BankruptcyClaimsFactSet":
        if (
            self.enforcement_document_predates_observation_and_is_exempt_category
            and not self.creditor_seeks_individual_enforcement
        ):
            raise ValueError(
                "Исключение по вступившему в силу исполнительному документу неприменимо, "
                "если кредитор не добивается индивидуального взыскания."
            )
        if (
            self.enforcement_document_predates_observation_and_is_exempt_category
            and not self.observation_introduced
        ):
            raise ValueError(
                "Исключение пункта 1 статьи 63 имеет смысл только при введённой процедуре "
                "наблюдения (или последующей процедуре)."
            )
        return self


class BankruptcyClaimsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class BankruptcyClaimsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: BankruptcyClaimsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[BankruptcyClaimsFactProvenance] = Field(default_factory=list)


class BankruptcyClaimsConstraintSet(BaseModel):
    id: str
    model_version: str = BANKRUPTCY_CLAIMS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class BankruptcyClaimsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    claim_is_current: bool
    individual_enforcement_suspended: bool
    individual_enforcement_permitted_by_exception: bool
    requires_human_bankruptcy_claims_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_bankruptcy_claims_evidence(
    evidence: ReviewedBankruptcyClaimsEvidence,
) -> BankruptcyClaimsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Bankruptcy-claims evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Bankruptcy-claims evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_BANKRUPTCY_CLAIMS_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed bankruptcy-claims evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_BANKRUPTCY_CLAIMS_PREDICATES
    }
    return BankruptcyClaimsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=BANKRUPTCY_CLAIMS_MAPPING_VERSION,
        facts=BankruptcyClaimsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            BankruptcyClaimsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_BANKRUPTCY_CLAIMS_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_bankruptcy_claims_constraint_set(
    mapping: BankruptcyClaimsEvidenceMappingResult,
) -> BankruptcyClaimsConstraintSet:
    return BankruptcyClaimsConstraintSet(
        id=f"bankruptcy-claims-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "claim_is_current == NOT obligation_arose_before_petition_accepted",
            (
                "individual_enforcement_suspended == observation_introduced AND "
                "obligation_arose_before_petition_accepted AND "
                "creditor_seeks_individual_enforcement AND "
                "NOT enforcement_document_predates_observation_and_is_exempt_category"
            ),
            (
                "individual_enforcement_permitted_by_exception == observation_introduced AND "
                "obligation_arose_before_petition_accepted AND "
                "enforcement_document_predates_observation_and_is_exempt_category"
            ),
            "requires_human_bankruptcy_claims_assessment == claim_is_current",
        ],
    )


def evaluate_bankruptcy_claims_constraints(
    constraint_set: BankruptcyClaimsConstraintSet,
    facts: BankruptcyClaimsFactSet,
) -> BankruptcyClaimsEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in BankruptcyClaimsFactSet.model_fields
    }
    claim_is_current = Bool("claim_is_current")
    individual_enforcement_suspended = Bool("individual_enforcement_suspended")
    individual_enforcement_permitted_by_exception = Bool(
        "individual_enforcement_permitted_by_exception"
    )
    requires_human_bankruptcy_claims_assessment = Bool(
        "requires_human_bankruptcy_claims_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(claim_is_current == Not(variables["obligation_arose_before_petition_accepted"]))
    solver.add(
        individual_enforcement_suspended
        == And(
            variables["observation_introduced"],
            variables["obligation_arose_before_petition_accepted"],
            variables["creditor_seeks_individual_enforcement"],
            Not(variables["enforcement_document_predates_observation_and_is_exempt_category"]),
        )
    )
    solver.add(
        individual_enforcement_permitted_by_exception
        == And(
            variables["observation_introduced"],
            variables["obligation_arose_before_petition_accepted"],
            variables["enforcement_document_predates_observation_and_is_exempt_category"],
        )
    )
    solver.add(requires_human_bankruptcy_claims_assessment == claim_is_current)

    satisfiable = solver.check() == sat
    if not satisfiable:
        return BankruptcyClaimsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            claim_is_current=False,
            individual_enforcement_suspended=False,
            individual_enforcement_permitted_by_exception=False,
            requires_human_bankruptcy_claims_assessment=True,
            reasons_ru=["Набор фактов о требовании кредитора в деле о банкротстве противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = []
    if truth(claim_is_current):
        reasons_ru.append(
            "Обязательство возникло после даты принятия заявления о признании должника "
            "банкротом — требование текущее: не включается в реестр требований кредиторов, "
            "а кредитор не признаётся лицом, участвующим в деле (пункты 1–2 статьи 5 127-ФЗ)."
        )
    else:
        reasons_ru.append(
            "Обязательство возникло до даты принятия заявления о признании должника "
            "банкротом — требование реестровое: для участия в деле срок его исполнения "
            "считается наступившим, а предъявляется оно в установленном законом порядке "
            "(пункт 2 статьи 5, пункт 3 статьи 63 127-ФЗ)."
        )
    if truth(individual_enforcement_suspended):
        reasons_ru.append(
            "С даты введения наблюдения индивидуальное взыскание по этому требованию "
            "приостановлено: оно может быть предъявлено только в порядке, установленном "
            "127-ФЗ, а исполнение исполнительных документов приостанавливается "
            "(пункт 1 статьи 63 127-ФЗ)."
        )
    if truth(individual_enforcement_permitted_by_exception):
        reasons_ru.append(
            "Действует узкое исключение абзаца четвёртого пункта 1 статьи 63 127-ФЗ: "
            "исполнительный документ выдан на основании вступившего в силу до наблюдения "
            "судебного акта из перечня, на который приостановление не распространяется."
        )
    if truth(requires_human_bankruptcy_claims_assessment):
        reasons_ru.append(
            "Пункты 2 и 3 статьи 5 127-ФЗ, определяющие режим текущего платежа, признаны "
            "частично не соответствующими Конституции РФ (постановления КС РФ от 19.03.2024 "
            "№ 11-П и от 31.05.2023 № 28-П), а правовое регулирование до внесения изменений "
            "устанавливает сам текст постановлений — модель этого не разрешает и передаёт "
            "требование на проверку юристом."
        )
    return BankruptcyClaimsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        claim_is_current=truth(claim_is_current),
        individual_enforcement_suspended=truth(individual_enforcement_suspended),
        individual_enforcement_permitted_by_exception=truth(
            individual_enforcement_permitted_by_exception
        ),
        requires_human_bankruptcy_claims_assessment=truth(
            requires_human_bankruptcy_claims_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель разбирает только режим текущего/реестрового требования по статьям 5 и 63 "
            "127-ФЗ и не устанавливает очередность удовлетворения реестровых требований.",
            "Модель не разрешает переходный период по постановлениям КС РФ, признавшим "
            "пункты 2 и 3 статьи 5 частично не соответствующими Конституции РФ.",
        ],
    )
