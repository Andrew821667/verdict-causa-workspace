from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


BANKRUPTCY_SETOFF_EVIDENCE_SCHEMA_VERSION = "contracts.bankruptcy-setoff-evidence.v0"
BANKRUPTCY_SETOFF_MAPPING_VERSION = "contracts-reviewed-bankruptcy-setoff-to-facts-v0"
BANKRUPTCY_SETOFF_MODEL_VERSION = "contracts-bankruptcy-setoff-articles-63-134-127fz-v0"

# Дословный текст статей 63 и 134 127-ФЗ — synthetic_sources.py,
# synthetic-ru-127fz-63-observation-effects-v1,
# synthetic-ru-127fz-134-creditor-ranking-v1.
BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS = (
    "synthetic-ru-127fz-63-observation-effects-v1",
    "synthetic-ru-127fz-134-creditor-ranking-v1",
)


class BankruptcySetoffEvidencePredicate(str, Enum):
    # С даты введения наблюдения (или последующей процедуры) действует запрет
    # зачёта, нарушающего очерёдность (абзац шестой пункта 1 статьи 63).
    OBSERVATION_INTRODUCED = "observation_introduced"
    # Сторона заявляет о зачёте встречного однородного требования к должнику
    # (общее основание статьи 410 ГК РФ) — механизм прекращения, к которому
    # относится запрет статьи 63.
    SETOFF_OF_MUTUAL_HOMOGENEOUS_CLAIMS_ASSERTED = "setoff_of_mutual_homogeneous_claims_asserted"
    # Совершение зачёта нарушило бы очерёдность удовлетворения требований
    # кредиторов, установленную пунктом 4 статьи 134 (кредитор получил бы
    # полное погашение в обход кредиторов той же или более высокой очереди).
    SETOFF_WOULD_VIOLATE_PRIORITY_ORDER = "setoff_would_violate_priority_order"
    # Обязательства прекращаются не зачётом, а определением и исполнением
    # нетто-обязательства по финансовым договорам в порядке статьи 4.1 —
    # узкое законное исключение из запрета, названное в самом абзаце шестом
    # пункта 1 статьи 63. Текст статьи 4.1 в пакете не источникован — это
    # внешний факт, а не отдельная проверяемая норма настоящей модели.
    ARISES_FROM_FINANCIAL_CONTRACT_NETTING_UNDER_ARTICLE_4_1 = (
        "arises_from_financial_contract_netting_under_article_4_1"
    )


REQUIRED_BANKRUPTCY_SETOFF_PREDICATES = frozenset(BankruptcySetoffEvidencePredicate)


class BankruptcySetoffEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: BankruptcySetoffEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedBankruptcySetoffEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = BANKRUPTCY_SETOFF_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[BankruptcySetoffEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedBankruptcySetoffEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Bankruptcy-setoff evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Bankruptcy-setoff evidence contains duplicate legal source refs.")
        return self


class BankruptcySetoffFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_introduced: bool
    setoff_of_mutual_homogeneous_claims_asserted: bool
    setoff_would_violate_priority_order: bool
    arises_from_financial_contract_netting_under_article_4_1: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "BankruptcySetoffFactSet":
        if (
            self.setoff_of_mutual_homogeneous_claims_asserted
            and self.arises_from_financial_contract_netting_under_article_4_1
        ):
            raise ValueError(
                "Зачёт встречного однородного требования и определение нетто-обязательства "
                "по финансовым договорам — разные механизмы прекращения обязательств: "
                "одна операция не может быть одновременно и тем, и другим."
            )
        if (
            self.setoff_would_violate_priority_order
            and not self.setoff_of_mutual_homogeneous_claims_asserted
        ):
            raise ValueError(
                "Нарушение очерёдности зачётом неприменимо, если зачёт встречного "
                "однородного требования не заявлен."
            )
        return self


class BankruptcySetoffFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class BankruptcySetoffEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: BankruptcySetoffFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[BankruptcySetoffFactProvenance] = Field(default_factory=list)


class BankruptcySetoffConstraintSet(BaseModel):
    id: str
    model_version: str = BANKRUPTCY_SETOFF_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class BankruptcySetoffEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    setoff_prohibited: bool
    setoff_permitted_as_priority_neutral: bool
    netting_permitted_by_financial_contract_exception: bool
    requires_human_bankruptcy_setoff_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_bankruptcy_setoff_evidence(
    evidence: ReviewedBankruptcySetoffEvidence,
) -> BankruptcySetoffEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Bankruptcy-setoff evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Bankruptcy-setoff evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_BANKRUPTCY_SETOFF_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed bankruptcy-setoff evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_BANKRUPTCY_SETOFF_PREDICATES
    }
    return BankruptcySetoffEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=BANKRUPTCY_SETOFF_MAPPING_VERSION,
        facts=BankruptcySetoffFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            BankruptcySetoffFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_BANKRUPTCY_SETOFF_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_bankruptcy_setoff_constraint_set(
    mapping: BankruptcySetoffEvidenceMappingResult,
) -> BankruptcySetoffConstraintSet:
    return BankruptcySetoffConstraintSet(
        id=f"bankruptcy-setoff-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            (
                "setoff_prohibited == observation_introduced AND "
                "setoff_of_mutual_homogeneous_claims_asserted AND "
                "setoff_would_violate_priority_order AND "
                "NOT arises_from_financial_contract_netting_under_article_4_1"
            ),
            (
                "setoff_permitted_as_priority_neutral == observation_introduced AND "
                "setoff_of_mutual_homogeneous_claims_asserted AND "
                "NOT setoff_would_violate_priority_order"
            ),
            (
                "netting_permitted_by_financial_contract_exception == "
                "arises_from_financial_contract_netting_under_article_4_1"
            ),
            (
                "requires_human_bankruptcy_setoff_assessment == "
                "setoff_of_mutual_homogeneous_claims_asserted AND "
                "setoff_would_violate_priority_order"
            ),
        ],
    )


def evaluate_bankruptcy_setoff_constraints(
    constraint_set: BankruptcySetoffConstraintSet,
    facts: BankruptcySetoffFactSet,
) -> BankruptcySetoffEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in BankruptcySetoffFactSet.model_fields
    }
    setoff_prohibited = Bool("setoff_prohibited")
    setoff_permitted_as_priority_neutral = Bool("setoff_permitted_as_priority_neutral")
    netting_permitted_by_financial_contract_exception = Bool(
        "netting_permitted_by_financial_contract_exception"
    )
    requires_human_bankruptcy_setoff_assessment = Bool(
        "requires_human_bankruptcy_setoff_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        setoff_prohibited
        == And(
            variables["observation_introduced"],
            variables["setoff_of_mutual_homogeneous_claims_asserted"],
            variables["setoff_would_violate_priority_order"],
            Not(variables["arises_from_financial_contract_netting_under_article_4_1"]),
        )
    )
    solver.add(
        setoff_permitted_as_priority_neutral
        == And(
            variables["observation_introduced"],
            variables["setoff_of_mutual_homogeneous_claims_asserted"],
            Not(variables["setoff_would_violate_priority_order"]),
        )
    )
    solver.add(
        netting_permitted_by_financial_contract_exception
        == variables["arises_from_financial_contract_netting_under_article_4_1"]
    )
    solver.add(
        requires_human_bankruptcy_setoff_assessment
        == And(
            variables["setoff_of_mutual_homogeneous_claims_asserted"],
            variables["setoff_would_violate_priority_order"],
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return BankruptcySetoffEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            setoff_prohibited=False,
            setoff_permitted_as_priority_neutral=False,
            netting_permitted_by_financial_contract_exception=False,
            requires_human_bankruptcy_setoff_assessment=True,
            reasons_ru=["Набор фактов о зачёте требований в деле о банкротстве противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = []
    if truth(setoff_prohibited):
        reasons_ru.append(
            "Зачёт встречного однородного требования не допускается: он нарушил бы "
            "очерёдность удовлетворения требований кредиторов, установленную пунктом 4 "
            "статьи 134 127-ФЗ (абзац шестой пункта 1 статьи 63 127-ФЗ)."
        )
    if truth(setoff_permitted_as_priority_neutral):
        reasons_ru.append(
            "Зачёт встречного однородного требования допустим: он не нарушает "
            "очерёдность удовлетворения требований кредиторов, установленную пунктом 4 "
            "статьи 134 127-ФЗ, а запрет абзаца шестого пункта 1 статьи 63 127-ФЗ "
            "обусловлен именно нарушением очерёдности."
        )
    if truth(netting_permitted_by_financial_contract_exception):
        reasons_ru.append(
            "Прекращение обязательств происходит через определение и исполнение "
            "нетто-обязательства по финансовым договорам в порядке статьи 4.1 127-ФЗ — "
            "запрет абзаца шестого пункта 1 статьи 63 127-ФЗ на этот случай прямо не "
            "распространяется."
        )
    if not (
        truth(setoff_prohibited)
        or truth(setoff_permitted_as_priority_neutral)
        or truth(netting_permitted_by_financial_contract_exception)
    ):
        reasons_ru.append(
            "Ни зачёт встречного однородного требования, ни определение нетто-обязательства "
            "по финансовым договорам не заявлены — статья 63 127-ФЗ к прекращению этого "
            "обязательства не применяется."
        )
    if truth(requires_human_bankruptcy_setoff_assessment):
        reasons_ru.append(
            "Модель принимает саму квалификацию операции как зачёта встречного однородного "
            "требования готовым фактом. Отличить действительный зачёт двух независимых "
            "требований от определения итогового сальдо по единому встречному "
            "предоставлению в рамках одного двустороннего договора — вопрос правовой "
            "квалификации, который модель не разрешает и передаёт на проверку юристом."
        )
    return BankruptcySetoffEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        setoff_prohibited=truth(setoff_prohibited),
        setoff_permitted_as_priority_neutral=truth(setoff_permitted_as_priority_neutral),
        netting_permitted_by_financial_contract_exception=truth(
            netting_permitted_by_financial_contract_exception
        ),
        requires_human_bankruptcy_setoff_assessment=truth(
            requires_human_bankruptcy_setoff_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель разбирает только запрет зачёта абзаца шестого пункта 1 статьи 63 127-ФЗ "
            "и названное в нём же исключение для нетто-обязательств по финансовым "
            "договорам — текст статьи 4.1 127-ФЗ, к которой эта статья отсылает, в пакете "
            "не источникован, и признак 'нетто-обязательство по статье 4.1' модель "
            "принимает как внешний факт, а не проверяет самостоятельно.",
            "Модель не разрешает вопрос о том, является ли операция по существу зачётом "
            "двух независимых требований (статья 410 ГК РФ) или определением сальдо "
            "взаимных предоставлений по одному договору — это открытый вопрос "
            "квалификации, а не отдельная норма настоящей модели.",
        ],
    )
