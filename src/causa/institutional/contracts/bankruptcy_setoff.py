"""Формальная модель зачёта и сальдирования в деле о банкротстве.

Абзац шестой пункта 1 статьи 63 закона 127-ФЗ с даты введения наблюдения
запрещает зачёт встречного однородного требования, если он нарушает очерёдность
пункта 4 статьи 134, и сам называет исключение — нетто-обязательства по
финансовым договорам статьи 4.1.

## Сальдо — не зачёт

До выпуска 1.30.0 модель принимала квалификацию операции как зачёта готовым
фактом и поднимала флаг юриста на каждом зачёте, нарушающем очерёдность: зачёт
двух независимых требований (статья 410 ГК РФ) и определение сальдо по одному
договору она не различала. Это был открытый вопрос, на котором расходятся суды.

Теперь модель применяет критерий Верховного Суда — пункт 17 Обзора судебной
практики по делам о банкротстве за 2022 год: сопоставление обязанностей сторон
из одного договора (либо нескольких взаимосвязанных договоров) и расчёт с
целью определить лицо, на которое возлагается завершающее исполнение, **не
могут быть квалифицированы как зачёт** и не оспариваются как сделка с
предпочтением по статье 61.3: встречные требования в такой ситуации фактически
не возникают. Пункт 16 того же обзора применяет это к подряду, пункт 4 Обзора
за 2023 год — к неустойке, учтённой при сальдировании.

Из критерия следуют два признака рецензента — откуда встречные обязанности (один
договор или взаимосвязанные) и что делает операция (определяет завершающую
обязанность). Сальдо выводит модель. Название, которое дала операции сторона,
вывода не меняет: в деле пункта 4 Обзора за 2023 год заказчик направил
«уведомление о зачёте», а Верховный Суд разобрал его как сальдирование.

## Что остаётся юристу

* **Отказ в сальдо там, где зачёт нарушил бы очерёдность.** Пункт 16 Обзора за
  2022 год требует сначала определить условия сделки, истолковав документы по
  статье 431 ГК РФ, а не по их названию. От этого толкования зависит, запрещён
  ли зачёт, — флаг остаётся.
* **Сальдо по нескольким взаимосвязанным договорам.** «Взаимосвязанность» —
  оценочное понятие; сальдо по одному договору флага не поднимает.
* **Явно несоразмерная неустойка в сальдо.** Само по себе её применение не
  делает сальдирование сделкой с предпочтением; права подрядчика и его
  кредиторов защищает статья 333 ГК РФ, а не недействительность сальдирования.
  Несоразмерность и уменьшение оценивает суд.

Взыскание встречных требований судом сальдированию не препятствует (пункт 17
Обзора за 2022 год); модель называет этот признак, чтобы отбросить, и тест
проверяет, что он ничего не меняет.

## Чего модель не делает

* **Не проверяет условия статьи 4.1** — генеральное соглашение, правила
  организованных торгов и клиринга, закрытый перечень лиц; это отдельный
  институт, а признак остаётся фактом рецензента.
* **Не считает сальдо** и не проверяет суммы: несогласие с ними само по себе не
  порочит сальдирование и разрешается при установлении требований (пункт 4
  Обзора за 2023 год).
* **Не разбирает очерёдность погашения внутри сальдо** по статье 319 ГК РФ —
  Верховный Суд отнёс этот довод к спору о включении требований в реестр.
* **Не связан с институтом оспаривания сделок** (статьи 61.2 и 61.3): тот
  описывает одну оспариваемую сделку, этот — одну операцию прекращения, и это
  не обязательно одна и та же операция.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


BANKRUPTCY_SETOFF_EVIDENCE_SCHEMA_VERSION = "contracts.bankruptcy-setoff-evidence.v0"
BANKRUPTCY_SETOFF_MAPPING_VERSION = "contracts-reviewed-bankruptcy-setoff-to-facts-v0"
BANKRUPTCY_SETOFF_MODEL_VERSION = "contracts-bankruptcy-setoff-articles-63-134-127fz-saldo-v1"

# Дословный текст статей 63, 134 и 4.1 127-ФЗ — synthetic_sources.py,
# synthetic-ru-127fz-63-observation-effects-v1,
# synthetic-ru-127fz-134-creditor-ranking-v1,
# synthetic-ru-127fz-4.1-financial-contract-netting-v1.
#
# Статья 4.1 добавлена отдельно от двух первых: абзац шестой пункта 1 статьи 63
# называет исключение для нетто-обязательств по финансовым договорам отсылкой, а
# текста той статьи в пакете не было. Модель ссылалась в пустоту — ровно тот
# дефект, который закрыт для остальных двухсот шестнадцати дословных источников.
#
# С выпуска 1.30.0 к ним добавлены критерий сальдо — пункты 16 и 17 Обзора ВС РФ
# по банкротству за 2022 год и пункт 4 Обзора за 2023 год, дословно, — и нормы,
# которые эти пункты называют: статья 410 ГК РФ (зачёт), статья 333 ГК РФ
# (уменьшение неустойки) и статья 61.3 127-ФЗ (сделка с предпочтением).
BANKRUPTCY_SETOFF_LEGAL_SOURCE_REFS = (
    "synthetic-ru-127fz-63-observation-effects-v1",
    "synthetic-ru-127fz-134-creditor-ranking-v1",
    "synthetic-ru-127fz-4.1-financial-contract-netting-v1",
    "synthetic-ru-127fz-61.3-contest-preference-transaction-v1",
    "synthetic-ru-gk407-413-discharge-v1",
    "synthetic-ru-gk333-penalty-model-v1",
    "synthetic-ru-vs-review-bankruptcy-2022-16-contract-work-saldo-v1",
    "synthetic-ru-vs-review-bankruptcy-2022-17-heat-transfer-saldo-v1",
    "synthetic-ru-vs-review-bankruptcy-2023-4-penalty-in-saldo-v1",
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
    # пункта 1 статьи 63.
    #
    # Текст статьи 4.1 теперь в пакете есть, и ссылка больше не уходит в
    # пустоту. Проверять её условия модель всё равно не берётся: статья
    # описывает режим генерального соглашения, правил организованных торгов и
    # клиринга и закрытый перечень лиц — это отдельный институт, а не признак.
    # Поэтому квалификация остаётся проверенным фактом рецензента.
    ARISES_FROM_FINANCIAL_CONTRACT_NETTING_UNDER_ARTICLE_4_1 = (
        "arises_from_financial_contract_netting_under_article_4_1"
    )

    # --- Сальдо: пункт 17 Обзора ВС РФ по банкротству за 2022 год ---
    # Встречные обязанности сторон возникли из одного договора.
    COUNTER_OBLIGATIONS_ARISE_FROM_ONE_CONTRACT = "counter_obligations_arise_from_one_contract"
    # Встречные обязанности возникли из нескольких взаимосвязанных договоров.
    COUNTER_OBLIGATIONS_ARISE_FROM_LINKED_CONTRACTS = (
        "counter_obligations_arise_from_linked_contracts"
    )
    # Операция сопоставляет обязанности сторон и расчётом определяет лицо, на
    # которое возлагается завершающее исполнение, и его сумму, — а не прекращает
    # два самостоятельных требования.
    OPERATION_DETERMINES_FINAL_OBLIGATION_BY_COMPARING_PERFORMANCES = (
        "operation_determines_final_obligation_by_comparing_performances"
    )
    # Встречные требования до сальдирования взысканы вступившими в силу
    # судебными актами (пункт 17 Обзора за 2022 год: сальдо это не мешает).
    COUNTER_CLAIMS_ALREADY_AWARDED_BY_COURT = "counter_claims_already_awarded_by_court"

    # --- Неустойка в сальдо: пункт 4 Обзора ВС РФ по банкротству за 2023 год ---
    PENALTY_COUNTED_IN_SALDO = "penalty_counted_in_saldo"
    # Сумма неустойки явно несоразмерна последствиям нарушения основного
    # обязательства.
    PENALTY_CLEARLY_DISPROPORTIONATE_TO_BREACH = "penalty_clearly_disproportionate_to_breach"


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
    counter_obligations_arise_from_one_contract: bool
    counter_obligations_arise_from_linked_contracts: bool
    operation_determines_final_obligation_by_comparing_performances: bool
    counter_claims_already_awarded_by_court: bool
    penalty_counted_in_saldo: bool
    penalty_clearly_disproportionate_to_breach: bool

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
        if (
            self.counter_obligations_arise_from_one_contract
            and self.counter_obligations_arise_from_linked_contracts
        ):
            raise ValueError(
                "Встречные обязанности возникли либо из одного договора, либо из нескольких "
                "взаимосвязанных: одно и то же отношение не описывается обоими способами."
            )
        if self.operation_determines_final_obligation_by_comparing_performances and not (
            self.counter_obligations_arise_from_one_contract
            or self.counter_obligations_arise_from_linked_contracts
        ):
            raise ValueError(
                "Определить завершающую обязанность можно, сопоставив обязанности сторон из "
                "одного договора либо нескольких взаимосвязанных (пункт 17 Обзора ВС РФ по "
                "банкротству за 2022 год); прекращение требований из независимых договоров — "
                "это зачёт."
            )
        if (
            self.operation_determines_final_obligation_by_comparing_performances
            and self.arises_from_financial_contract_netting_under_article_4_1
        ):
            raise ValueError(
                "Сальдо по договору и нетто-обязательство по финансовым договорам статьи 4.1 — "
                "разные механизмы: одна операция не может быть одновременно и тем, и другим."
            )
        if (
            self.counter_claims_already_awarded_by_court or self.penalty_counted_in_saldo
        ) and not self.operation_determines_final_obligation_by_comparing_performances:
            raise ValueError(
                "Взыскание встречных требований судом и неустойка в сальдо описывают "
                "сальдирование, а операция завершающую обязанность не определяет."
            )
        if self.penalty_clearly_disproportionate_to_breach and not self.penalty_counted_in_saldo:
            raise ValueError(
                "Несоразмерность неустойки названа, а неустойка при сальдировании не учтена."
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
    #: Операция — определение сальдо по одному договору (или взаимосвязанным), а
    #: не зачёт: запрет статьи 63 и оспаривание по статье 61.3 к ней не относятся.
    operation_is_saldo_not_setoff: bool
    #: Взыскание встречных требований судом названо и сальдо не препятствует.
    prior_judgments_do_not_bar_saldo: bool
    #: Явно несоразмерная неустойка в сальдо: защита — статья 333 ГК РФ, а не
    #: недействительность сальдирования.
    penalty_disproportion_remedied_by_article_333: bool
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
                "operation_is_saldo_not_setoff == "
                "(counter_obligations_arise_from_one_contract OR "
                "counter_obligations_arise_from_linked_contracts) AND "
                "operation_determines_final_obligation_by_comparing_performances"
            ),
            (
                "setoff_prohibited == observation_introduced AND "
                "setoff_of_mutual_homogeneous_claims_asserted AND "
                "setoff_would_violate_priority_order AND "
                "NOT arises_from_financial_contract_netting_under_article_4_1 AND "
                "NOT operation_is_saldo_not_setoff"
            ),
            (
                "setoff_permitted_as_priority_neutral == observation_introduced AND "
                "setoff_of_mutual_homogeneous_claims_asserted AND "
                "NOT setoff_would_violate_priority_order AND "
                "NOT operation_is_saldo_not_setoff"
            ),
            (
                "netting_permitted_by_financial_contract_exception == "
                "arises_from_financial_contract_netting_under_article_4_1"
            ),
            (
                "prior_judgments_do_not_bar_saldo == operation_is_saldo_not_setoff AND "
                "counter_claims_already_awarded_by_court"
            ),
            (
                "penalty_disproportion_remedied_by_article_333 == "
                "operation_is_saldo_not_setoff AND penalty_counted_in_saldo AND "
                "penalty_clearly_disproportionate_to_breach"
            ),
            (
                "requires_human_bankruptcy_setoff_assessment == "
                "(setoff_of_mutual_homogeneous_claims_asserted AND "
                "setoff_would_violate_priority_order AND NOT operation_is_saldo_not_setoff) OR "
                "(operation_is_saldo_not_setoff AND "
                "counter_obligations_arise_from_linked_contracts) OR "
                "penalty_disproportion_remedied_by_article_333"
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
    operation_is_saldo_not_setoff = Bool("operation_is_saldo_not_setoff")
    setoff_prohibited = Bool("setoff_prohibited")
    setoff_permitted_as_priority_neutral = Bool("setoff_permitted_as_priority_neutral")
    netting_permitted_by_financial_contract_exception = Bool(
        "netting_permitted_by_financial_contract_exception"
    )
    prior_judgments_do_not_bar_saldo = Bool("prior_judgments_do_not_bar_saldo")
    penalty_disproportion_remedied_by_article_333 = Bool(
        "penalty_disproportion_remedied_by_article_333"
    )
    requires_human_bankruptcy_setoff_assessment = Bool(
        "requires_human_bankruptcy_setoff_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    # Пункт 17 Обзора ВС РФ по банкротству за 2022 год: сопоставление обязанностей
    # из одного договора (либо взаимосвязанных) с определением завершающего
    # исполнения — не зачёт. Название операции, данное стороной, не решает.
    solver.add(
        operation_is_saldo_not_setoff
        == And(
            Or(
                variables["counter_obligations_arise_from_one_contract"],
                variables["counter_obligations_arise_from_linked_contracts"],
            ),
            variables["operation_determines_final_obligation_by_comparing_performances"],
        )
    )
    solver.add(
        setoff_prohibited
        == And(
            variables["observation_introduced"],
            variables["setoff_of_mutual_homogeneous_claims_asserted"],
            variables["setoff_would_violate_priority_order"],
            Not(variables["arises_from_financial_contract_netting_under_article_4_1"]),
            Not(operation_is_saldo_not_setoff),
        )
    )
    solver.add(
        setoff_permitted_as_priority_neutral
        == And(
            variables["observation_introduced"],
            variables["setoff_of_mutual_homogeneous_claims_asserted"],
            Not(variables["setoff_would_violate_priority_order"]),
            Not(operation_is_saldo_not_setoff),
        )
    )
    solver.add(
        netting_permitted_by_financial_contract_exception
        == variables["arises_from_financial_contract_netting_under_article_4_1"]
    )
    # Взыскание встречных требований судом названо, чтобы быть отброшенным: в
    # правило сальдо оно не входит.
    solver.add(
        prior_judgments_do_not_bar_saldo
        == And(operation_is_saldo_not_setoff, variables["counter_claims_already_awarded_by_court"])
    )
    # Пункт 4 Обзора за 2023 год: неустойка в сальдо не делает его предпочтением,
    # а против явной несоразмерности защищает статья 333 ГК РФ.
    solver.add(
        penalty_disproportion_remedied_by_article_333
        == And(
            operation_is_saldo_not_setoff,
            variables["penalty_counted_in_saldo"],
            variables["penalty_clearly_disproportionate_to_breach"],
        )
    )
    solver.add(
        requires_human_bankruptcy_setoff_assessment
        == Or(
            And(
                variables["setoff_of_mutual_homogeneous_claims_asserted"],
                variables["setoff_would_violate_priority_order"],
                Not(operation_is_saldo_not_setoff),
            ),
            And(
                operation_is_saldo_not_setoff,
                variables["counter_obligations_arise_from_linked_contracts"],
            ),
            penalty_disproportion_remedied_by_article_333,
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
            operation_is_saldo_not_setoff=False,
            prior_judgments_do_not_bar_saldo=False,
            penalty_disproportion_remedied_by_article_333=False,
            requires_human_bankruptcy_setoff_assessment=True,
            reasons_ru=["Набор фактов о зачёте требований в деле о банкротстве противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = []
    if truth(operation_is_saldo_not_setoff):
        source = (
            "одного договора"
            if truth(variables["counter_obligations_arise_from_one_contract"])
            else "нескольких взаимосвязанных договоров"
        )
        named = (
            " Сторона назвала операцию зачётом, но квалификацию определяет её "
            "содержание, а не название."
            if truth(variables["setoff_of_mutual_homogeneous_claims_asserted"])
            else ""
        )
        reasons_ru.append(
            f"Операция — определение сальдо, а не зачёт: она сопоставляет обязанности "
            f"сторон из {source} и определяет лицо, на которое возлагается завершающее "
            "исполнение. Встречные требования в такой ситуации фактически не возникают, "
            "поэтому запрет зачёта абзаца шестого пункта 1 статьи 63 127-ФЗ к ней не "
            "относится, и как сделка с предпочтением по статье 61.3 она не оспаривается "
            "(пункт 17 Обзора судебной практики ВС РФ по делам о банкротстве за 2022 год)." + named
        )
    if truth(prior_judgments_do_not_bar_saldo):
        reasons_ru.append(
            "Взыскание встречных требований вступившими в законную силу судебными актами "
            "не препятствует определению итоговой обязанности одной из сторон (пункт 17 "
            "Обзора за 2022 год)."
        )
    if truth(operation_is_saldo_not_setoff) and truth(variables["penalty_counted_in_saldo"]):
        reasons_ru.append(
            "Учёт неустойки при сальдировании сам по себе не делает его недействительной "
            "сделкой с предпочтением (пункт 4 Обзора судебной практики ВС РФ по делам о "
            "банкротстве за 2023 год)."
        )
    if truth(penalty_disproportion_remedied_by_article_333):
        reasons_ru.append(
            "Неустойка, учтённая при сальдировании, явно несоразмерна последствиям "
            "нарушения: права должника и его кредиторов защищает уменьшение неустойки по "
            "статье 333 ГК РФ, а не недействительность сальдирования. Несоразмерность и "
            "размер уменьшения оценивает суд."
        )
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
        or truth(operation_is_saldo_not_setoff)
    ):
        reasons_ru.append(
            "Ни зачёт встречного однородного требования, ни сальдо по договору, ни "
            "определение нетто-обязательства по финансовым договорам не заявлены — статья "
            "63 127-ФЗ к прекращению этого обязательства не применяется."
        )
    if truth(requires_human_bankruptcy_setoff_assessment):
        grounds = []
        if (
            truth(variables["setoff_of_mutual_homogeneous_claims_asserted"])
            and truth(variables["setoff_would_violate_priority_order"])
            and not truth(operation_is_saldo_not_setoff)
        ):
            grounds.append(
                "в сальдо отказано, и от этого зависит запрет зачёта: квалификация требует "
                "истолковать документы сторон по статье 431 ГК РФ, а не по их названию "
                "(пункт 16 Обзора за 2022 год)"
            )
        if truth(operation_is_saldo_not_setoff) and truth(
            variables["counter_obligations_arise_from_linked_contracts"]
        ):
            grounds.append("сальдо держится на взаимосвязанности нескольких договоров")
        if truth(penalty_disproportion_remedied_by_article_333):
            grounds.append("несоразмерность неустойки и её уменьшение оценивает суд")
        reasons_ru.append("Требуется проверка юристом: " + "; ".join(grounds) + ".")
    return BankruptcySetoffEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        setoff_prohibited=truth(setoff_prohibited),
        setoff_permitted_as_priority_neutral=truth(setoff_permitted_as_priority_neutral),
        netting_permitted_by_financial_contract_exception=truth(
            netting_permitted_by_financial_contract_exception
        ),
        operation_is_saldo_not_setoff=truth(operation_is_saldo_not_setoff),
        prior_judgments_do_not_bar_saldo=truth(prior_judgments_do_not_bar_saldo),
        penalty_disproportion_remedied_by_article_333=truth(
            penalty_disproportion_remedied_by_article_333
        ),
        requires_human_bankruptcy_setoff_assessment=truth(
            requires_human_bankruptcy_setoff_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель разбирает запрет зачёта абзаца шестого пункта 1 статьи 63 127-ФЗ, "
            "названное в нём исключение для нетто-обязательств по финансовым договорам и "
            "отграничение зачёта от сальдо по критерию Верховного Суда. Условия статьи 4.1 "
            "127-ФЗ — генеральное соглашение, правила организованных торгов и клиринга, "
            "закрытый перечень лиц — модель не проверяет: это отдельный институт, и признак "
            "'нетто-обязательство по статье 4.1' остаётся проверенным фактом рецензента.",
            "Сальдо модель выводит из двух признаков рецензента — откуда встречные "
            "обязанности и определяет ли операция завершающую обязанность. Сумм сальдо она "
            "не считает: несогласие с ними само по себе сальдирование не порочит и "
            "разрешается при установлении требований (пункт 4 Обзора за 2023 год).",
            "Очерёдность погашения внутри сальдо по статье 319 ГК РФ модель не проверяет: "
            "Верховный Суд отнёс этот довод к спору о включении требований в реестр.",
        ],
    )
