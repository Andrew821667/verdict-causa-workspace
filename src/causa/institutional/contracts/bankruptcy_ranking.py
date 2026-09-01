from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


BANKRUPTCY_RANKING_EVIDENCE_SCHEMA_VERSION = "contracts.bankruptcy-ranking-evidence.v0"
BANKRUPTCY_RANKING_MAPPING_VERSION = "contracts-reviewed-bankruptcy-ranking-to-facts-v0"
BANKRUPTCY_RANKING_MODEL_VERSION = "contracts-bankruptcy-ranking-articles-134-135-138-127fz-v1"

# Дословный текст статей 134, 135 и 138 127-ФЗ — synthetic_sources.py,
# synthetic-ru-127fz-134-creditor-ranking-v1,
# synthetic-ru-127fz-135-first-rank-claims-v1,
# synthetic-ru-127fz-138-secured-creditor-claims-v1.
BANKRUPTCY_RANKING_LEGAL_SOURCE_REFS = (
    "synthetic-ru-127fz-134-creditor-ranking-v1",
    "synthetic-ru-127fz-135-first-rank-claims-v1",
    "synthetic-ru-127fz-138-secured-creditor-claims-v1",
)


class BankruptcyRankingEvidencePredicate(str, Enum):
    # Включено ли требование в реестр требований кредиторов по возбуждённому
    # делу о банкротстве. Предпосылка всего пункта 4 статьи 134: очерёдность
    # существует только внутри конкурсного производства и только для реестровых
    # требований. Без этого факта модель по умолчанию (все категории — «нет»)
    # относила бы любое требование к третьей очереди, включая требования по
    # делам, где банкротства нет вовсе.
    CLAIM_FILED_IN_BANKRUPTCY_REGISTER = "claim_filed_in_bankruptcy_register"
    # Первая очередь — вред жизни или здоровью, капитализация повременных
    # платежей (абзац второй пункта 4 статьи 134, статья 135).
    IS_LIFE_OR_HEALTH_HARM_CLAIM = "is_life_or_health_harm_claim"
    # Вторая очередь — выходные пособия, оплата труда, вознаграждения
    # авторам результатов интеллектуальной деятельности (абзац третий
    # пункта 4 статьи 134).
    IS_WAGE_SEVERANCE_OR_AUTHORSHIP_CLAIM = "is_wage_severance_or_authorship_claim"
    # Обеспечено залогом имущества должника — отдельный трек удовлетворения
    # из стоимости предмета залога по правилам статьи 138, а не по очередям
    # пункта 4 статьи 134.
    IS_SECURED_BY_PLEDGE = "is_secured_by_pledge"
    # Требование по сделке, признанной недействительной по пункту 2 статьи
    # 61.2 или пункту 3 статьи 61.3 — субординировано и удовлетворяется
    # после расчётов с кредиторами третьей очереди (абзац пункта 4 статьи
    # 134, следующий за перечнем очередей).
    IS_CLAIM_FROM_AVOIDED_TRANSACTION = "is_claim_from_avoided_transaction"
    # Требование владельца облигаций без срока погашения — удовлетворяется
    # после требований всех иных кредиторов (пункт 4 статьи 134).
    IS_PERPETUAL_BOND_CLAIM = "is_perpetual_bond_claim"
    # --- Текущие платежи: пункты 1.1, 2 и 2.1 статьи 134 ---
    # Требование по текущим платежам. Отдельные ворота, а не отрицание
    # реестровых: текущее требование в реестр не включается (пункт 2 статьи 5),
    # и очерёдность у него своя — пункт 2 статьи 134, а не пункт 4.
    IS_CURRENT_PAYMENT_CLAIM = "is_current_payment_claim"
    # Расходы на снижение угрозы техногенных или экологических катастроф либо
    # гибели людей на опасном объекте — вне очереди преимущественно перед
    # любыми другими текущими платежами (пункт 1.1 статьи 134).
    IS_TECHNOGENIC_RISK_MITIGATION_EXPENSE = "is_technogenic_risk_mitigation_expense"
    # Первая очередь текущих: судебные расходы по делу о банкротстве,
    # вознаграждение арбитражному управляющему и лицам, исполнявшим его
    # обязанности, оплата деятельности лиц, привлечение которых обязательно
    # (абзац второй пункта 2 статьи 134).
    IS_PROCEEDING_COST_OR_MANDATORY_ENGAGEMENT = "is_proceeding_cost_or_mandatory_engagement"
    # Вторая очередь текущих: оплата труда лиц, работающих или работавших по
    # трудовому договору после даты принятия заявления, и выходные пособия
    # (абзац третий пункта 2 статьи 134).
    IS_POST_PETITION_LABOUR_PAYMENT = "is_post_petition_labour_payment"
    # Третья очередь текущих: оплата деятельности лиц, привлечённых
    # управляющим для обеспечения исполнения обязанностей, кроме тех, чьё
    # привлечение обязательно (абзац четвёртый пункта 2 статьи 134).
    IS_DISCRETIONARY_ENGAGEMENT_PAYMENT = "is_discretionary_engagement_payment"
    # Четвёртая очередь текущих: эксплуатационные платежи — коммунальные,
    # по договорам энергоснабжения и иные аналогичные (абзац пятый пункта 2
    # статьи 134).
    IS_UTILITY_PAYMENT = "is_utility_payment"
    # Выходное пособие или компенсация руководителю, его заместителям, членам
    # коллегиального исполнительного органа, главному бухгалтеру и их
    # заместителям в части, превышающей минимум трудового законодательства.
    # Закон прямо исключает такое требование из текущих платежей и относит его
    # за третью очередь реестра (пункт 2.1 статьи 134).
    IS_EXCESS_EXECUTIVE_SEVERANCE = "is_excess_executive_severance"


REQUIRED_BANKRUPTCY_RANKING_PREDICATES = frozenset(BankruptcyRankingEvidencePredicate)


class BankruptcyRankingEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: BankruptcyRankingEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedBankruptcyRankingEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = BANKRUPTCY_RANKING_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[BankruptcyRankingEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedBankruptcyRankingEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Bankruptcy-ranking evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Bankruptcy-ranking evidence contains duplicate legal source refs.")
        return self


class BankruptcyRankingFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    claim_filed_in_bankruptcy_register: bool
    is_life_or_health_harm_claim: bool
    is_wage_severance_or_authorship_claim: bool
    is_secured_by_pledge: bool
    is_claim_from_avoided_transaction: bool
    is_perpetual_bond_claim: bool
    is_current_payment_claim: bool
    is_technogenic_risk_mitigation_expense: bool
    is_proceeding_cost_or_mandatory_engagement: bool
    is_post_petition_labour_payment: bool
    is_discretionary_engagement_payment: bool
    is_utility_payment: bool
    is_excess_executive_severance: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "BankruptcyRankingFactSet":
        flags = (
            self.is_life_or_health_harm_claim,
            self.is_wage_severance_or_authorship_claim,
            self.is_secured_by_pledge,
            self.is_claim_from_avoided_transaction,
            self.is_perpetual_bond_claim,
        )
        if sum(flags) > 1:
            raise ValueError(
                "Требование не может одновременно относиться к нескольким особым "
                "категориям пункта 4 статьи 134 и статьи 138 — категории взаимно "
                "исключают друг друга для целей очерёдности."
            )
        if any(flags) and not self.claim_filed_in_bankruptcy_register:
            raise ValueError(
                "Категория очерёдности определяется только для требования, включённого "
                "в реестр требований кредиторов по возбуждённому делу о банкротстве."
            )
        current_flags = (
            self.is_proceeding_cost_or_mandatory_engagement,
            self.is_post_petition_labour_payment,
            self.is_discretionary_engagement_payment,
            self.is_utility_payment,
        )
        if sum(current_flags) > 1:
            raise ValueError(
                "Требование по текущим платежам не может одновременно относиться к "
                "нескольким очередям пункта 2 статьи 134 — они перечислены как "
                "взаимно исключающие."
            )
        if (
            any(current_flags) or self.is_technogenic_risk_mitigation_expense
        ) and not self.is_current_payment_claim:
            raise ValueError(
                "Очерёдность пункта 2 статьи 134 определяется только для требования "
                "по текущим платежам: у реестрового требования очередь своя, по "
                "пункту 4 той же статьи."
            )
        if self.is_current_payment_claim and self.claim_filed_in_bankruptcy_register:
            raise ValueError(
                "Требование не может быть одновременно текущим и реестровым: "
                "требования по текущим платежам в реестр не включаются "
                "(пункт 2 статьи 5 127-ФЗ)."
            )
        if self.is_excess_executive_severance and self.is_current_payment_claim:
            raise ValueError(
                "Выходное пособие руководителя в части, превышающей минимум трудового "
                "законодательства, законом прямо исключено из текущих платежей "
                "(пункт 2.1 статьи 134 127-ФЗ)."
            )
        return self


class BankruptcyRankingFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class BankruptcyRankingEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: BankruptcyRankingFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[BankruptcyRankingFactProvenance] = Field(default_factory=list)


class BankruptcyRankingConstraintSet(BaseModel):
    id: str
    model_version: str = BANKRUPTCY_RANKING_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class BankruptcyRankingEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    first_tier: bool
    second_tier: bool
    third_tier: bool
    subordinated_after_third_tier: bool
    satisfied_from_pledge_proceeds: bool
    satisfied_last_after_all_other_creditors: bool
    current_payment_ahead_of_all_current: bool = False
    current_payment_first_tier: bool = False
    current_payment_second_tier: bool = False
    current_payment_third_tier: bool = False
    current_payment_fourth_tier: bool = False
    current_payment_fifth_tier: bool = False
    excess_executive_severance_after_third_tier: bool = False
    requires_human_bankruptcy_ranking_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_bankruptcy_ranking_evidence(
    evidence: ReviewedBankruptcyRankingEvidence,
) -> BankruptcyRankingEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Bankruptcy-ranking evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Bankruptcy-ranking evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_BANKRUPTCY_RANKING_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed bankruptcy-ranking evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_BANKRUPTCY_RANKING_PREDICATES
    }
    return BankruptcyRankingEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=BANKRUPTCY_RANKING_MAPPING_VERSION,
        facts=BankruptcyRankingFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            BankruptcyRankingFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_BANKRUPTCY_RANKING_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_bankruptcy_ranking_constraint_set(
    mapping: BankruptcyRankingEvidenceMappingResult,
) -> BankruptcyRankingConstraintSet:
    return BankruptcyRankingConstraintSet(
        id=f"bankruptcy-ranking-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "first_tier == is_life_or_health_harm_claim",
            "second_tier == is_wage_severance_or_authorship_claim",
            (
                "third_tier == claim_filed_in_bankruptcy_register AND "
                "NOT is_life_or_health_harm_claim AND "
                "NOT is_wage_severance_or_authorship_claim AND NOT is_secured_by_pledge AND "
                "NOT is_claim_from_avoided_transaction AND NOT is_perpetual_bond_claim"
            ),
            "subordinated_after_third_tier == is_claim_from_avoided_transaction",
            "satisfied_from_pledge_proceeds == is_secured_by_pledge",
            "satisfied_last_after_all_other_creditors == is_perpetual_bond_claim",
            (
                "current_payment_ahead_of_all_current == is_current_payment_claim AND "
                "is_technogenic_risk_mitigation_expense"
            ),
            (
                "current_payment_first_tier == is_current_payment_claim AND "
                "NOT is_technogenic_risk_mitigation_expense AND "
                "is_proceeding_cost_or_mandatory_engagement"
            ),
            (
                "current_payment_second_tier == is_current_payment_claim AND "
                "NOT is_technogenic_risk_mitigation_expense AND "
                "is_post_petition_labour_payment"
            ),
            (
                "current_payment_third_tier == is_current_payment_claim AND "
                "NOT is_technogenic_risk_mitigation_expense AND "
                "is_discretionary_engagement_payment"
            ),
            (
                "current_payment_fourth_tier == is_current_payment_claim AND "
                "NOT is_technogenic_risk_mitigation_expense AND is_utility_payment"
            ),
            (
                "current_payment_fifth_tier == is_current_payment_claim AND "
                "NOT is_technogenic_risk_mitigation_expense AND "
                "NOT is_proceeding_cost_or_mandatory_engagement AND "
                "NOT is_post_petition_labour_payment AND "
                "NOT is_discretionary_engagement_payment AND NOT is_utility_payment"
            ),
            "excess_executive_severance_after_third_tier == is_excess_executive_severance",
            (
                "requires_human_bankruptcy_ranking_assessment == is_secured_by_pledge OR "
                "is_life_or_health_harm_claim OR (is_current_payment_claim AND "
                "is_technogenic_risk_mitigation_expense)"
            ),
        ],
    )


def evaluate_bankruptcy_ranking_constraints(
    constraint_set: BankruptcyRankingConstraintSet,
    facts: BankruptcyRankingFactSet,
) -> BankruptcyRankingEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in BankruptcyRankingFactSet.model_fields
    }
    first_tier = Bool("first_tier")
    second_tier = Bool("second_tier")
    third_tier = Bool("third_tier")
    subordinated_after_third_tier = Bool("subordinated_after_third_tier")
    satisfied_from_pledge_proceeds = Bool("satisfied_from_pledge_proceeds")
    satisfied_last_after_all_other_creditors = Bool("satisfied_last_after_all_other_creditors")
    current_payment_ahead_of_all_current = Bool("current_payment_ahead_of_all_current")
    current_payment_first_tier = Bool("current_payment_first_tier")
    current_payment_second_tier = Bool("current_payment_second_tier")
    current_payment_third_tier = Bool("current_payment_third_tier")
    current_payment_fourth_tier = Bool("current_payment_fourth_tier")
    current_payment_fifth_tier = Bool("current_payment_fifth_tier")
    excess_executive_severance_after_third_tier = Bool(
        "excess_executive_severance_after_third_tier"
    )
    requires_human_bankruptcy_ranking_assessment = Bool(
        "requires_human_bankruptcy_ranking_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(first_tier == variables["is_life_or_health_harm_claim"])
    solver.add(second_tier == variables["is_wage_severance_or_authorship_claim"])
    # Третья очередь — остаточная категория, и только она нуждается в явных
    # воротах: остальные пять треков включаются положительным признаком, а тот
    # без реестра запрещён проверкой непротиворечивости фактов.
    solver.add(
        third_tier
        == And(
            variables["claim_filed_in_bankruptcy_register"],
            Not(variables["is_life_or_health_harm_claim"]),
            Not(variables["is_wage_severance_or_authorship_claim"]),
            Not(variables["is_secured_by_pledge"]),
            Not(variables["is_claim_from_avoided_transaction"]),
            Not(variables["is_perpetual_bond_claim"]),
        )
    )
    solver.add(subordinated_after_third_tier == variables["is_claim_from_avoided_transaction"])
    solver.add(satisfied_from_pledge_proceeds == variables["is_secured_by_pledge"])
    solver.add(satisfied_last_after_all_other_creditors == variables["is_perpetual_bond_claim"])

    # Текущие платежи: пункты 1.1, 2 и 2.1 статьи 134. Ворота те же по замыслу,
    # что и у реестровых очередей, но свои: очерёдность текущих платежей
    # существует только внутри самой категории текущих, и путать её с реестровой
    # нельзя — она применяется вне очереди, преимущественно перед реестром.
    current = variables["is_current_payment_claim"]
    # Расходы пункта 1.1 идут преимущественно перед любыми другими текущими,
    # поэтому они вытесняют пять очередей пункта 2, а не встают в одну из них.
    outside_the_five = And(current, Not(variables["is_technogenic_risk_mitigation_expense"]))
    solver.add(
        current_payment_ahead_of_all_current
        == And(current, variables["is_technogenic_risk_mitigation_expense"])
    )
    solver.add(
        current_payment_first_tier
        == And(outside_the_five, variables["is_proceeding_cost_or_mandatory_engagement"])
    )
    solver.add(
        current_payment_second_tier
        == And(outside_the_five, variables["is_post_petition_labour_payment"])
    )
    solver.add(
        current_payment_third_tier
        == And(outside_the_five, variables["is_discretionary_engagement_payment"])
    )
    solver.add(
        current_payment_fourth_tier == And(outside_the_five, variables["is_utility_payment"])
    )
    # Пятая очередь — «иные текущие платежи», остаточная категория пункта 2.
    # Как и третья очередь реестра, она нуждается в явных воротах: без них
    # любое требование без единого признака попадало бы в неё.
    solver.add(
        current_payment_fifth_tier
        == And(
            outside_the_five,
            Not(variables["is_proceeding_cost_or_mandatory_engagement"]),
            Not(variables["is_post_petition_labour_payment"]),
            Not(variables["is_discretionary_engagement_payment"]),
            Not(variables["is_utility_payment"]),
        )
    )
    solver.add(
        excess_executive_severance_after_third_tier == variables["is_excess_executive_severance"]
    )
    solver.add(
        requires_human_bankruptcy_ranking_assessment
        == Or(
            variables["is_secured_by_pledge"],
            variables["is_life_or_health_harm_claim"],
            And(current, variables["is_technogenic_risk_mitigation_expense"]),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return BankruptcyRankingEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            first_tier=False,
            second_tier=False,
            third_tier=False,
            subordinated_after_third_tier=False,
            satisfied_from_pledge_proceeds=False,
            satisfied_last_after_all_other_creditors=False,
            current_payment_ahead_of_all_current=False,
            current_payment_first_tier=False,
            current_payment_second_tier=False,
            current_payment_third_tier=False,
            current_payment_fourth_tier=False,
            current_payment_fifth_tier=False,
            excess_executive_severance_after_third_tier=False,
            requires_human_bankruptcy_ranking_assessment=True,
            reasons_ru=["Набор фактов об очерёдности требования кредитора противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = []
    if not truth(variables["claim_filed_in_bankruptcy_register"]) and not truth(
        variables["is_current_payment_claim"]
    ):
        # Пустой вывод без объяснения читался бы как «очередь не определена»,
        # тогда как верно другое: очерёдности здесь нет предмета.
        reasons_ru.append(
            "Требование не включено в реестр требований кредиторов по делу о банкротстве "
            "и не заявлено как текущий платёж — очерёдность удовлетворения (пункты 2 и 4 "
            "статьи 134, статьи 135 и 138 127-ФЗ) к нему не применяется."
        )
    if truth(first_tier):
        reasons_ru.append(
            "Требование удовлетворяется в первую очередь: расчёты по вреду жизни или "
            "здоровью производятся путём капитализации повременных платежей (абзац "
            "второй пункта 4 статьи 134, статья 135 127-ФЗ)."
        )
    if truth(second_tier):
        reasons_ru.append(
            "Требование удовлетворяется во вторую очередь: выходные пособия, оплата "
            "труда или вознаграждение автору результата интеллектуальной деятельности "
            "(абзац третий пункта 4 статьи 134 127-ФЗ)."
        )
    if truth(third_tier):
        reasons_ru.append(
            "Требование не относится к первой, второй очереди и к особым категориям — "
            "расчёты с ним производятся в третью очередь наравне с другими кредиторами, "
            "включая кредиторов по нетто-обязательствам (абзац четвёртый пункта 4 "
            "статьи 134 127-ФЗ)."
        )
    if truth(subordinated_after_third_tier):
        reasons_ru.append(
            "Требование возникло из сделки, признанной недействительной по пункту 2 "
            "статьи 61.2 или пункту 3 статьи 61.3 127-ФЗ, и удовлетворяется после "
            "расчётов с кредиторами третьей очереди."
        )
    if truth(satisfied_from_pledge_proceeds):
        reasons_ru.append(
            "Требование обеспечено залогом имущества должника и удовлетворяется из "
            "стоимости предмета залога по правилам статьи 138 127-ФЗ, а не по очередям "
            "пункта 4 статьи 134."
        )
    if truth(satisfied_last_after_all_other_creditors):
        reasons_ru.append(
            "Требование владельца облигаций без срока погашения удовлетворяется после "
            "требований всех иных кредиторов (абзац пункта 4 статьи 134 127-ФЗ)."
        )
    if truth(current_payment_ahead_of_all_current):
        reasons_ru.append(
            "Расходы на мероприятия по снижению угрозы техногенных или экологических "
            "катастроф либо гибели людей на опасном объекте погашаются вне очереди "
            "преимущественно перед любыми другими требованиями по текущим платежам "
            "(пункт 1.1 статьи 134 127-ФЗ)."
        )
    if truth(current_payment_first_tier):
        reasons_ru.append(
            "Текущий платёж первой очереди: судебные расходы по делу о банкротстве, "
            "вознаграждение арбитражному управляющему или оплата деятельности лиц, "
            "привлечение которых обязательно (абзац второй пункта 2 статьи 134 127-ФЗ)."
        )
    if truth(current_payment_second_tier):
        reasons_ru.append(
            "Текущий платёж второй очереди: оплата труда лиц, работающих или работавших "
            "по трудовому договору после принятия заявления, и выходные пособия "
            "(абзац третий пункта 2 статьи 134 127-ФЗ)."
        )
    if truth(current_payment_third_tier):
        reasons_ru.append(
            "Текущий платёж третьей очереди: оплата деятельности лиц, привлечённых "
            "управляющим для обеспечения исполнения его обязанностей, кроме тех, чьё "
            "привлечение обязательно (абзац четвёртый пункта 2 статьи 134 127-ФЗ)."
        )
    if truth(current_payment_fourth_tier):
        reasons_ru.append(
            "Текущий платёж четвёртой очереди: эксплуатационные платежи — коммунальные, "
            "по договорам энергоснабжения и иные аналогичные (абзац пятый пункта 2 "
            "статьи 134 127-ФЗ)."
        )
    if truth(current_payment_fifth_tier):
        reasons_ru.append(
            "Текущий платёж пятой очереди: иные текущие платежи (абзац шестой пункта 2 "
            "статьи 134 127-ФЗ). Это остаточная категория — требование не отнесено ни к "
            "одной из четырёх предшествующих."
        )
    if truth(variables["is_current_payment_claim"]):
        reasons_ru.append(
            "Очерёдность внутри одной очереди текущих платежей — календарная (абзац "
            "седьмой пункта 2 статьи 134 127-ФЗ). Даты возникновения требований модель "
            "не сравнивает: они не входят в её факты."
        )
    if truth(excess_executive_severance_after_third_tier):
        reasons_ru.append(
            "Выходное пособие или компенсация руководителю, его заместителям, членам "
            "коллегиального исполнительного органа либо главному бухгалтеру в части, "
            "превышающей минимум трудового законодательства, к текущим платежам не "
            "относится и удовлетворяется после расчётов с кредиторами третьей очереди "
            "реестра (пункт 2.1 статьи 134 127-ФЗ)."
        )
    if truth(requires_human_bankruptcy_ranking_assessment):
        reasons_ru.append(
            "Модель определяет только очередь требования, а не сумму удовлетворения: "
            "капитализация повременных платежей по статье 135 и раздел выручки от "
            "продажи предмета залога по статье 138 (семьдесят/восемьдесят процентов, "
            "с учётом наличия кредитного договора) — расчёт, который модель не "
            "производит и передаёт на проверку юристом."
        )
    return BankruptcyRankingEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        first_tier=truth(first_tier),
        second_tier=truth(second_tier),
        third_tier=truth(third_tier),
        subordinated_after_third_tier=truth(subordinated_after_third_tier),
        satisfied_from_pledge_proceeds=truth(satisfied_from_pledge_proceeds),
        satisfied_last_after_all_other_creditors=truth(satisfied_last_after_all_other_creditors),
        current_payment_ahead_of_all_current=truth(current_payment_ahead_of_all_current),
        current_payment_first_tier=truth(current_payment_first_tier),
        current_payment_second_tier=truth(current_payment_second_tier),
        current_payment_third_tier=truth(current_payment_third_tier),
        current_payment_fourth_tier=truth(current_payment_fourth_tier),
        current_payment_fifth_tier=truth(current_payment_fifth_tier),
        excess_executive_severance_after_third_tier=truth(
            excess_executive_severance_after_third_tier
        ),
        requires_human_bankruptcy_ranking_assessment=truth(
            requires_human_bankruptcy_ranking_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель разбирает очерёдность и реестровых требований (пункт 4 статьи 134, "
            "статьи 135 и 138 127-ФЗ), и требований по текущим платежам (пункты 1.1, 2 "
            "и 2.1 статьи 134). Внутри одной очереди текущих платежей закон устанавливает "
            "календарный порядок, и его модель не определяет: дат возникновения требований "
            "в её фактах нет.",
            "Отнесение требования к категории 'из недействительной сделки' модель "
            "принимает как готовый факт: сама проверка недействительности по статьям "
            "61.2 и 61.3 — задача отдельного института оспаривания сделок должника.",
        ],
    )
