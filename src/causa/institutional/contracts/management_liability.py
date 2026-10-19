"""Формальная модель ответственности управляющих лиц юридического лица.

Статья 53.1 ГК РФ целиком: пять пунктов.

**Почему институт появился.** Пробел нашёл не обход кодекса, а измерение
покрытия практики: статья 53.1 стояла в `KNOWN_GAPS_RU` с причиной «модель лиц
(статьи 17–53) разбирает правоспособность и полномочия органа, но не убытки,
взыскиваемые с директора». Причина была верной, и именно поэтому пробел не
закрывался сам: 53.1 лежит сразу за объявленной границей института лиц, и
расширять ту границу было бы неправдой — предмет другой.

**Чем предмет отличается от института лиц.** Модель лиц отвечает на вопрос, мог
ли орган связать юридическое лицо сделкой. Эта модель отвечает на другой: отвечает
ли управляющее лицо **перед самим юридическим лицом** за причинённые ему убытки.
Стороны разные, обязательство другое, и смешение двух вопросов стирало бы ровно
ту разницу, которую статья 53.1 вводит.

## Три субъекта, не один

Статья называет три основания ответственности, и у них разные условия:

* **пункт 1** — лицо, уполномоченное выступать от имени юридического лица в силу
  закона, иного правового акта или учредительного документа (пункт 3 статьи 53);
* **пункт 2** — члены коллегиальных органов, с двумя исключениями, которых у
  пункта 1 нет;
* **пункт 3** — лицо, имеющее фактическую возможность определять действия
  юридического лица, в том числе давать указания лицам пунктов 1 и 2.

Одно и то же лицо может отвечать по нескольким основаниям сразу — директор,
входящий в правление, или участник, который и голосует, и указывает. Поэтому
модель выводит ответственность по каждому основанию отдельно, а не выбирает
одно: исключение пункта 2 снимает основание пункта 2, а не остальные.

## Стандарт поведения

Пункт 1 абзац 2 требует **доказанности**: ответственность наступает, «если будет
доказано, что при осуществлении своих прав и исполнении своих обязанностей оно
действовало недобросовестно или неразумно, в том числе если его действия
(бездействие) не соответствовали обычным условиям гражданского оборота или
обычному предпринимательскому риску».

Оборот «в том числе» — это включение, а не отдельное основание: несоответствие
обычным условиям оборота или обычному предпринимательскому риску есть частный
случай недобросовестности или неразумности. Поэтому модель выводит нарушение
стандарта из любого из трёх признаков, а не требует их вместе.

**Это самая оценочная часть статьи**, и модель её не решает: что считать обычным
условием оборота и обычным предпринимательским риском, устанавливает суд. Признак
принимается как проверенный факт, а вывод поднимает флаг экспертизы — иначе
решатель выдавал бы за правовой вывод чужую оценку.

## Требование как условие возмещения

Пункт 1 обязывает возместить убытки **по требованию** юридического лица или его
учредителей (участников), выступающих в его интересах. Пункт 2 переносит на
членов коллегиальных органов «ответственность, предусмотренную пунктом 1», то
есть вместе с этим условием.

Пункт 3 сформулирован иначе: «несет ответственность за убытки, причиненные по его
вине юридическому лицу» — о требовании там не сказано. Модель следует тексту и
требования для пункта 3 не требует. Разница не редакционная: пункт 1 описывает
обязанность возместить, возникающую по требованию, а пункт 3 — ответственность
как таковую.

## Вина

Пункты 1 и 3 говорят об убытках, причинённых **по его вине**. Модель требует вины
по всем трём основаниям: пункт 2 переносит ответственность пункта 1 целиком, а
своего правила о вине не вводит.

Нарушение стандарта и вина разделены намеренно. Это не одно и то же: стандарт
отвечает на вопрос, как лицо действовало, а вина — на вопрос, отвечает ли оно за
последствия. Сливать их означало бы выводить вину из поведения автоматически.

## Ничтожность соглашения об ограничении

Пункт 5 устроен несимметрично, и в этой несимметрии вся его суть:

* для лиц пунктов 1 и 2 ничтожно соглашение об устранении или ограничении
  ответственности **за недобросовестные** действия, а в **публичном обществе** —
  за недобросовестные **и неразумные**;
* для лица пункта 3 ничтожно соглашение об устранении или ограничении
  ответственности **без оговорок**.

Отсюда следует вывод, который легко потерять: в непубличном обществе соглашение,
ограничивающее ответственность директора или члена правления за **неразумные**
(но добросовестные) действия, ничтожным не является. Модель выводит это отдельным
полем, а не оставляет читателю вычитать из отрицания.

## Чего модель не делает

Она не определяет размер убытков и не распределяет их между солидарными
должниками: пункт 4 устанавливает солидарность, а не доли. Она не проверяет
полномочия лица по существу — это вопрос института лиц и представительства. Она
отвечает об ответственности **одного** лица по одному требованию.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

MANAGEMENT_LIABILITY_EVIDENCE_SCHEMA_VERSION = "contracts.management-liability-evidence.v0"
MANAGEMENT_LIABILITY_MAPPING_VERSION = "contracts-reviewed-management-liability-to-facts-v0"
MANAGEMENT_LIABILITY_MODEL_VERSION = "contracts-management-liability-article-53-1-v0"

# Дословный текст статьи 53.1 ГК РФ — synthetic_sources.py,
# synthetic-ru-gk53-1-management-liability-v1; пункт 3 статьи 53, к которому
# пункты 1 и 5 отсылают, — в составе модели статей 49–53.
MANAGEMENT_LIABILITY_LEGAL_SOURCE_REFS = (
    "synthetic-ru-gk53-1-management-liability-v1",
    "synthetic-ru-gk49-53-capacity-registration-and-bodies-of-legal-entities-v1",
)


class ManagementLiabilityEvidencePredicate(str, Enum):
    # --- Субъект: три основания пунктов 1, 2 и 3 ---
    # Уполномочен выступать от имени юридического лица в силу закона, иного
    # правового акта или учредительного документа (пункт 1, отсылка к пункту 3
    # статьи 53).
    AUTHORISED_TO_ACT_FOR_ENTITY = "authorised_to_act_for_entity"
    # Член коллегиального органа юридического лица (пункт 2).
    MEMBER_OF_COLLEGIAL_BODY = "member_of_collegial_body"
    # Имеет фактическую возможность определять действия юридического лица, в том
    # числе давать указания лицам пунктов 1 и 2 (пункт 3).
    HAS_ACTUAL_ABILITY_TO_DETERMINE_ACTIONS = "has_actual_ability_to_determine_actions"

    # --- Требование и убытки ---
    # Требование заявлено юридическим лицом либо его учредителями (участниками),
    # выступающими в интересах юридического лица (пункт 1).
    CLAIM_BROUGHT_BY_ENTITY_OR_PARTICIPANT = "claim_brought_by_entity_or_participant"
    # Юридическому лицу причинены убытки (пункты 1 и 3).
    LOSSES_CAUSED_TO_ENTITY = "losses_caused_to_entity"
    # Убытки причинены по вине этого лица (пункты 1 и 3).
    FAULT_PROVEN = "fault_proven"
    # Убытки причинены совместно с другими лицами пунктов 1–3 (пункт 4).
    LOSSES_CAUSED_JOINTLY_WITH_OTHERS = "losses_caused_jointly_with_others"

    # --- Стандарт поведения: пункт 1 абзац 2 ---
    # Доказана недобросовестность при осуществлении прав и исполнении
    # обязанностей.
    BAD_FAITH_PROVEN = "bad_faith_proven"
    # Доказана неразумность при осуществлении прав и исполнении обязанностей.
    UNREASONABLENESS_PROVEN = "unreasonableness_proven"
    # Действия (бездействие) не соответствовали обычным условиям гражданского
    # оборота или обычному предпринимательскому риску. Оборот «в том числе»
    # делает это частным случаем двух предыдущих, а не отдельным основанием.
    CONDUCT_OUTSIDE_ORDINARY_COURSE_OR_RISK = "conduct_outside_ordinary_course_or_risk"

    # --- Исключения для члена коллегиального органа: пункт 2 ---
    # Голосовал против решения, которое повлекло причинение убытков.
    VOTED_AGAINST_THE_HARMFUL_DECISION = "voted_against_the_harmful_decision"
    # Действуя добросовестно, не принимал участия в голосовании.
    ABSTAINED_IN_GOOD_FAITH = "abstained_in_good_faith"

    # --- Соглашение об устранении или ограничении ответственности: пункт 5 ---
    LIABILITY_LIMITATION_AGREEMENT_MADE = "liability_limitation_agreement_made"
    # Юридическое лицо — публичное общество: для лиц пунктов 1 и 2 ничтожность
    # распространяется и на неразумные действия.
    ENTITY_IS_PUBLIC_COMPANY = "entity_is_public_company"
    # Соглашение охватывает недобросовестные действия.
    AGREEMENT_COVERS_BAD_FAITH_CONDUCT = "agreement_covers_bad_faith_conduct"
    # Соглашение охватывает неразумные действия.
    AGREEMENT_COVERS_UNREASONABLE_CONDUCT = "agreement_covers_unreasonable_conduct"


REQUIRED_MANAGEMENT_LIABILITY_PREDICATES = frozenset(ManagementLiabilityEvidencePredicate)


class ManagementLiabilityEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ManagementLiabilityEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedManagementLiabilityEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = MANAGEMENT_LIABILITY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ManagementLiabilityEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedManagementLiabilityEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Management-liability evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Management-liability evidence contains duplicate legal source refs.")
        return self


class ManagementLiabilityFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    authorised_to_act_for_entity: bool
    member_of_collegial_body: bool
    has_actual_ability_to_determine_actions: bool
    claim_brought_by_entity_or_participant: bool
    losses_caused_to_entity: bool
    fault_proven: bool
    losses_caused_jointly_with_others: bool
    bad_faith_proven: bool
    unreasonableness_proven: bool
    conduct_outside_ordinary_course_or_risk: bool
    voted_against_the_harmful_decision: bool
    abstained_in_good_faith: bool
    liability_limitation_agreement_made: bool
    entity_is_public_company: bool
    agreement_covers_bad_faith_conduct: bool
    agreement_covers_unreasonable_conduct: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ManagementLiabilityFactSet":
        if self.voted_against_the_harmful_decision and self.abstained_in_good_faith:
            raise ValueError(
                "Член коллегиального органа не может одновременно голосовать против "
                "решения и не принимать участия в голосовании: пункт 2 статьи 53.1 "
                "называет это двумя разными исключениями."
            )
        if (
            self.voted_against_the_harmful_decision or self.abstained_in_good_faith
        ) and not self.member_of_collegial_body:
            raise ValueError(
                "Исключения пункта 2 статьи 53.1 относятся к членам коллегиальных "
                "органов: без этого признака голосование и неучастие в нём беспредметны."
            )
        if self.fault_proven and not self.losses_caused_to_entity:
            raise ValueError(
                "Вина в причинении убытков без самих убытков беспредметна: пункты 1 и 3 "
                "статьи 53.1 говорят об убытках, причинённых по вине лица."
            )
        if self.losses_caused_jointly_with_others and not self.losses_caused_to_entity:
            raise ValueError(
                "Совместное причинение убытков предполагает убытки: пункт 4 статьи 53.1 "
                "устанавливает солидарность за причинённое, а не за возможное."
            )
        if (
            self.agreement_covers_bad_faith_conduct or self.agreement_covers_unreasonable_conduct
        ) and not self.liability_limitation_agreement_made:
            raise ValueError(
                "Охват соглашения описан, а самого соглашения нет: пункт 5 статьи 53.1 "
                "оценивает ничтожность состоявшегося соглашения."
            )
        return self


class ManagementLiabilityFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ManagementLiabilityEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ManagementLiabilityFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ManagementLiabilityFactProvenance] = Field(default_factory=list)


class ManagementLiabilityConstraintSet(BaseModel):
    id: str
    model_version: str = MANAGEMENT_LIABILITY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ManagementLiabilityEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    #: Лицо относится к субъектам статьи 53.1 хотя бы по одному пункту.
    person_within_article_53_1: bool
    #: Нарушен стандарт пункта 1 абзаца 2: недобросовестность или неразумность.
    standard_of_conduct_breached: bool
    #: Член коллегиального органа освобождён исключением пункта 2.
    collegial_member_exempt: bool
    #: Ответственность по пункту 1 — уполномоченное выступать от имени лицо.
    liability_of_authorised_person: bool
    #: Ответственность по пункту 2 — член коллегиального органа.
    liability_of_collegial_member: bool
    #: Ответственность по пункту 3 — лицо, определяющее действия.
    liability_of_controlling_person: bool
    #: Солидарная обязанность возместить убытки (пункт 4).
    joint_and_several_liability: bool
    #: Соглашение об устранении или ограничении ответственности ничтожно (пункт 5).
    liability_limitation_agreement_void: bool
    #: Ограничение ответственности за неразумные действия допустимо: непубличное
    #: общество, соглашение не охватывает недобросовестность (пункт 5 абзац 1).
    limitation_of_unreasonable_conduct_permitted: bool
    requires_human_management_liability_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_management_liability_evidence(
    evidence: ReviewedManagementLiabilityEvidence,
) -> ManagementLiabilityEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Management-liability evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Management-liability evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value
        for predicate in REQUIRED_MANAGEMENT_LIABILITY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed management-liability evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_MANAGEMENT_LIABILITY_PREDICATES
    }
    return ManagementLiabilityEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=MANAGEMENT_LIABILITY_MAPPING_VERSION,
        facts=ManagementLiabilityFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ManagementLiabilityFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_MANAGEMENT_LIABILITY_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_management_liability_constraint_set(
    mapping: ManagementLiabilityEvidenceMappingResult,
) -> ManagementLiabilityConstraintSet:
    return ManagementLiabilityConstraintSet(
        id=f"management-liability-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            (
                "person_within_article_53_1 == authorised_to_act_for_entity OR "
                "member_of_collegial_body OR has_actual_ability_to_determine_actions"
            ),
            (
                "standard_of_conduct_breached == bad_faith_proven OR "
                "unreasonableness_proven OR conduct_outside_ordinary_course_or_risk"
            ),
            (
                "collegial_member_exempt == member_of_collegial_body AND "
                "(voted_against_the_harmful_decision OR abstained_in_good_faith)"
            ),
            (
                "liability_of_authorised_person == authorised_to_act_for_entity AND "
                "claim_brought_by_entity_or_participant AND losses_caused_to_entity AND "
                "fault_proven AND standard_of_conduct_breached"
            ),
            (
                "liability_of_collegial_member == member_of_collegial_body AND "
                "claim_brought_by_entity_or_participant AND losses_caused_to_entity AND "
                "fault_proven AND standard_of_conduct_breached AND NOT collegial_member_exempt"
            ),
            (
                "liability_of_controlling_person == has_actual_ability_to_determine_actions AND "
                "losses_caused_to_entity AND fault_proven AND standard_of_conduct_breached"
            ),
            (
                "joint_and_several_liability == losses_caused_jointly_with_others AND "
                "(liability_of_authorised_person OR liability_of_collegial_member OR "
                "liability_of_controlling_person)"
            ),
            (
                "liability_limitation_agreement_void == liability_limitation_agreement_made AND "
                "((has_actual_ability_to_determine_actions) OR "
                "((authorised_to_act_for_entity OR member_of_collegial_body) AND "
                "(agreement_covers_bad_faith_conduct OR "
                "(entity_is_public_company AND agreement_covers_unreasonable_conduct))))"
            ),
            (
                "limitation_of_unreasonable_conduct_permitted == "
                "liability_limitation_agreement_made AND "
                "agreement_covers_unreasonable_conduct AND "
                "NOT agreement_covers_bad_faith_conduct AND NOT entity_is_public_company AND "
                "(authorised_to_act_for_entity OR member_of_collegial_body) AND "
                "NOT has_actual_ability_to_determine_actions"
            ),
            (
                "requires_human_management_liability_assessment == "
                "(person_within_article_53_1 AND conduct_outside_ordinary_course_or_risk) OR "
                "(member_of_collegial_body AND abstained_in_good_faith) OR "
                "joint_and_several_liability"
            ),
        ],
    )


def evaluate_management_liability_constraints(
    constraint_set: ManagementLiabilityConstraintSet,
    facts: ManagementLiabilityFactSet,
) -> ManagementLiabilityEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in ManagementLiabilityFactSet.model_fields
    }
    person_within_article_53_1 = Bool("person_within_article_53_1")
    standard_of_conduct_breached = Bool("standard_of_conduct_breached")
    collegial_member_exempt = Bool("collegial_member_exempt")
    liability_of_authorised_person = Bool("liability_of_authorised_person")
    liability_of_collegial_member = Bool("liability_of_collegial_member")
    liability_of_controlling_person = Bool("liability_of_controlling_person")
    joint_and_several_liability = Bool("joint_and_several_liability")
    liability_limitation_agreement_void = Bool("liability_limitation_agreement_void")
    limitation_of_unreasonable_conduct_permitted = Bool(
        "limitation_of_unreasonable_conduct_permitted"
    )
    requires_human_management_liability_assessment = Bool(
        "requires_human_management_liability_assessment"
    )

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    solver.add(
        person_within_article_53_1
        == Or(
            variables["authorised_to_act_for_entity"],
            variables["member_of_collegial_body"],
            variables["has_actual_ability_to_determine_actions"],
        )
    )
    # Оборот «в том числе» пункта 1 абзаца 2 — включение: несоответствие обычным
    # условиям оборота или обычному предпринимательскому риску есть частный
    # случай недобросовестности или неразумности, а не четвёртое основание.
    solver.add(
        standard_of_conduct_breached
        == Or(
            variables["bad_faith_proven"],
            variables["unreasonableness_proven"],
            variables["conduct_outside_ordinary_course_or_risk"],
        )
    )
    solver.add(
        collegial_member_exempt
        == And(
            variables["member_of_collegial_body"],
            Or(
                variables["voted_against_the_harmful_decision"],
                variables["abstained_in_good_faith"],
            ),
        )
    )
    solver.add(
        liability_of_authorised_person
        == And(
            variables["authorised_to_act_for_entity"],
            variables["claim_brought_by_entity_or_participant"],
            variables["losses_caused_to_entity"],
            variables["fault_proven"],
            standard_of_conduct_breached,
        )
    )
    # Пункт 2 переносит ответственность пункта 1 целиком — вместе с требованием и
    # стандартом, — и добавляет два исключения, которых у пункта 1 нет.
    solver.add(
        liability_of_collegial_member
        == And(
            variables["member_of_collegial_body"],
            variables["claim_brought_by_entity_or_participant"],
            variables["losses_caused_to_entity"],
            variables["fault_proven"],
            standard_of_conduct_breached,
            Not(collegial_member_exempt),
        )
    )
    # Пункт 3 сформулирован без условия о требовании: «несет ответственность за
    # убытки, причиненные по его вине». Модель следует тексту и требования здесь
    # не требует.
    solver.add(
        liability_of_controlling_person
        == And(
            variables["has_actual_ability_to_determine_actions"],
            variables["losses_caused_to_entity"],
            variables["fault_proven"],
            standard_of_conduct_breached,
        )
    )
    solver.add(
        joint_and_several_liability
        == And(
            variables["losses_caused_jointly_with_others"],
            Or(
                liability_of_authorised_person,
                liability_of_collegial_member,
                liability_of_controlling_person,
            ),
        )
    )
    # Пункт 5 несимметричен: для лица пункта 3 ничтожно любое соглашение, для
    # лиц пунктов 1 и 2 — только за недобросовестность, а в публичном обществе
    # ещё и за неразумность.
    solver.add(
        liability_limitation_agreement_void
        == And(
            variables["liability_limitation_agreement_made"],
            Or(
                variables["has_actual_ability_to_determine_actions"],
                And(
                    Or(
                        variables["authorised_to_act_for_entity"],
                        variables["member_of_collegial_body"],
                    ),
                    Or(
                        variables["agreement_covers_bad_faith_conduct"],
                        And(
                            variables["entity_is_public_company"],
                            variables["agreement_covers_unreasonable_conduct"],
                        ),
                    ),
                ),
            ),
        )
    )
    # Вывод, который легко потерять, вычитая из отрицания: в непубличном
    # обществе ограничение ответственности за неразумные (но добросовестные)
    # действия ничтожным не является.
    solver.add(
        limitation_of_unreasonable_conduct_permitted
        == And(
            variables["liability_limitation_agreement_made"],
            variables["agreement_covers_unreasonable_conduct"],
            Not(variables["agreement_covers_bad_faith_conduct"]),
            Not(variables["entity_is_public_company"]),
            Or(
                variables["authorised_to_act_for_entity"],
                variables["member_of_collegial_body"],
            ),
            Not(variables["has_actual_ability_to_determine_actions"]),
        )
    )
    solver.add(
        requires_human_management_liability_assessment
        == Or(
            And(person_within_article_53_1, variables["conduct_outside_ordinary_course_or_risk"]),
            And(variables["member_of_collegial_body"], variables["abstained_in_good_faith"]),
            joint_and_several_liability,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ManagementLiabilityEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            person_within_article_53_1=False,
            standard_of_conduct_breached=False,
            collegial_member_exempt=False,
            liability_of_authorised_person=False,
            liability_of_collegial_member=False,
            liability_of_controlling_person=False,
            joint_and_several_liability=False,
            liability_limitation_agreement_void=False,
            limitation_of_unreasonable_conduct_permitted=False,
            requires_human_management_liability_assessment=True,
            reasons_ru=["Набор фактов об ответственности управляющего лица противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru: list[str] = []
    if not truth(person_within_article_53_1):
        # Пустой вывод без объяснения читался бы как «ответственности нет»,
        # тогда как верно другое: статья 53.1 к этому лицу не применяется.
        reasons_ru.append(
            "Лицо не отнесено ни к одному из субъектов статьи 53.1 ГК РФ: оно не "
            "уполномочено выступать от имени юридического лица, не входит в его "
            "коллегиальный орган и не имеет фактической возможности определять его "
            "действия. Ответственность по этой статье к нему не применяется."
        )
    if truth(standard_of_conduct_breached):
        grounds = []
        if truth(variables["bad_faith_proven"]):
            grounds.append("доказана недобросовестность")
        if truth(variables["unreasonableness_proven"]):
            grounds.append("доказана неразумность")
        if truth(variables["conduct_outside_ordinary_course_or_risk"]):
            grounds.append(
                "действия (бездействие) не соответствовали обычным условиям "
                "гражданского оборота или обычному предпринимательскому риску"
            )
        reasons_ru.append(
            "Нарушен стандарт пункта 1 абзаца 2 статьи 53.1 ГК РФ: " + "; ".join(grounds) + "."
        )
    if truth(collegial_member_exempt):
        ground = (
            "голосовал против решения, повлёкшего причинение убытков"
            if truth(variables["voted_against_the_harmful_decision"])
            else "действуя добросовестно, не принимал участия в голосовании"
        )
        reasons_ru.append(
            "Член коллегиального органа освобождён от ответственности по исключению "
            f"пункта 2 статьи 53.1 ГК РФ: {ground}."
        )
    if truth(liability_of_authorised_person):
        reasons_ru.append(
            "Лицо, уполномоченное выступать от имени юридического лица, обязано "
            "возместить причинённые по его вине убытки по требованию юридического "
            "лица или его участников, выступающих в его интересах (пункт 1 статьи "
            "53.1 ГК РФ)."
        )
    if truth(liability_of_collegial_member):
        reasons_ru.append(
            "Член коллегиального органа несёт ответственность, предусмотренную "
            "пунктом 1 статьи 53.1 ГК РФ: ни одно из исключений пункта 2 к нему не "
            "относится."
        )
    if truth(liability_of_controlling_person):
        reasons_ru.append(
            "Лицо, имеющее фактическую возможность определять действия юридического "
            "лица, обязано действовать в его интересах разумно и добросовестно и "
            "несёт ответственность за причинённые по его вине убытки (пункт 3 статьи "
            "53.1 ГК РФ). Требования юридического лица пункт 3 условием не называет, "
            "в отличие от пункта 1."
        )
    if truth(joint_and_several_liability):
        reasons_ru.append(
            "Убытки причинены совместно, поэтому лица пунктов 1–3 обязаны возместить "
            "их солидарно (пункт 4 статьи 53.1 ГК РФ). Доли между ними статья не "
            "устанавливает, и модель их не определяет."
        )
    if truth(liability_limitation_agreement_void):
        if truth(variables["has_actual_ability_to_determine_actions"]):
            ground = (
                "для лица, имеющего фактическую возможность определять действия "
                "юридического лица, ничтожно любое такое соглашение (пункт 5 абзац 2)"
            )
        elif truth(variables["agreement_covers_bad_faith_conduct"]):
            ground = "соглашение охватывает недобросовестные действия (пункт 5 абзац 1)"
        else:
            ground = (
                "общество публичное, и ничтожность распространяется на неразумные "
                "действия наравне с недобросовестными (пункт 5 абзац 1)"
            )
        reasons_ru.append(
            f"Соглашение об устранении или ограничении ответственности ничтожно: {ground}."
        )
    if truth(limitation_of_unreasonable_conduct_permitted):
        reasons_ru.append(
            "Соглашение ограничивает ответственность за неразумные, но "
            "добросовестные действия, общество не публичное — ничтожным по пункту 5 "
            "статьи 53.1 ГК РФ такое соглашение не является. Вывод назван прямо, "
            "потому что он следует из отрицания и легко теряется при чтении."
        )
    if truth(requires_human_management_liability_assessment):
        reasons_ru.append(
            "Требуется оценка юриста. Что считать обычными условиями гражданского "
            "оборота и обычным предпринимательским риском, а равно добросовестность "
            "неучастия в голосовании, устанавливает суд, а не модель; распределение "
            "солидарно причинённых убытков между должниками статья 53.1 не "
            "определяет."
        )
    return ManagementLiabilityEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        person_within_article_53_1=truth(person_within_article_53_1),
        standard_of_conduct_breached=truth(standard_of_conduct_breached),
        collegial_member_exempt=truth(collegial_member_exempt),
        liability_of_authorised_person=truth(liability_of_authorised_person),
        liability_of_collegial_member=truth(liability_of_collegial_member),
        liability_of_controlling_person=truth(liability_of_controlling_person),
        joint_and_several_liability=truth(joint_and_several_liability),
        liability_limitation_agreement_void=truth(liability_limitation_agreement_void),
        limitation_of_unreasonable_conduct_permitted=truth(
            limitation_of_unreasonable_conduct_permitted
        ),
        requires_human_management_liability_assessment=truth(
            requires_human_management_liability_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель разбирает ответственность одного лица по одному требованию и не "
            "определяет размер убытков: статья 53.1 говорит об обязанности возместить, "
            "а не о её исчислении.",
            "Пункт 4 устанавливает солидарность, но не доли: распределение между "
            "солидарными должниками лежит вне этой модели.",
            "Полномочия лица по существу проверяют институт лиц (статьи 17–53) и "
            "институт представительства; здесь принадлежность к субъектам статьи 53.1 "
            "принимается как проверенный факт.",
        ],
    )
