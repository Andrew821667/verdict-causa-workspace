from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


GAMES_EVIDENCE_SCHEMA_VERSION = "contracts.games-evidence.v0"
GAMES_MAPPING_VERSION = "contracts-reviewed-games-to-facts-v0"
GAMES_MODEL_VERSION = "contracts-games-articles-1062-1063-v0"


class GamesEvidencePredicate(str, Enum):
    # Отношения из игр и пари и отказ в судебной защите (статья 1062 ГК РФ).
    GAMES_OR_BETTING_RELATION_ESTABLISHED = "games_or_betting_relation_established"
    JUDICIAL_PROTECTION_EXCLUSION_BREACHED = "judicial_protection_exclusion_breached"
    COERCION_EXCEPTION_DISREGARDED = "coercion_exception_disregarded"
    # Требования из расчётных сделок и производных финансовых инструментов
    # (статья 1062 ГК РФ).
    DERIVATIVE_TRANSACTIONS_PROTECTION_BREACHED = "derivative_transactions_protection_breached"
    # Организатор лотерей, тотализаторов и иных игр (статья 1063 ГК РФ).
    ORGANIZER_STATUS_OR_LICENCE_BREACHED = "organizer_status_or_licence_breached"
    GAME_CONTRACT_FORM_BREACHED = "game_contract_form_breached"
    GAME_PARTICIPATION_RULES_BREACHED = "game_participation_rules_breached"
    # Условия проведения игр и выплата выигрыша (статья 1063 ГК РФ).
    PRIZE_TERMS_ANNOUNCEMENT_BREACHED = "prize_terms_announcement_breached"
    PRIZE_PAYMENT_PERIOD_BREACHED = "prize_payment_period_breached"
    PAYMENT_REFUSAL_DAMAGES_NOT_APPLIED = "payment_refusal_damages_not_applied"


REQUIRED_GAMES_PREDICATES = frozenset(GamesEvidencePredicate)


class GamesEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: GamesEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedGamesEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = GAMES_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[GamesEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedGamesEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Games evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Games evidence contains duplicate legal source refs.")
        return self


class GamesFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    games_or_betting_relation_established: bool
    judicial_protection_exclusion_breached: bool
    coercion_exception_disregarded: bool
    derivative_transactions_protection_breached: bool
    organizer_status_or_licence_breached: bool
    game_contract_form_breached: bool
    game_participation_rules_breached: bool
    prize_terms_announcement_breached: bool
    prize_payment_period_breached: bool
    payment_refusal_damages_not_applied: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "GamesFactSet":
        if self.payment_refusal_damages_not_applied and not self.prize_payment_period_breached:
            raise ValueError(
                "Неприменение права участника на возмещение реального ущерба относится только к "
                "случаю, когда нарушение срока выплаты выигрыша установлено."
            )
        if (
            self.judicial_protection_exclusion_breached
            and not self.games_or_betting_relation_established
        ):
            raise ValueError(
                "Нарушение правила об отказе в судебной защите относится только к требованиям, "
                "связанным с организацией игр и пари или с участием в них."
            )
        return self


class GamesFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class GamesEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: GamesFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[GamesFactProvenance] = Field(default_factory=list)


class GamesConstraintSet(BaseModel):
    id: str
    model_version: str = GAMES_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class GamesEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    games_qualified: bool
    judicial_protection_duty_breached: bool
    coercion_exception_duty_breached: bool
    derivative_protection_duty_breached: bool
    organizer_status_duty_breached: bool
    game_contract_form_duty_breached: bool
    participation_rules_duty_breached: bool
    prize_terms_duty_breached: bool
    prize_payment_duty_breached: bool
    payment_refusal_damages_breached: bool
    requires_human_games_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_games_evidence(
    evidence: ReviewedGamesEvidence,
) -> GamesEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Games evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Games evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(predicate.value for predicate in REQUIRED_GAMES_PREDICATES - assertions.keys())
    if missing:
        raise ValueError(
            "Reviewed games evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_GAMES_PREDICATES
    }
    return GamesEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=GAMES_MAPPING_VERSION,
        facts=GamesFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            GamesFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_GAMES_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_games_constraint_set(
    mapping: GamesEvidenceMappingResult,
) -> GamesConstraintSet:
    return GamesConstraintSet(
        id=f"games-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "games_qualified == games_or_betting_relation_established",
            "judicial_protection_duty_breached == games_qualified AND judicial_protection_exclusion_breached",
            "coercion_exception_duty_breached == games_qualified AND coercion_exception_disregarded",
            "derivative_protection_duty_breached == games_qualified AND derivative_transactions_protection_breached",
            "organizer_status_duty_breached == games_qualified AND organizer_status_or_licence_breached",
            "game_contract_form_duty_breached == games_qualified AND game_contract_form_breached",
            "participation_rules_duty_breached == games_qualified AND game_participation_rules_breached",
            "prize_terms_duty_breached == games_qualified AND prize_terms_announcement_breached",
            "prize_payment_duty_breached == games_qualified AND prize_payment_period_breached",
            "payment_refusal_damages_breached == games_qualified AND prize_payment_period_breached AND payment_refusal_damages_not_applied",
            "requires_human_games_assessment == judicial_protection_duty_breached OR coercion_exception_duty_breached OR derivative_protection_duty_breached OR organizer_status_duty_breached OR game_contract_form_duty_breached OR participation_rules_duty_breached OR prize_terms_duty_breached OR prize_payment_duty_breached",
        ],
    )


def evaluate_games_constraints(
    constraint_set: GamesConstraintSet,
    facts: GamesFactSet,
) -> GamesEvaluation:
    variables = {field_name: Bool(field_name) for field_name in GamesFactSet.model_fields}
    games_qualified = Bool("games_qualified")
    judicial_protection_duty_breached = Bool("judicial_protection_duty_breached")
    coercion_exception_duty_breached = Bool("coercion_exception_duty_breached")
    derivative_protection_duty_breached = Bool("derivative_protection_duty_breached")
    organizer_status_duty_breached = Bool("organizer_status_duty_breached")
    game_contract_form_duty_breached = Bool("game_contract_form_duty_breached")
    participation_rules_duty_breached = Bool("participation_rules_duty_breached")
    prize_terms_duty_breached = Bool("prize_terms_duty_breached")
    prize_payment_duty_breached = Bool("prize_payment_duty_breached")
    payment_refusal_damages_breached = Bool("payment_refusal_damages_breached")
    requires_human_games_assessment = Bool("requires_human_games_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(games_qualified == variables["games_or_betting_relation_established"])
    solver.add(
        judicial_protection_duty_breached
        == And(games_qualified, variables["judicial_protection_exclusion_breached"])
    )
    solver.add(
        coercion_exception_duty_breached
        == And(games_qualified, variables["coercion_exception_disregarded"])
    )
    solver.add(
        derivative_protection_duty_breached
        == And(games_qualified, variables["derivative_transactions_protection_breached"])
    )
    solver.add(
        organizer_status_duty_breached
        == And(games_qualified, variables["organizer_status_or_licence_breached"])
    )
    solver.add(
        game_contract_form_duty_breached
        == And(games_qualified, variables["game_contract_form_breached"])
    )
    solver.add(
        participation_rules_duty_breached
        == And(games_qualified, variables["game_participation_rules_breached"])
    )
    solver.add(
        prize_terms_duty_breached
        == And(games_qualified, variables["prize_terms_announcement_breached"])
    )
    solver.add(
        prize_payment_duty_breached
        == And(games_qualified, variables["prize_payment_period_breached"])
    )
    solver.add(
        payment_refusal_damages_breached
        == And(
            games_qualified,
            variables["prize_payment_period_breached"],
            variables["payment_refusal_damages_not_applied"],
        )
    )
    solver.add(
        requires_human_games_assessment
        == Or(
            judicial_protection_duty_breached,
            coercion_exception_duty_breached,
            derivative_protection_duty_breached,
            organizer_status_duty_breached,
            game_contract_form_duty_breached,
            participation_rules_duty_breached,
            prize_terms_duty_breached,
            prize_payment_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return GamesEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            games_qualified=False,
            judicial_protection_duty_breached=False,
            coercion_exception_duty_breached=False,
            derivative_protection_duty_breached=False,
            organizer_status_duty_breached=False,
            game_contract_form_duty_breached=False,
            participation_rules_duty_breached=False,
            prize_terms_duty_breached=False,
            prize_payment_duty_breached=False,
            payment_refusal_damages_breached=False,
            requires_human_games_assessment=True,
            reasons_ru=["Набор фактов о проведении игр и пари противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Отношения квалифицированы как связанные с организацией игр и пари или с участием "
            "в них: требования граждан и юридических лиц из таких отношений подчиняются "
            "специальным правилам главы 58 ГК РФ (статьи 1062 и 1063 ГК РФ)."
            if truth(games_qualified)
            else "Отношения не квалифицированы как связанные с организацией игр и пари."
        ),
    ]
    if truth(judicial_protection_duty_breached):
        reasons_ru.append(
            "Требования граждан и юридических лиц, связанные с организацией игр и пари или с "
            "участием в них, не подлежат судебной защите, за исключением случаев, прямо "
            "предусмотренных законом (статья 1062 ГК РФ)."
        )
    if truth(coercion_exception_duty_breached):
        reasons_ru.append(
            "Судебной защите подлежат требования лиц, принявших участие в играх или пари под "
            "влиянием обмана, насилия, угрозы или злонамеренного соглашения их представителя с "
            "организатором игр или пари (статья 1062 ГК РФ)."
        )
    if truth(derivative_protection_duty_breached):
        reasons_ru.append(
            "Требования, связанные с участием в сделках, предусматривающих обязанность уплатить "
            "денежные суммы в зависимости от изменения цен, курсов валют, процентных ставок и "
            "иных обстоятельств, подлежат судебной защите при условиях, установленных законом, "
            "в том числе при заключении сделки на бирже или с участием лицензированного лица "
            "(статья 1062 ГК РФ)."
        )
    if truth(organizer_status_duty_breached):
        reasons_ru.append(
            "Отношения между организаторами лотерей, тотализаторов и других основанных на риске "
            "игр и участниками игр основаны на договоре, а организаторами могут выступать "
            "Российская Федерация, субъекты Российской Федерации, муниципальные образования "
            "или лица, получившие от уполномоченного государственного или муниципального "
            "органа разрешение (лицензию) (статья 1063 ГК РФ)."
        )
    if truth(game_contract_form_duty_breached):
        reasons_ru.append(
            "Договор между организатором и участником игр оформляется выдачей лотерейного "
            "билета, квитанции или иного документа, а в случаях, предусмотренных правилами "
            "организации игр, — иным способом (статья 1063 ГК РФ)."
        )
    if truth(participation_rules_duty_breached):
        reasons_ru.append(
            "Правила организации и проведения игр, включая условия участия и порядок "
            "определения размера выигрыша, должны соблюдаться организатором и доводиться до "
            "участников (статья 1063 ГК РФ)."
        )
    if truth(prize_terms_duty_breached):
        reasons_ru.append(
            "Предложение о заключении договора должно включать условия о сроке проведения игр и "
            "порядке определения выигрыша и его размера (статья 1063 ГК РФ)."
        )
    if truth(prize_payment_duty_breached):
        reasons_ru.append(
            "Организатор игр обязан выплатить выигрыш в предусмотренных условиями проведения "
            "игр размере, форме и срок, а если срок не указан — не позднее десяти дней с "
            "момента определения результатов игр (статья 1063 ГК РФ)."
        )
    if truth(payment_refusal_damages_breached):
        reasons_ru.append(
            "В случае неисполнения организатором игр обязанности выплатить выигрыш участник "
            "вправе требовать выплаты выигрыша, а также возмещения убытков, причинённых "
            "нарушением договора со стороны организатора (статья 1063 ГК РФ)."
        )
    return GamesEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        games_qualified=truth(games_qualified),
        judicial_protection_duty_breached=truth(judicial_protection_duty_breached),
        coercion_exception_duty_breached=truth(coercion_exception_duty_breached),
        derivative_protection_duty_breached=truth(derivative_protection_duty_breached),
        organizer_status_duty_breached=truth(organizer_status_duty_breached),
        game_contract_form_duty_breached=truth(game_contract_form_duty_breached),
        participation_rules_duty_breached=truth(participation_rules_duty_breached),
        prize_terms_duty_breached=truth(prize_terms_duty_breached),
        prize_payment_duty_breached=truth(prize_payment_duty_breached),
        payment_refusal_damages_breached=truth(payment_refusal_damages_breached),
        requires_human_games_assessment=truth(requires_human_games_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о проведении игр и пари и не заменяет "
            "судебную оценку.",
            "Наличие обмана, насилия или угрозы при участии в играх, характер расчётной сделки "
            "и содержание правил проведения игр оцениваются экспертом и судом "
            "(статьи 1062 и 1063 ГК РФ).",
        ],
    )
