from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


BANKRUPTCY_CONTEST_EVIDENCE_SCHEMA_VERSION = "contracts.bankruptcy-contest-evidence.v0"
BANKRUPTCY_CONTEST_MAPPING_VERSION = "contracts-reviewed-bankruptcy-contest-to-facts-v0"
BANKRUPTCY_CONTEST_MODEL_VERSION = (
    "contracts-bankruptcy-contest-articles-61-1-61-2-61-3-61-9-127fz-v0"
)

# Дословный текст статей 61.1, 61.2, 61.3 и 61.9 127-ФЗ — synthetic_sources.py,
# synthetic-ru-127fz-61.1-contest-transactions-general-v1,
# synthetic-ru-127fz-61.2-contest-suspicious-transaction-v1,
# synthetic-ru-127fz-61.3-contest-preference-transaction-v1,
# synthetic-ru-127fz-61.9-contest-standing-v1.
BANKRUPTCY_CONTEST_LEGAL_SOURCE_REFS = (
    "synthetic-ru-127fz-61.1-contest-transactions-general-v1",
    "synthetic-ru-127fz-61.2-contest-suspicious-transaction-v1",
    "synthetic-ru-127fz-61.3-contest-preference-transaction-v1",
    "synthetic-ru-127fz-61.9-contest-standing-v1",
)


class BankruptcyContestEvidencePredicate(str, Enum):
    # Подозрительная сделка типа 1 — неравноценное встречное исполнение
    # (пункт 1 статьи 61.2): годичное окно и сам факт неравноценности.
    TRANSACTION_WITHIN_ONE_YEAR_BEFORE_OR_AFTER_PETITION = (
        "transaction_within_one_year_before_or_after_petition"
    )
    UNEQUAL_CONSIDERATION = "unequal_consideration"
    # Подозрительная сделка типа 2 — вред имущественным правам кредиторов
    # (пункт 2 статьи 61.2): трёхлетнее окно, вред, осведомлённость другой
    # стороны о цели причинения вреда.
    TRANSACTION_WITHIN_THREE_YEARS_BEFORE_OR_AFTER_PETITION = (
        "transaction_within_three_years_before_or_after_petition"
    )
    HARM_TO_CREDITORS_CAUSED = "harm_to_creditors_caused"
    COUNTERPARTY_KNEW_OF_HARMFUL_PURPOSE = "counterparty_knew_of_harmful_purpose"
    # Сделка с предпочтением (статья 61.3): окна в один месяц/после подачи
    # заявления и в шесть месяцев, основание предпочтения (общее и узкое —
    # абзацы второй и третий пункта 1) и осведомлённость о неплатёжеспособности.
    TRANSACTION_WITHIN_SIX_MONTHS_BEFORE_PETITION = (
        "transaction_within_six_months_before_petition"
    )
    TRANSACTION_AFTER_PETITION_OR_WITHIN_ONE_MONTH_BEFORE = (
        "transaction_after_petition_or_within_one_month_before"
    )
    PREFERENCE_GROUND_PRESENT = "preference_ground_present"
    PREFERENCE_NARROW_GROUND_PRESENT = "preference_narrow_ground_present"
    COUNTERPARTY_KNEW_OF_INSOLVENCY_SIGNS = "counterparty_knew_of_insolvency_signs"
    # Право на подачу заявления (статья 61.9).
    APPLICANT_IS_ADMINISTRATOR = "applicant_is_administrator"
    APPLICANT_CREDITOR_SHARE_PERCENT_EXCEEDS_TEN = (
        "applicant_creditor_share_percent_exceeds_ten"
    )


REQUIRED_BANKRUPTCY_CONTEST_PREDICATES = frozenset(BankruptcyContestEvidencePredicate)


class BankruptcyContestEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: BankruptcyContestEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedBankruptcyContestEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = BANKRUPTCY_CONTEST_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[BankruptcyContestEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedBankruptcyContestEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Bankruptcy-contest evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Bankruptcy-contest evidence contains duplicate legal source refs.")
        return self


class BankruptcyContestFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transaction_within_one_year_before_or_after_petition: bool
    unequal_consideration: bool
    transaction_within_three_years_before_or_after_petition: bool
    harm_to_creditors_caused: bool
    counterparty_knew_of_harmful_purpose: bool
    transaction_within_six_months_before_petition: bool
    transaction_after_petition_or_within_one_month_before: bool
    preference_ground_present: bool
    preference_narrow_ground_present: bool
    counterparty_knew_of_insolvency_signs: bool
    applicant_is_administrator: bool
    applicant_creditor_share_percent_exceeds_ten: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "BankruptcyContestFactSet":
        if (
            self.transaction_within_one_year_before_or_after_petition
            and not self.transaction_within_three_years_before_or_after_petition
        ):
            raise ValueError(
                "Сделка в пределах одного года до или после принятия заявления "
                "всегда лежит и в пределах трёх лет — окно пункта 2 статьи 61.2 "
                "шире окна пункта 1."
            )
        if self.preference_narrow_ground_present and not self.preference_ground_present:
            raise ValueError(
                "Узкое основание предпочтения (абзацы второй и третий пункта 1 "
                "статьи 61.3) — частный случай общего основания пункта 1: если "
                "узкое присутствует, общее тоже должно быть отмечено."
            )
        return self


class BankruptcyContestFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class BankruptcyContestEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: BankruptcyContestFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[BankruptcyContestFactProvenance] = Field(default_factory=list)


class BankruptcyContestConstraintSet(BaseModel):
    id: str
    model_version: str = BANKRUPTCY_CONTEST_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class BankruptcyContestEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    voidable_as_unequal_consideration: bool
    voidable_as_harm_to_creditors: bool
    transaction_voidable_as_suspicious: bool
    voidable_as_preference_short_window: bool
    voidable_as_preference_six_month_window: bool
    transaction_voidable_as_preference: bool
    transaction_voidable: bool
    standing_to_file: bool
    requires_human_bankruptcy_contest_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_bankruptcy_contest_evidence(
    evidence: ReviewedBankruptcyContestEvidence,
) -> BankruptcyContestEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Bankruptcy-contest evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Bankruptcy-contest evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value
        for predicate in REQUIRED_BANKRUPTCY_CONTEST_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed bankruptcy-contest evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_BANKRUPTCY_CONTEST_PREDICATES
    }
    return BankruptcyContestEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=BANKRUPTCY_CONTEST_MAPPING_VERSION,
        facts=BankruptcyContestFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            BankruptcyContestFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_BANKRUPTCY_CONTEST_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_bankruptcy_contest_constraint_set(
    mapping: BankruptcyContestEvidenceMappingResult,
) -> BankruptcyContestConstraintSet:
    return BankruptcyContestConstraintSet(
        id=f"bankruptcy-contest-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            (
                "voidable_as_unequal_consideration == "
                "transaction_within_one_year_before_or_after_petition AND unequal_consideration"
            ),
            (
                "voidable_as_harm_to_creditors == "
                "transaction_within_three_years_before_or_after_petition AND "
                "harm_to_creditors_caused AND counterparty_knew_of_harmful_purpose"
            ),
            (
                "transaction_voidable_as_suspicious == voidable_as_unequal_consideration OR "
                "voidable_as_harm_to_creditors"
            ),
            (
                "voidable_as_preference_short_window == "
                "transaction_after_petition_or_within_one_month_before AND "
                "preference_ground_present"
            ),
            (
                "voidable_as_preference_six_month_window == "
                "transaction_within_six_months_before_petition AND preference_ground_present "
                "AND (preference_narrow_ground_present OR counterparty_knew_of_insolvency_signs)"
            ),
            (
                "transaction_voidable_as_preference == voidable_as_preference_short_window OR "
                "voidable_as_preference_six_month_window"
            ),
            (
                "transaction_voidable == transaction_voidable_as_suspicious OR "
                "transaction_voidable_as_preference"
            ),
            (
                "standing_to_file == applicant_is_administrator OR "
                "applicant_creditor_share_percent_exceeds_ten"
            ),
            (
                "requires_human_bankruptcy_contest_assessment == "
                "voidable_as_unequal_consideration OR voidable_as_harm_to_creditors OR "
                "voidable_as_preference_six_month_window"
            ),
        ],
    )


def evaluate_bankruptcy_contest_constraints(
    constraint_set: BankruptcyContestConstraintSet,
    facts: BankruptcyContestFactSet,
) -> BankruptcyContestEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in BankruptcyContestFactSet.model_fields
    }
    voidable_as_unequal_consideration = Bool("voidable_as_unequal_consideration")
    voidable_as_harm_to_creditors = Bool("voidable_as_harm_to_creditors")
    transaction_voidable_as_suspicious = Bool("transaction_voidable_as_suspicious")
    voidable_as_preference_short_window = Bool("voidable_as_preference_short_window")
    voidable_as_preference_six_month_window = Bool("voidable_as_preference_six_month_window")
    transaction_voidable_as_preference = Bool("transaction_voidable_as_preference")
    transaction_voidable = Bool("transaction_voidable")
    standing_to_file = Bool("standing_to_file")
    requires_human_bankruptcy_contest_assessment = Bool(
        "requires_human_bankruptcy_contest_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        voidable_as_unequal_consideration
        == And(
            variables["transaction_within_one_year_before_or_after_petition"],
            variables["unequal_consideration"],
        )
    )
    solver.add(
        voidable_as_harm_to_creditors
        == And(
            variables["transaction_within_three_years_before_or_after_petition"],
            variables["harm_to_creditors_caused"],
            variables["counterparty_knew_of_harmful_purpose"],
        )
    )
    solver.add(
        transaction_voidable_as_suspicious
        == Or(voidable_as_unequal_consideration, voidable_as_harm_to_creditors)
    )
    solver.add(
        voidable_as_preference_short_window
        == And(
            variables["transaction_after_petition_or_within_one_month_before"],
            variables["preference_ground_present"],
        )
    )
    solver.add(
        voidable_as_preference_six_month_window
        == And(
            variables["transaction_within_six_months_before_petition"],
            variables["preference_ground_present"],
            Or(
                variables["preference_narrow_ground_present"],
                variables["counterparty_knew_of_insolvency_signs"],
            ),
        )
    )
    solver.add(
        transaction_voidable_as_preference
        == Or(voidable_as_preference_short_window, voidable_as_preference_six_month_window)
    )
    solver.add(
        transaction_voidable
        == Or(transaction_voidable_as_suspicious, transaction_voidable_as_preference)
    )
    solver.add(
        standing_to_file
        == Or(
            variables["applicant_is_administrator"],
            variables["applicant_creditor_share_percent_exceeds_ten"],
        )
    )
    solver.add(
        requires_human_bankruptcy_contest_assessment
        == Or(
            voidable_as_unequal_consideration,
            voidable_as_harm_to_creditors,
            voidable_as_preference_six_month_window,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return BankruptcyContestEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            voidable_as_unequal_consideration=False,
            voidable_as_harm_to_creditors=False,
            transaction_voidable_as_suspicious=False,
            voidable_as_preference_short_window=False,
            voidable_as_preference_six_month_window=False,
            transaction_voidable_as_preference=False,
            transaction_voidable=False,
            standing_to_file=False,
            requires_human_bankruptcy_contest_assessment=True,
            reasons_ru=["Набор фактов об оспаривании сделки должника противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = []
    if truth(voidable_as_unequal_consideration):
        reasons_ru.append(
            "Сделка совершена в течение года до принятия заявления о банкротстве или после "
            "и при неравноценном встречном исполнении — подозрительная сделка по пункту 1 "
            "статьи 61.2 127-ФЗ."
        )
    if truth(voidable_as_harm_to_creditors):
        reasons_ru.append(
            "Сделка совершена в течение трёх лет до принятия заявления или после, причинила "
            "вред имущественным правам кредиторов, и другая сторона знала о цели причинения "
            "вреда — подозрительная сделка по пункту 2 статьи 61.2 127-ФЗ."
        )
    if truth(voidable_as_preference_short_window):
        reasons_ru.append(
            "Сделка совершена после принятия заявления о банкротстве или в течение месяца до "
            "этого и влечёт предпочтение одному кредитору перед другими — недействительна по "
            "пунктам 1 и 2 статьи 61.3 127-ФЗ без дополнительных условий."
        )
    if truth(voidable_as_preference_six_month_window):
        reasons_ru.append(
            "Сделка совершена в течение шести месяцев до принятия заявления, влечёт "
            "предпочтение и либо обеспечивает старое обязательство или меняет очерёдность "
            "(абзацы второй и третий пункта 1 статьи 61.3), либо контрагенту было известно "
            "о признаке неплатёжеспособности — недействительна по пункту 3 статьи 61.3 127-ФЗ."
        )
    if not truth(transaction_voidable):
        reasons_ru.append(
            "Ни одно из оснований оспаривания по статьям 61.2 и 61.3 127-ФЗ не установлено — "
            "сделка не может быть признана недействительной по специальным основаниям "
            "законодательства о банкротстве (общие основания ГК РФ статья 61.1 не исключены)."
        )
    if truth(standing_to_file):
        reasons_ru.append(
            "Заявитель вправе подать заявление об оспаривании сделки: внешний или конкурсный "
            "управляющий либо конкурсный кредитор с долей более десяти процентов реестровой "
            "задолженности (статья 61.9 127-ФЗ)."
        )
    else:
        reasons_ru.append(
            "У заявителя нет права на подачу заявления об оспаривании сделки по статье 61.9 "
            "127-ФЗ."
        )
    if truth(requires_human_bankruptcy_contest_assessment):
        reasons_ru.append(
            "Вывод опирается на оценочный стандарт или опровержимую презумпцию, которые "
            "модель не разрешает: существенность отличия цены (пункт 1 статьи 61.2), "
            "презумпцию осведомлённости о цели причинения вреда (пункт 2 статьи 61.2) или "
            "презумпцию осведомлённости о неплатёжеспособности (пункт 3 статьи 61.3) — "
            "требуется проверка юристом."
        )
    return BankruptcyContestEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        voidable_as_unequal_consideration=truth(voidable_as_unequal_consideration),
        voidable_as_harm_to_creditors=truth(voidable_as_harm_to_creditors),
        transaction_voidable_as_suspicious=truth(transaction_voidable_as_suspicious),
        voidable_as_preference_short_window=truth(voidable_as_preference_short_window),
        voidable_as_preference_six_month_window=truth(voidable_as_preference_six_month_window),
        transaction_voidable_as_preference=truth(transaction_voidable_as_preference),
        transaction_voidable=truth(transaction_voidable),
        standing_to_file=truth(standing_to_file),
        requires_human_bankruptcy_contest_assessment=truth(
            requires_human_bankruptcy_contest_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель разбирает основания оспаривания по статьям 61.2 и 61.3 127-ФЗ и право на "
            "подачу заявления по статье 61.9, но не общие основания недействительности ГК РФ, "
            "к которым отсылает пункт 1 статьи 61.1 — это отдельный институт invalidity.",
            "Если сделка признана недействительной по пункту 2 статьи 61.2 или пункту 3 "
            "статьи 61.3, требование контрагента к должнику субординируется после третьей "
            "очереди (абзац пункта 4 статьи 134 127-ФЗ) — это выход в институт очерёдности "
            "(bankruptcy_ranking), а не вывод настоящей модели.",
        ],
    )
