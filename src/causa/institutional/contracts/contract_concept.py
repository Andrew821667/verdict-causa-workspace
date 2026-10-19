"""Формальная модель понятия договора и применимых к нему правил.

Статья 420 ГК РФ целиком: четыре пункта.

**Почему институт появился и почему позже всех.** Статья 420 стояла сразу в
двух картах пробелов, и карты отвечали по-разному. Измерение покрытия практики
держало её в `KNOWN_GAPS_RU` как пробел: «статья лежит между моделью
обязательств и моделью свободы договора». Обход кодекса держал её в
`CODE_GAP_REASONS_RU` как **границу** с причиной «не содержит правила, которое
можно проверить». Второе утверждение неверно, и неверность видна в тексте:
пункты 2, 3 и 4 построены на условии «если иное не установлено», «если иное не
предусмотрено», «если это не противоречит». Условие, из которого следует
применимость целого свода правил, проверяемо ровно настолько, насколько
проверяемо любое другое условие модели.

**Чем статья отличается от всех остальных институтов пакета.** Остальные
институты отвечают на вопрос о судьбе требования: возникло ли, нарушено ли,
прекращено ли, подлежит ли защите. Эта статья отвечает на вопрос о том,
**какие своды правил к делу применяются вообще**. Её выводы — не о деле, а о
том, чем дело разбирать.

Такой вывод в пакете до сих пор не выводился ниоткуда: он был **встроен в
устройство конвейера**. Конвейер прогоняет институт сделок (глава 9), институт
общих положений об обязательствах (307–308.3) и институт специального
договорного типа, а слой общих положений сводит общее со специальным. Статья
420 — это норма, которая такое устройство разрешает; до появления института
разрешение было молчаливой посылкой архитектуры, а не проверяемым выводом.

## Пункт 1: что вообще является договором

«Договором признается соглашение двух или нескольких лиц об установлении,
изменении или прекращении гражданских прав и обязанностей.»

Три условия, и каждое отсекает свой случай:

* **соглашение двух или нескольких лиц** — односторонняя сделка (завещание,
  доверенность, отказ от договора) договором не является, сколько бы
  гражданских прав она ни устанавливала;
* **направленность на установление, изменение или прекращение** — три
  направленности равноправны и соединены союзом «или»: соглашение о
  расторжении есть договор не менее, чем соглашение о поставке;
* **гражданские права и обязанности** — соглашение о правах трудовых,
  налоговых или процессуальных под это понятие не подпадает, и правила части
  первой ГК РФ к нему по статье 420 не применяются.

Обе неудачи квалификации выведены **отдельными выводами**, а не оставлены
пустотой. «Ничего не выведено» и «это не договор» читаются по-разному: первое
похоже на отсутствие ответа, второе отвечает, и отвечает по-разному для
односторонней сделки и для соглашения о негражданских правах.

До этого института признак «договор заявлен» существовал в пакете только как
предикат рецензента `contract_asserted` института свободы договора, введённый
в выпуске 1.19.0, и не сверялся ни с чем. Теперь он сверяется с выводом этой
модели: два института, описывающие один факт по-разному, — ровно то, ради чего
существует слой сверки фактов.

## Пункт 2: вытеснить правила о сделках может только Кодекс

«К договорам применяются правила о двух- и многосторонних сделках,
предусмотренные главой 9 настоящего Кодекса, если иное не установлено
**настоящим Кодексом**.»

Оговорка названа адресно, и это не стилистика. Правила главы 9 — о форме, о
недействительности, о согласии третьего лица — вытесняются только самим
Кодексом: ни законом вне Кодекса, ни тем более соглашением сторон. Условие
договора, объявляющее правила о недействительности неприменимыми, пункт 2
статьи 420 не исполняет.

## Пункт 3: общие положения об обязательствах и что их вытесняет

«К обязательствам, возникшим из договора, применяются общие положения об
обязательствах (статьи 307 - 419), если иное не предусмотрено правилами
настоящей главы и правилами об отдельных видах договоров, **содержащимися в
настоящем Кодексе**.»

Та же адресная оговорка, и те же два вытесняющих источника: глава 27 и правила
об отдельных видах договоров. Здесь лежит главная ловушка прочтения, и модель
её избегает прямо.

**Предикат спрашивает не о существовании специальных правил, а о вытеснении
того общего положения, на которое опирается разбор.** У любого поименованного
договора специальные правила есть — иначе он не был бы поименован. Если читать
условие как «существуют ли правила о поставке», оно будет выполнено в каждом
деле о поставке, и общие положения об обязательствах окажутся вытесненными
всегда, чего пункт 3 не говорит и близко. Специальное правило вытесняет общее
там, где отвечает на тот же вопрос иначе; в остальном оно общее правило
дополняет.

**Чего модель не знает о вытеснении.** Она знает, что какое-то общее положение
вытеснено, но не знает какое: её предикаты говорят о сводах правил, а не об
отдельных нормах. Поэтому вывод о вытеснении не отменяет ни одного конкретного
вывода конвейера — он поднимает флаг юриста. Молчаливо снять вывод, опирающийся
на статью 401, потому что специальное правило вытеснило статью 395, было бы
хуже, чем не снять ничего.

## Пункт 4: многосторонний договор

«К договорам, заключаемым более чем двумя сторонами, общие положения о договоре
применяются, если это не противоречит многостороннему характеру таких
договоров.»

Единственный пункт статьи с оценочным условием: что именно противоречит
многостороннему характеру, устанавливает суд. Поэтому обе ветви выведены —
правила применяются или не применяются, — и заявленное противоречие всегда
поднимает флаг юриста.

## Чего модель не делает

* **Не решает вопрос о диспозитивности нормы.** Пункты 2 и 3 говорят о
  вытеснении одного свода правил другим сводом; может ли соглашение сторон
  отступить от конкретной диспозитивной нормы, решают статьи 421 и 422, а не
  статья 420. Попытка вытеснения соглашением выведена отдельно именно для
  того, чтобы отправить вопрос туда, а не ответить на него здесь.
* **Не проверяет заключённость договора.** Что перед нами договор и что он
  заключён — разные вопросы: первый решает статья 420, второй — статья 432 и
  институт заключения.
* **Не перечисляет вытесненные нормы** — см. выше о границе точности.
* **Отвечает об одном договоре** и одном возникшем из него обязательстве:
  контракт данных даёт один блок доказательств на институт.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

CONTRACT_CONCEPT_EVIDENCE_SCHEMA_VERSION = "contracts.contract-concept-evidence.v0"
CONTRACT_CONCEPT_MAPPING_VERSION = "contracts-reviewed-contract-concept-to-facts-v0"
CONTRACT_CONCEPT_MODEL_VERSION = "contracts-contract-concept-article-420-v0"

# Дословный текст статьи 420 ГК РФ — synthetic_sources.py,
# synthetic-ru-gk420-contract-concept-v1. Остальные три ссылки — своды правил,
# о применимости которых статья и говорит: глава 9 (пункт 2), общие положения
# об обязательствах (пункт 3) и свобода договора со статьёй 422, куда модель
# отправляет вопрос о диспозитивности нормы.
CONTRACT_CONCEPT_LEGAL_SOURCE_REFS = (
    "synthetic-ru-gk420-contract-concept-v1",
    "synthetic-ru-gk153-157-transaction-concept-kinds-and-conditions-v1",
    "synthetic-ru-gk307-308-obligation-concept-v1",
    "synthetic-ru-gk421-422-freedom-of-contract-v1",
)


class ContractConceptEvidencePredicate(str, Enum):
    # --- Пункт 1: признаки договора ---
    # Соглашение двух или нескольких лиц.
    AGREEMENT_OF_TWO_OR_MORE_PERSONS = "agreement_of_two_or_more_persons"
    # Заявлена односторонняя сделка: распоряжение одного лица. Договором она не
    # является независимо от того, какие права устанавливает.
    SINGLE_PERSON_DISPOSITION_ASSERTED = "single_person_disposition_asserted"
    # Направлено на установление прав и обязанностей.
    DIRECTED_AT_ESTABLISHING_RIGHTS_AND_DUTIES = "directed_at_establishing_rights_and_duties"
    # Направлено на изменение прав и обязанностей.
    DIRECTED_AT_CHANGING_RIGHTS_AND_DUTIES = "directed_at_changing_rights_and_duties"
    # Направлено на прекращение прав и обязанностей.
    DIRECTED_AT_TERMINATING_RIGHTS_AND_DUTIES = "directed_at_terminating_rights_and_duties"
    # Права и обязанности лежат вне гражданского права: трудовые, налоговые,
    # процессуальные. Понятие договора статьи 420 их не охватывает.
    RIGHTS_AND_DUTIES_LIE_OUTSIDE_CIVIL_LAW = "rights_and_duties_lie_outside_civil_law"

    # --- Пункт 2: правила главы 9 о сделках ---
    # Иное о применении правил главы 9 установлено самим Кодексом.
    CODE_PROVIDES_OTHERWISE_FOR_TRANSACTION_RULES = "code_provides_otherwise_for_transaction_rules"

    # --- Пункт 3: общие положения об обязательствах ---
    # Спорное обязательство возникло из этого договора.
    OBLIGATION_AROSE_FROM_THE_CONTRACT = "obligation_arose_from_the_contract"
    # Правило главы 27 вытесняет то общее положение об обязательствах, на
    # которое опирается разбор.
    CHAPTER_27_RULE_PROVIDES_OTHERWISE = "chapter_27_rule_provides_otherwise"
    # Правило об отдельном виде договора вытесняет то общее положение, на
    # которое опирается разбор. Вопрос не в существовании специальных правил —
    # они есть у каждого поименованного договора, — а в вытеснении.
    SPECIFIC_CONTRACT_TYPE_RULE_PROVIDES_OTHERWISE = (
        "specific_contract_type_rule_provides_otherwise"
    )
    # Вытеснение правил Кодекса заявлено соглашением сторон. Пункты 2 и 3
    # называют вытесняющий источник адресно, и соглашения среди них нет.
    DISPLACEMENT_ASSERTED_BY_AGREEMENT_NOT_BY_CODE = (
        "displacement_asserted_by_agreement_not_by_code"
    )

    # --- Пункт 4: многосторонний договор ---
    # Договор заключается более чем двумя сторонами.
    CONTRACT_HAS_MORE_THAN_TWO_PARTIES = "contract_has_more_than_two_parties"
    # Применение общего положения о договоре противоречит многостороннему
    # характеру договора. Условие оценочное: его устанавливает суд.
    GENERAL_CONTRACT_PROVISION_CONTRADICTS_MULTILATERAL_NATURE = (
        "general_contract_provision_contradicts_multilateral_nature"
    )


REQUIRED_CONTRACT_CONCEPT_PREDICATES = frozenset(ContractConceptEvidencePredicate)


class ContractConceptEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ContractConceptEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedContractConceptEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = CONTRACT_CONCEPT_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ContractConceptEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedContractConceptEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Contract-concept evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Contract-concept evidence contains duplicate legal source refs.")
        return self


class ContractConceptFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    agreement_of_two_or_more_persons: bool
    single_person_disposition_asserted: bool
    directed_at_establishing_rights_and_duties: bool
    directed_at_changing_rights_and_duties: bool
    directed_at_terminating_rights_and_duties: bool
    rights_and_duties_lie_outside_civil_law: bool
    code_provides_otherwise_for_transaction_rules: bool
    obligation_arose_from_the_contract: bool
    chapter_27_rule_provides_otherwise: bool
    specific_contract_type_rule_provides_otherwise: bool
    displacement_asserted_by_agreement_not_by_code: bool
    contract_has_more_than_two_parties: bool
    general_contract_provision_contradicts_multilateral_nature: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ContractConceptFactSet":
        if self.agreement_of_two_or_more_persons and self.single_person_disposition_asserted:
            raise ValueError(
                "Один и тот же акт не может быть и соглашением двух или нескольких лиц, "
                "и односторонней сделкой: пункт 1 статьи 420 различает их по числу "
                "выразивших волю."
            )
        aim = (
            self.directed_at_establishing_rights_and_duties
            or self.directed_at_changing_rights_and_duties
            or self.directed_at_terminating_rights_and_duties
        )
        if self.rights_and_duties_lie_outside_civil_law and not aim:
            raise ValueError(
                "Отрасль прав и обязанностей названа, а самих прав и обязанностей нет: "
                "пункт 1 статьи 420 относит к гражданским те права, на установление, "
                "изменение или прекращение которых соглашение направлено."
            )
        if self.contract_has_more_than_two_parties and not self.agreement_of_two_or_more_persons:
            raise ValueError(
                "Договор более чем двух сторон предполагает соглашение двух или "
                "нескольких лиц: пункт 4 статьи 420 говорит о договорах, а не об "
                "односторонних сделках."
            )
        if (
            self.general_contract_provision_contradicts_multilateral_nature
            and not self.contract_has_more_than_two_parties
        ):
            raise ValueError(
                "Противоречие многостороннему характеру без более чем двух сторон "
                "беспредметно: оговорка пункта 4 статьи 420 адресована именно таким "
                "договорам."
            )
        if self.obligation_arose_from_the_contract and not self.agreement_of_two_or_more_persons:
            raise ValueError(
                "Обязательство не может возникнуть из договора, которого нет: пункт 3 "
                "статьи 420 говорит об обязательствах, возникших из договора."
            )
        if (
            self.chapter_27_rule_provides_otherwise
            or self.specific_contract_type_rule_provides_otherwise
        ) and not self.obligation_arose_from_the_contract:
            raise ValueError(
                "Вытеснение общего положения об обязательствах заявлено, а обязательства "
                "из договора нет: пункт 3 статьи 420 решает, какие правила применяются к "
                "возникшему из договора обязательству."
            )
        if (
            self.displacement_asserted_by_agreement_not_by_code
            and not self.agreement_of_two_or_more_persons
        ):
            raise ValueError(
                "Вытеснение соглашением сторон предполагает само соглашение: без него "
                "утверждение беспредметно."
            )
        return self


class ContractConceptFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ContractConceptEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ContractConceptFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ContractConceptFactProvenance] = Field(default_factory=list)


class ContractConceptConstraintSet(BaseModel):
    id: str
    model_version: str = CONTRACT_CONCEPT_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ContractConceptEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    #: Акт отвечает понятию договора пункта 1 статьи 420.
    contract_qualified_under_article_420: bool
    #: Квалификация не состоялась: заявлена односторонняя сделка.
    qualification_fails_for_lack_of_a_second_party: bool
    #: Квалификация не состоялась: права и обязанности не гражданские.
    qualification_fails_for_non_civil_subject_matter: bool
    #: К договору применяются правила главы 9 о сделках (пункт 2).
    chapter_9_transaction_rules_apply: bool
    #: К обязательству применяются общие положения статей 307–419 (пункт 3).
    general_obligation_provisions_apply: bool
    #: Специальное правило вытеснило общее положение об обязательствах (пункт 3).
    special_rule_displaces_general_provisions: bool
    #: Вытеснить правила Кодекса соглашением сторон нельзя: пункты 2 и 3
    #: называют вытесняющий источник адресно.
    agreement_cannot_displace_code_rules: bool
    #: К многостороннему договору применяются общие положения о договоре (пункт 4).
    general_contract_provisions_apply_to_multiparty_contract: bool
    #: Общее положение о договоре к многостороннему договору не применяется (пункт 4).
    general_contract_provisions_withheld_from_multiparty_contract: bool
    requires_human_contract_concept_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_contract_concept_evidence(
    evidence: ReviewedContractConceptEvidence,
) -> ContractConceptEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Contract-concept evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Contract-concept evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_CONTRACT_CONCEPT_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed contract-concept evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_CONTRACT_CONCEPT_PREDICATES
    }
    return ContractConceptEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=CONTRACT_CONCEPT_MAPPING_VERSION,
        facts=ContractConceptFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ContractConceptFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_CONTRACT_CONCEPT_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_contract_concept_constraint_set(
    mapping: ContractConceptEvidenceMappingResult,
) -> ContractConceptConstraintSet:
    return ContractConceptConstraintSet(
        id=f"contract-concept-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            (
                "contract_qualified_under_article_420 == agreement_of_two_or_more_persons AND "
                "(directed_at_establishing_rights_and_duties OR "
                "directed_at_changing_rights_and_duties OR "
                "directed_at_terminating_rights_and_duties) AND "
                "NOT rights_and_duties_lie_outside_civil_law"
            ),
            (
                "qualification_fails_for_lack_of_a_second_party == "
                "single_person_disposition_asserted"
            ),
            (
                "qualification_fails_for_non_civil_subject_matter == "
                "agreement_of_two_or_more_persons AND "
                "(directed_at_establishing_rights_and_duties OR "
                "directed_at_changing_rights_and_duties OR "
                "directed_at_terminating_rights_and_duties) AND "
                "rights_and_duties_lie_outside_civil_law"
            ),
            (
                "chapter_9_transaction_rules_apply == contract_qualified_under_article_420 AND "
                "NOT code_provides_otherwise_for_transaction_rules"
            ),
            (
                "general_obligation_provisions_apply == contract_qualified_under_article_420 AND "
                "obligation_arose_from_the_contract AND NOT chapter_27_rule_provides_otherwise "
                "AND NOT specific_contract_type_rule_provides_otherwise"
            ),
            (
                "special_rule_displaces_general_provisions == "
                "contract_qualified_under_article_420 AND obligation_arose_from_the_contract AND "
                "(chapter_27_rule_provides_otherwise OR "
                "specific_contract_type_rule_provides_otherwise)"
            ),
            (
                "agreement_cannot_displace_code_rules == "
                "displacement_asserted_by_agreement_not_by_code"
            ),
            (
                "general_contract_provisions_apply_to_multiparty_contract == "
                "contract_qualified_under_article_420 AND contract_has_more_than_two_parties AND "
                "NOT general_contract_provision_contradicts_multilateral_nature"
            ),
            (
                "general_contract_provisions_withheld_from_multiparty_contract == "
                "contract_qualified_under_article_420 AND contract_has_more_than_two_parties AND "
                "general_contract_provision_contradicts_multilateral_nature"
            ),
            (
                "requires_human_contract_concept_assessment == "
                "general_contract_provisions_withheld_from_multiparty_contract OR "
                "special_rule_displaces_general_provisions OR "
                "agreement_cannot_displace_code_rules"
            ),
        ],
    )


def evaluate_contract_concept_constraints(
    constraint_set: ContractConceptConstraintSet,
    facts: ContractConceptFactSet,
) -> ContractConceptEvaluation:
    variables = {field_name: Bool(field_name) for field_name in ContractConceptFactSet.model_fields}
    contract_qualified_under_article_420 = Bool("contract_qualified_under_article_420")
    qualification_fails_for_lack_of_a_second_party = Bool(
        "qualification_fails_for_lack_of_a_second_party"
    )
    qualification_fails_for_non_civil_subject_matter = Bool(
        "qualification_fails_for_non_civil_subject_matter"
    )
    chapter_9_transaction_rules_apply = Bool("chapter_9_transaction_rules_apply")
    general_obligation_provisions_apply = Bool("general_obligation_provisions_apply")
    special_rule_displaces_general_provisions = Bool("special_rule_displaces_general_provisions")
    agreement_cannot_displace_code_rules = Bool("agreement_cannot_displace_code_rules")
    general_contract_provisions_apply_to_multiparty_contract = Bool(
        "general_contract_provisions_apply_to_multiparty_contract"
    )
    general_contract_provisions_withheld_from_multiparty_contract = Bool(
        "general_contract_provisions_withheld_from_multiparty_contract"
    )
    requires_human_contract_concept_assessment = Bool("requires_human_contract_concept_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    # Три направленности пункта 1 соединены союзом «или» и равноправны:
    # соглашение о расторжении есть договор не менее, чем соглашение о поставке.
    directed_at_rights_and_duties = Or(
        variables["directed_at_establishing_rights_and_duties"],
        variables["directed_at_changing_rights_and_duties"],
        variables["directed_at_terminating_rights_and_duties"],
    )
    solver.add(
        contract_qualified_under_article_420
        == And(
            variables["agreement_of_two_or_more_persons"],
            directed_at_rights_and_duties,
            Not(variables["rights_and_duties_lie_outside_civil_law"]),
        )
    )
    # Две неудачи квалификации выведены отдельно и по разным причинам: пустота
    # на их месте читалась бы как отсутствие ответа.
    solver.add(
        qualification_fails_for_lack_of_a_second_party
        == variables["single_person_disposition_asserted"]
    )
    solver.add(
        qualification_fails_for_non_civil_subject_matter
        == And(
            variables["agreement_of_two_or_more_persons"],
            directed_at_rights_and_duties,
            variables["rights_and_duties_lie_outside_civil_law"],
        )
    )
    # Пункт 2: вытеснить правила главы 9 может только сам Кодекс.
    solver.add(
        chapter_9_transaction_rules_apply
        == And(
            contract_qualified_under_article_420,
            Not(variables["code_provides_otherwise_for_transaction_rules"]),
        )
    )
    # Пункт 3: два вытесняющих источника — глава 27 и правила об отдельных
    # видах договоров, и оба содержатся в самом Кодексе.
    displaced_by_code = Or(
        variables["chapter_27_rule_provides_otherwise"],
        variables["specific_contract_type_rule_provides_otherwise"],
    )
    solver.add(
        general_obligation_provisions_apply
        == And(
            contract_qualified_under_article_420,
            variables["obligation_arose_from_the_contract"],
            Not(displaced_by_code),
        )
    )
    solver.add(
        special_rule_displaces_general_provisions
        == And(
            contract_qualified_under_article_420,
            variables["obligation_arose_from_the_contract"],
            displaced_by_code,
        )
    )
    # Вывод, который легко потерять: соглашение сторон вытесняющим источником
    # пунктов 2 и 3 не названо, и попытка вытеснения им их условия не исполняет.
    solver.add(
        agreement_cannot_displace_code_rules
        == variables["displacement_asserted_by_agreement_not_by_code"]
    )
    # Пункт 4: обе ветви выведены, потому что условие оценочное.
    solver.add(
        general_contract_provisions_apply_to_multiparty_contract
        == And(
            contract_qualified_under_article_420,
            variables["contract_has_more_than_two_parties"],
            Not(variables["general_contract_provision_contradicts_multilateral_nature"]),
        )
    )
    solver.add(
        general_contract_provisions_withheld_from_multiparty_contract
        == And(
            contract_qualified_under_article_420,
            variables["contract_has_more_than_two_parties"],
            variables["general_contract_provision_contradicts_multilateral_nature"],
        )
    )
    solver.add(
        requires_human_contract_concept_assessment
        == Or(
            general_contract_provisions_withheld_from_multiparty_contract,
            special_rule_displaces_general_provisions,
            agreement_cannot_displace_code_rules,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ContractConceptEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            contract_qualified_under_article_420=False,
            qualification_fails_for_lack_of_a_second_party=False,
            qualification_fails_for_non_civil_subject_matter=False,
            chapter_9_transaction_rules_apply=False,
            general_obligation_provisions_apply=False,
            special_rule_displaces_general_provisions=False,
            agreement_cannot_displace_code_rules=False,
            general_contract_provisions_apply_to_multiparty_contract=False,
            general_contract_provisions_withheld_from_multiparty_contract=False,
            requires_human_contract_concept_assessment=True,
            reasons_ru=["Набор фактов о понятии договора противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru: list[str] = []
    if truth(contract_qualified_under_article_420):
        aims = []
        if truth(variables["directed_at_establishing_rights_and_duties"]):
            aims.append("установление")
        if truth(variables["directed_at_changing_rights_and_duties"]):
            aims.append("изменение")
        if truth(variables["directed_at_terminating_rights_and_duties"]):
            aims.append("прекращение")
        reasons_ru.append(
            "Акт отвечает понятию договора: соглашение двух или нескольких лиц, "
            "направленное на " + ", ".join(aims) + " гражданских прав и обязанностей "
            "(пункт 1 статьи 420 ГК РФ)."
        )
    if truth(qualification_fails_for_lack_of_a_second_party):
        reasons_ru.append(
            "Заявлена односторонняя сделка — распоряжение одного лица. Договором она "
            "не является, сколько бы гражданских прав ни устанавливала: пункт 1 статьи "
            "420 ГК РФ требует соглашения двух или нескольких лиц. Правила о договорах "
            "к такому акту не применяются; его разбирают правила о сделках (глава 9)."
        )
    if truth(qualification_fails_for_non_civil_subject_matter):
        reasons_ru.append(
            "Соглашение направлено на права и обязанности, лежащие вне гражданского "
            "права. Понятие договора пункта 1 статьи 420 ГК РФ их не охватывает, и "
            "правила Кодекса о договорах к такому соглашению по этой статье не "
            "применяются."
        )
    if truth(chapter_9_transaction_rules_apply):
        reasons_ru.append(
            "К договору применяются правила о двух- и многосторонних сделках главы 9 "
            "ГК РФ — о форме, о недействительности, о согласии третьего лица (пункт 2 "
            "статьи 420 ГК РФ)."
        )
    if truth(variables["code_provides_otherwise_for_transaction_rules"]):
        reasons_ru.append(
            "Иное о применении правил главы 9 установлено самим Кодексом, и правила о "
            "сделках в этой части вытеснены (пункт 2 статьи 420 ГК РФ). Оговорка пункта "
            "2 названа адресно: вытеснить их может только Кодекс."
        )
    if truth(general_obligation_provisions_apply):
        reasons_ru.append(
            "К обязательству, возникшему из договора, применяются общие положения об "
            "обязательствах (статьи 307–419 ГК РФ): ни правило главы 27, ни правило об "
            "отдельном виде договора того общего положения, на которое опирается разбор, "
            "не вытесняют (пункт 3 статьи 420 ГК РФ)."
        )
    if truth(special_rule_displaces_general_provisions):
        grounds = []
        if truth(variables["chapter_27_rule_provides_otherwise"]):
            grounds.append("правилом главы 27")
        if truth(variables["specific_contract_type_rule_provides_otherwise"]):
            grounds.append("правилом об отдельном виде договора")
        reasons_ru.append(
            "Общее положение об обязательствах вытеснено " + " и ".join(grounds) + " "
            "(пункт 3 статьи 420 ГК РФ). Какое именно положение вытеснено, модель не "
            "называет: её предикаты говорят о сводах правил, а не об отдельных нормах, "
            "поэтому ни один вывод конвейера она на этом основании не снимает."
        )
    if truth(agreement_cannot_displace_code_rules):
        reasons_ru.append(
            "Вытеснение правил Кодекса заявлено соглашением сторон. Пункты 2 и 3 статьи "
            "420 ГК РФ называют вытесняющий источник адресно — «настоящим Кодексом» и "
            "«содержащимися в настоящем Кодексе», — и соглашения среди них нет. Может ли "
            "соглашение отступить от конкретной диспозитивной нормы, решают статьи 421 и "
            "422 ГК РФ, а не статья 420."
        )
    if truth(general_contract_provisions_apply_to_multiparty_contract):
        reasons_ru.append(
            "Договор заключается более чем двумя сторонами, и общие положения о договоре "
            "к нему применяются: многостороннему характеру это не противоречит (пункт 4 "
            "статьи 420 ГК РФ)."
        )
    if truth(general_contract_provisions_withheld_from_multiparty_contract):
        reasons_ru.append(
            "Применение общего положения о договоре противоречит многостороннему "
            "характеру договора, поэтому оно не применяется (пункт 4 статьи 420 ГК РФ)."
        )
    if truth(requires_human_contract_concept_assessment):
        reasons_ru.append(
            "Требуется оценка юриста. Что противоречит многостороннему характеру "
            "договора, устанавливает суд; какое именно общее положение вытеснено "
            "специальным правилом, модель не называет; вопрос о диспозитивности нормы "
            "решают статьи 421 и 422 ГК РФ."
        )
    return ContractConceptEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        contract_qualified_under_article_420=truth(contract_qualified_under_article_420),
        qualification_fails_for_lack_of_a_second_party=truth(
            qualification_fails_for_lack_of_a_second_party
        ),
        qualification_fails_for_non_civil_subject_matter=truth(
            qualification_fails_for_non_civil_subject_matter
        ),
        chapter_9_transaction_rules_apply=truth(chapter_9_transaction_rules_apply),
        general_obligation_provisions_apply=truth(general_obligation_provisions_apply),
        special_rule_displaces_general_provisions=truth(special_rule_displaces_general_provisions),
        agreement_cannot_displace_code_rules=truth(agreement_cannot_displace_code_rules),
        general_contract_provisions_apply_to_multiparty_contract=truth(
            general_contract_provisions_apply_to_multiparty_contract
        ),
        general_contract_provisions_withheld_from_multiparty_contract=truth(
            general_contract_provisions_withheld_from_multiparty_contract
        ),
        requires_human_contract_concept_assessment=truth(
            requires_human_contract_concept_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель отвечает, какие своды правил к делу применяются, а не какая норма "
            "решает спор: вывод о применимости общих положений об обязательствах не "
            "предрешает ни одного вывода по существу.",
            "Границы точности названы прямо: модель знает, что общее положение "
            "вытеснено специальным правилом, но не знает какое именно, и потому не "
            "снимает выводов конвейера на этом основании.",
            "Диспозитивность нормы — вопрос статей 421 и 422 ГК РФ. Пункты 2 и 3 статьи "
            "420 говорят о вытеснении одного свода правил другим, а не о праве сторон "
            "отступить от отдельной нормы.",
            "Заключённость договора проверяет институт заключения (статья 432 ГК РФ): "
            "что перед нами договор и что он заключён — разные вопросы.",
        ],
    )
