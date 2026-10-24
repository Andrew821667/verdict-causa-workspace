"""Формальная модель понятия, видов и условий сделок по статьям 153–157.1 ГК РФ.

Модель разделяет понятие сделки, деление сделок на односторонние и
дву-/многосторонние, правовой эффект односторонней сделки, применение к ней
общих положений об обязательствах и договорах, сделки под отлагательным и
отменительным условием, недобросовестное воспрепятствование наступлению
условия, необходимость согласия третьего лица или органа на совершение сделки,
порядок и содержание такого согласия, а также запрет считать молчание
согласием.

Ключевой вывод для слоя общих положений — `consent_missing_for_transaction`:
сделка совершена без необходимого в силу закона согласия. По статье 173.1 ГК РФ
такая сделка является оспоримой, поэтому слой помечает её как оспоримую, но не
лишает договор действия автоматически: оспоримая сделка недействительна только
в силу признания её таковой судом (пункт 1 статьи 166 ГК РФ).

С выпуска 1.39.0 слой получает и статус условия (статья 157):
`suspensive_condition_unfulfilled` — отлагательное условие не наступило, и права
и обязанности, поставленные в зависимость от него, не возникли;
`resolutive_condition_fulfilled` — отменительное условие наступило, и они
прекратились. Статус учитывает пункт 3: условие, наступлению которого
недобросовестно воспрепятствовала сторона, признаётся наступившим, а условие,
наступлению которого недобросовестно содействовала сторона, — ненаступившим.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


TRANSACTIONS_EVIDENCE_SCHEMA_VERSION = "contracts.transactions-evidence.v0"
TRANSACTIONS_MAPPING_VERSION = "contracts-reviewed-transactions-to-facts-v0"
TRANSACTIONS_MODEL_VERSION = "contracts-transactions-articles-153-157-1-v1"


class TransactionsEvidencePredicate(str, Enum):
    # Понятие сделки (статья 153 ГК РФ).
    TRANSACTION_ASSERTED = "transaction_asserted"
    TRANSACTION_DEFINITION_BREACHED = "transaction_definition_breached"
    # Договоры и односторонние сделки (статьи 154–156 ГК РФ).
    PARTIES_COUNT_RULES_BREACHED = "parties_count_rules_breached"
    UNILATERAL_TRANSACTION_EFFECT_BREACHED = "unilateral_transaction_effect_breached"
    UNILATERAL_REGULATION_BREACHED = "unilateral_regulation_breached"
    # Сделки, совершённые под условием (статья 157 ГК РФ): какое условие, наступило
    # ли оно и не повлияла ли на это сторона недобросовестно.
    CONDITIONAL_TRANSACTION_RULES_BREACHED = "conditional_transaction_rules_breached"
    SUSPENSIVE_CONDITION_SET = "suspensive_condition_set"
    RESOLUTIVE_CONDITION_SET = "resolutive_condition_set"
    CONDITION_OCCURRED = "condition_occurred"
    CONDITION_OBSTRUCTED_IN_BAD_FAITH = "condition_obstructed_in_bad_faith"
    CONDITION_PROMOTED_IN_BAD_FAITH = "condition_promoted_in_bad_faith"
    # Согласие на совершение сделки (статья 157.1 ГК РФ).
    STATUTORY_CONSENT_NOT_OBTAINED = "statutory_consent_not_obtained"
    CONSENT_PROCEDURE_BREACHED = "consent_procedure_breached"
    SILENCE_TREATED_AS_CONSENT = "silence_treated_as_consent"


REQUIRED_TRANSACTIONS_PREDICATES = frozenset(TransactionsEvidencePredicate)


class TransactionsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: TransactionsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedTransactionsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = TRANSACTIONS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[TransactionsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedTransactionsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Transactions evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Transactions evidence contains duplicate legal source refs.")
        return self


class TransactionsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    transaction_asserted: bool
    transaction_definition_breached: bool
    parties_count_rules_breached: bool
    unilateral_transaction_effect_breached: bool
    unilateral_regulation_breached: bool
    conditional_transaction_rules_breached: bool
    suspensive_condition_set: bool
    resolutive_condition_set: bool
    condition_occurred: bool
    condition_obstructed_in_bad_faith: bool
    condition_promoted_in_bad_faith: bool
    statutory_consent_not_obtained: bool
    consent_procedure_breached: bool
    silence_treated_as_consent: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "TransactionsFactSet":
        if self.silence_treated_as_consent and not self.statutory_consent_not_obtained:
            raise ValueError(
                "Признание молчания согласием относится только к случаю, когда необходимое "
                "в силу закона согласие на совершение сделки не получено."
            )
        if self.transaction_definition_breached and not self.transaction_asserted:
            raise ValueError(
                "Нарушение понятия сделки относится только к заявленному действию, "
                "квалифицируемому как сделка."
            )
        condition_set = self.suspensive_condition_set or self.resolutive_condition_set
        if condition_set and not self.transaction_asserted:
            raise ValueError("Условие относится только к заявленной сделке.")
        if self.suspensive_condition_set and self.resolutive_condition_set:
            raise ValueError(
                "Модель разбирает одно условие: права и обязанности, о которых спор, "
                "поставлены в зависимость либо от отлагательного, либо от отменительного "
                "условия."
            )
        if (
            self.condition_occurred
            or self.condition_obstructed_in_bad_faith
            or self.condition_promoted_in_bad_faith
        ) and not condition_set:
            raise ValueError(
                "Наступление условия и влияние на него относятся только к сделке, "
                "совершённой под условием; условие не установлено."
            )
        if self.condition_obstructed_in_bad_faith and self.condition_promoted_in_bad_faith:
            raise ValueError(
                "Условие не может быть одновременно признано наступившим и ненаступившим "
                "(пункт 3 статьи 157 ГК РФ): рецензент называет решающее воздействие."
            )
        return self


class TransactionsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class TransactionsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: TransactionsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[TransactionsFactProvenance] = Field(default_factory=list)


class TransactionsConstraintSet(BaseModel):
    id: str
    model_version: str = TRANSACTIONS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class TransactionsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    transactions_qualified: bool
    transaction_definition_duty_breached: bool
    parties_count_duty_breached: bool
    unilateral_transaction_duty_breached: bool
    unilateral_regulation_duty_breached: bool
    conditional_transaction_duty_breached: bool
    condition_interference_duty_breached: bool
    # Статус условия (статья 157): наступило ли оно или признаётся наступившим.
    # Два последних вывода — входы слоя общих положений с выпуска 1.39.0.
    condition_fulfilled: bool
    suspensive_condition_unfulfilled: bool
    resolutive_condition_fulfilled: bool
    # Ключевой вывод для слоя общих положений: сделка совершена без необходимого
    # в силу закона согласия, поэтому она оспорима (статья 173.1 ГК РФ).
    consent_missing_for_transaction: bool
    consent_procedure_duty_breached: bool
    silence_as_consent_breached: bool
    requires_human_transactions_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_transactions_evidence(
    evidence: ReviewedTransactionsEvidence,
) -> TransactionsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Transactions evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Transactions evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_TRANSACTIONS_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed transactions evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_TRANSACTIONS_PREDICATES
    }
    return TransactionsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=TRANSACTIONS_MAPPING_VERSION,
        facts=TransactionsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            TransactionsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_TRANSACTIONS_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_transactions_constraint_set(
    mapping: TransactionsEvidenceMappingResult,
) -> TransactionsConstraintSet:
    return TransactionsConstraintSet(
        id=f"transactions-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "transactions_qualified == transaction_asserted",
            "transaction_definition_duty_breached == transactions_qualified AND transaction_definition_breached",
            "parties_count_duty_breached == transactions_qualified AND parties_count_rules_breached",
            "unilateral_transaction_duty_breached == transactions_qualified AND unilateral_transaction_effect_breached",
            "unilateral_regulation_duty_breached == transactions_qualified AND unilateral_regulation_breached",
            "conditional_transaction_duty_breached == transactions_qualified AND conditional_transaction_rules_breached",
            "condition_interference_duty_breached == transactions_qualified AND (condition_obstructed_in_bad_faith OR condition_promoted_in_bad_faith)",
            "condition_fulfilled == transactions_qualified AND (suspensive_condition_set OR resolutive_condition_set) AND ((condition_occurred AND NOT condition_promoted_in_bad_faith) OR condition_obstructed_in_bad_faith)",
            "suspensive_condition_unfulfilled == transactions_qualified AND suspensive_condition_set AND NOT condition_fulfilled",
            "resolutive_condition_fulfilled == resolutive_condition_set AND condition_fulfilled",
            "consent_missing_for_transaction == transactions_qualified AND statutory_consent_not_obtained",
            "consent_procedure_duty_breached == transactions_qualified AND consent_procedure_breached",
            "silence_as_consent_breached == transactions_qualified AND statutory_consent_not_obtained AND silence_treated_as_consent",
            "requires_human_transactions_assessment == transaction_definition_duty_breached OR parties_count_duty_breached OR unilateral_transaction_duty_breached OR unilateral_regulation_duty_breached OR conditional_transaction_duty_breached OR condition_interference_duty_breached OR consent_missing_for_transaction OR consent_procedure_duty_breached",
        ],
    )


def evaluate_transactions_constraints(
    constraint_set: TransactionsConstraintSet,
    facts: TransactionsFactSet,
) -> TransactionsEvaluation:
    variables = {field_name: Bool(field_name) for field_name in TransactionsFactSet.model_fields}
    transactions_qualified = Bool("transactions_qualified")
    transaction_definition_duty_breached = Bool("transaction_definition_duty_breached")
    parties_count_duty_breached = Bool("parties_count_duty_breached")
    unilateral_transaction_duty_breached = Bool("unilateral_transaction_duty_breached")
    unilateral_regulation_duty_breached = Bool("unilateral_regulation_duty_breached")
    conditional_transaction_duty_breached = Bool("conditional_transaction_duty_breached")
    condition_interference_duty_breached = Bool("condition_interference_duty_breached")
    condition_fulfilled = Bool("condition_fulfilled")
    suspensive_condition_unfulfilled = Bool("suspensive_condition_unfulfilled")
    resolutive_condition_fulfilled = Bool("resolutive_condition_fulfilled")
    consent_missing_for_transaction = Bool("consent_missing_for_transaction")
    consent_procedure_duty_breached = Bool("consent_procedure_duty_breached")
    silence_as_consent_breached = Bool("silence_as_consent_breached")
    requires_human_transactions_assessment = Bool("requires_human_transactions_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(transactions_qualified == variables["transaction_asserted"])
    solver.add(
        transaction_definition_duty_breached
        == And(transactions_qualified, variables["transaction_definition_breached"])
    )
    solver.add(
        parties_count_duty_breached
        == And(transactions_qualified, variables["parties_count_rules_breached"])
    )
    solver.add(
        unilateral_transaction_duty_breached
        == And(transactions_qualified, variables["unilateral_transaction_effect_breached"])
    )
    solver.add(
        unilateral_regulation_duty_breached
        == And(transactions_qualified, variables["unilateral_regulation_breached"])
    )
    solver.add(
        conditional_transaction_duty_breached
        == And(transactions_qualified, variables["conditional_transaction_rules_breached"])
    )
    solver.add(
        condition_interference_duty_breached
        == And(
            transactions_qualified,
            Or(
                variables["condition_obstructed_in_bad_faith"],
                variables["condition_promoted_in_bad_faith"],
            ),
        )
    )
    # Пункт 3 статьи 157: условие, наступлению которого недобросовестно
    # воспрепятствовали, признаётся наступившим, а условие, наступлению которого
    # недобросовестно содействовали, — ненаступившим.
    solver.add(
        condition_fulfilled
        == And(
            transactions_qualified,
            Or(variables["suspensive_condition_set"], variables["resolutive_condition_set"]),
            Or(
                And(
                    variables["condition_occurred"],
                    Not(variables["condition_promoted_in_bad_faith"]),
                ),
                variables["condition_obstructed_in_bad_faith"],
            ),
        )
    )
    solver.add(
        suspensive_condition_unfulfilled
        == And(
            transactions_qualified,
            variables["suspensive_condition_set"],
            Not(condition_fulfilled),
        )
    )
    solver.add(
        resolutive_condition_fulfilled
        == And(variables["resolutive_condition_set"], condition_fulfilled)
    )
    solver.add(
        consent_missing_for_transaction
        == And(transactions_qualified, variables["statutory_consent_not_obtained"])
    )
    solver.add(
        consent_procedure_duty_breached
        == And(transactions_qualified, variables["consent_procedure_breached"])
    )
    solver.add(
        silence_as_consent_breached
        == And(
            transactions_qualified,
            variables["statutory_consent_not_obtained"],
            variables["silence_treated_as_consent"],
        )
    )
    solver.add(
        requires_human_transactions_assessment
        == Or(
            transaction_definition_duty_breached,
            parties_count_duty_breached,
            unilateral_transaction_duty_breached,
            unilateral_regulation_duty_breached,
            conditional_transaction_duty_breached,
            condition_interference_duty_breached,
            consent_missing_for_transaction,
            consent_procedure_duty_breached,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return TransactionsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            transactions_qualified=False,
            transaction_definition_duty_breached=False,
            parties_count_duty_breached=False,
            unilateral_transaction_duty_breached=False,
            unilateral_regulation_duty_breached=False,
            conditional_transaction_duty_breached=False,
            condition_interference_duty_breached=False,
            condition_fulfilled=False,
            suspensive_condition_unfulfilled=False,
            resolutive_condition_fulfilled=False,
            consent_missing_for_transaction=False,
            consent_procedure_duty_breached=False,
            silence_as_consent_breached=False,
            requires_human_transactions_assessment=True,
            reasons_ru=["Набор фактов о сделке противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Заявлена сделка: действия граждан и юридических лиц, направленные на "
            "установление, изменение или прекращение гражданских прав и обязанностей, "
            "признаются сделками (статья 153 ГК РФ)."
            if truth(transactions_qualified)
            else "Совершение сделки не заявлено."
        ),
    ]
    if truth(transaction_definition_duty_breached):
        reasons_ru.append(
            "Действие не отвечает понятию сделки: сделками признаются действия граждан и "
            "юридических лиц, направленные на установление, изменение или прекращение "
            "гражданских прав и обязанностей (статья 153 ГК РФ)."
        )
    if truth(parties_count_duty_breached):
        reasons_ru.append(
            "Нарушены правила о видах сделок: сделки могут быть двух- или многосторонними "
            "(договоры) и односторонними; для заключения договора необходимо выражение "
            "согласованной воли двух сторон либо трёх и более сторон (статья 154 ГК РФ)."
        )
    if truth(unilateral_transaction_duty_breached):
        reasons_ru.append(
            "Односторонняя сделка создаёт обязанности для лиц, которые её не совершали: "
            "односторонняя сделка создаёт обязанности для лица, её совершившего, и может "
            "создавать обязанности для других лиц лишь в случаях, установленных законом либо "
            "соглашением с этими лицами (статья 155 ГК РФ)."
        )
    if truth(unilateral_regulation_duty_breached):
        reasons_ru.append(
            "К односторонней сделке не применены общие положения об обязательствах и о "
            "договорах, применимые постольку, поскольку это не противоречит закону, "
            "одностороннему характеру и существу сделки (статья 156 ГК РФ)."
        )
    if truth(conditional_transaction_duty_breached):
        reasons_ru.append(
            "Нарушены правила о сделках под условием: сделка считается совершённой под "
            "отлагательным или отменительным условием, если стороны поставили возникновение "
            "либо прекращение прав и обязанностей в зависимость от обстоятельства, "
            "относительно которого неизвестно, наступит оно или не наступит "
            "(статья 157 ГК РФ)."
        )
    if truth(condition_interference_duty_breached):
        reasons_ru.append(
            "Наступлению условия недобросовестно воспрепятствовала сторона, которой оно "
            "невыгодно, поэтому условие признаётся наступившим (пункт 3 статьи 157 ГК РФ)."
            if truth(variables["condition_obstructed_in_bad_faith"])
            else "Наступлению условия недобросовестно содействовала сторона, которой оно "
            "выгодно, поэтому условие признаётся ненаступившим (пункт 3 статьи 157 ГК РФ)."
        )
    if truth(suspensive_condition_unfulfilled):
        reasons_ru.append(
            "Сделка совершена под отлагательным условием, и оно не наступило: права и "
            "обязанности, поставленные в зависимость от него, не возникли "
            "(пункт 1 статьи 157 ГК РФ)."
        )
    elif truth(condition_fulfilled) and truth(variables["suspensive_condition_set"]):
        reasons_ru.append(
            "Отлагательное условие наступило: права и обязанности, поставленные в "
            "зависимость от него, возникли (пункт 1 статьи 157 ГК РФ)."
        )
    if truth(resolutive_condition_fulfilled):
        reasons_ru.append(
            "Сделка совершена под отменительным условием, и оно наступило: права и "
            "обязанности, поставленные в зависимость от него, прекратились "
            "(пункт 2 статьи 157 ГК РФ)."
        )
    elif truth(transactions_qualified) and truth(variables["resolutive_condition_set"]):
        reasons_ru.append(
            "Отменительное условие не наступило: права и обязанности, поставленные в "
            "зависимость от него, сохраняются (пункт 2 статьи 157 ГК РФ)."
        )
    if truth(consent_missing_for_transaction):
        reasons_ru.append(
            "Сделка совершена без необходимого в силу закона согласия третьего лица, органа "
            "юридического лица или государственного органа либо органа местного "
            "самоуправления (статья 157.1 ГК РФ); такая сделка является оспоримой и может "
            "быть признана недействительной судом (статья 173.1 ГК РФ)."
        )
    if truth(consent_procedure_duty_breached):
        reasons_ru.append(
            "Нарушены порядок и содержание согласия на совершение сделки: в предварительном "
            "согласии должен быть определён предмет сделки, а при последующем согласии "
            "(одобрении) должна быть указана сделка, на совершение которой дано согласие "
            "(статья 157.1 ГК РФ)."
        )
    if truth(silence_as_consent_breached):
        reasons_ru.append(
            "Молчание признано согласием на совершение сделки, тогда как молчание не считается "
            "согласием на совершение сделки, за исключением случаев, установленных законом "
            "(статья 157.1 ГК РФ)."
        )
    return TransactionsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        transactions_qualified=truth(transactions_qualified),
        transaction_definition_duty_breached=truth(transaction_definition_duty_breached),
        parties_count_duty_breached=truth(parties_count_duty_breached),
        unilateral_transaction_duty_breached=truth(unilateral_transaction_duty_breached),
        unilateral_regulation_duty_breached=truth(unilateral_regulation_duty_breached),
        conditional_transaction_duty_breached=truth(conditional_transaction_duty_breached),
        condition_interference_duty_breached=truth(condition_interference_duty_breached),
        condition_fulfilled=truth(condition_fulfilled),
        suspensive_condition_unfulfilled=truth(suspensive_condition_unfulfilled),
        resolutive_condition_fulfilled=truth(resolutive_condition_fulfilled),
        consent_missing_for_transaction=truth(consent_missing_for_transaction),
        consent_procedure_duty_breached=truth(consent_procedure_duty_breached),
        silence_as_consent_breached=truth(silence_as_consent_breached),
        requires_human_transactions_assessment=truth(requires_human_transactions_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о понятии, видах и условиях сделок и "
            "не заменяет судебную оценку.",
            "Направленность воли сторон, наступление или ненаступление условия и "
            "добросовестность влияния на него оцениваются экспертом и судом "
            "(статьи 153 и 157 ГК РФ).",
        ],
    )
