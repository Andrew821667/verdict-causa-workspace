"""Формальная модель решений собраний: глава 9.1 ГК РФ, статьи 181.1–181.5.

Решение собрания — не сделка. Оно порождает правовые последствия для всех лиц,
имевших право участвовать в собрании, включая тех, кто голосовал против или не
участвовал вовсе (статья 181.1). Поэтому и пороки его оцениваются по своим
правилам, а не по правилам недействительности сделок: глава 9.1 отделена от
статей 166–181, и модель здесь отдельная.

**Почему институт появился.** Последний существенный пробел покрытия, оставшийся
после измерения на реальной судебной практике. Дело 45-КГ23-2-К7: размер платы
по договору управления должен соответствовать решению общего собрания
собственников, и управляющая организация не вправе менять его в одностороннем
порядке. Суд сослался на статьи 181.3 и 181.5 — а их не разбирал ни один
институт пакета.

Связь с договорным правом прямая: решение собрания выступает основанием
договорного условия и его изменения, а недействительность решения бьёт по
условию, которое на нём держится.

## Что модель разделяет

Три исхода, которые нельзя смешивать:

- **решение не принято** — не набрано большинство (статья 181.2). Это не порок
  решения, а его отсутствие;
- **решение ничтожно** — нет кворума, вопрос вне повестки при неполном участии,
  вопрос вне компетенции, противоречие основам правопорядка или нравственности
  (статья 181.5). Недействительно независимо от признания судом;
- **решение оспоримо** — нарушен порядок созыва, подготовки или проведения,
  нарушено равенство прав участников, у выступавшего от имени участника не было
  полномочий, существенно нарушены правила составления протокола (статья 181.4).
  Действует, пока не признано недействительным судом.

## Две «исцеляющие» оговорки статьи 181.4

Оспоримость снимается, и модель проверяет обе раздельно:

- **несущественность** (пункт 4): голос лица не мог повлиять на принятие решения
  и решение не влечёт существенных неблагоприятных последствий для этого лица;
- **подтверждение** (пункт 2): решение подтверждено последующим решением
  собрания, принятым до вынесения решения суда.

Обе снимают оспоримость, но **не** ничтожность: порок статьи 181.5 не лечится
ни несущественностью, ни подтверждением.

## Связь с договорным условием

Решение собрания попадает в договорный спор тогда, когда на нём держится
конкретное условие договора: размер платы, порядок её изменения, состав услуг.
Само по себе это отношение из модели не выводится — ни кворум, ни повестка не
говорят, легло ли решение в основание условия. Поэтому оно принимается как факт
дела (`meeting_decision_underpins_contract_term`) от рецензента, и уже из него
вместе с судьбой решения выводятся три вывода, которые уходят в слой общих
положений:

- **условие лишилось основания** — решение ничтожно (статья 181.5) или не
  принято (статья 181.2), поэтому требовать по такому условию нечего;
- **основание условия оспоримо** — решение оспоримо (статья 181.4): условие
  действует, пока суд не признал решение недействительным, но вывод по делу без
  человека принимать нельзя;
- **условие обязательно для всех участников** — решение действительно, и тогда
  условие связывает и тех, кто голосовал против или не участвовал
  (статья 181.1).

## Чего модель не делает

Не считает сроки оспаривания (шесть месяцев со дня, когда участник узнал или
должен был узнать, но не позднее двух лет со дня общедоступности сведений) — это
исчисление сроков и исковая давность, у них свои институты. Не оценивает
существенность неблагоприятных последствий: это принимается как факт от
рецензента, а не выводится. Не определяет, какое именно условие договора держится
на решении и о каком условии идёт спор: модель знает только, что такая связь
заявлена, поэтому вывод о нарушении она не отменяет, а поднимает дело человеку.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus

MEETING_DECISIONS_EVIDENCE_SCHEMA_VERSION = "contracts.meeting-decisions-evidence.v1"
MEETING_DECISIONS_MAPPING_VERSION = "contracts-reviewed-meeting-decisions-to-facts-v1"
MEETING_DECISIONS_MODEL_VERSION = "contracts-meeting-decisions-articles-1811-1815-v1"


class MeetingDecisionsEvidencePredicate(str, Enum):
    # Квалификация (статья 181.1 ГК РФ).
    MEETING_DECISION_ASSERTED = "meeting_decision_asserted"
    # Связь решения с договорным условием (дело 45-КГ23-2-К7).
    MEETING_DECISION_UNDERPINS_CONTRACT_TERM = "meeting_decision_underpins_contract_term"
    # Принятие решения (статья 181.2 ГК РФ).
    QUORUM_PRESENT = "quorum_present"
    REQUIRED_MAJORITY_OBTAINED = "required_majority_obtained"
    ALL_PARTICIPANTS_TOOK_PART = "all_participants_took_part"
    # Основания ничтожности (статья 181.5 ГК РФ).
    QUESTION_OUTSIDE_AGENDA = "question_outside_agenda"
    QUESTION_OUTSIDE_COMPETENCE = "question_outside_competence"
    CONTRARY_TO_PUBLIC_ORDER_OR_MORALITY = "contrary_to_public_order_or_morality"
    # Основания оспоримости (статья 181.4 ГК РФ).
    CONVOCATION_OR_CONDUCT_PROCEDURE_BREACHED = "convocation_or_conduct_procedure_breached"
    PARTICIPANT_EQUALITY_BREACHED = "participant_equality_breached"
    REPRESENTATIVE_AUTHORITY_DEFECT = "representative_authority_defect"
    MINUTES_REQUIREMENTS_BREACHED = "minutes_requirements_breached"
    # Оговорки, снимающие оспоримость (статья 181.4, пункты 2 и 4).
    VOTE_COULD_NOT_AFFECT_OUTCOME = "vote_could_not_affect_outcome"
    NO_MATERIAL_ADVERSE_CONSEQUENCES = "no_material_adverse_consequences"
    DECISION_CONFIRMED_BY_LATER_DECISION = "decision_confirmed_by_later_decision"


REQUIRED_MEETING_DECISIONS_PREDICATES = frozenset(MeetingDecisionsEvidencePredicate)


class MeetingDecisionsEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: MeetingDecisionsEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedMeetingDecisionsEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = MEETING_DECISIONS_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[MeetingDecisionsEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedMeetingDecisionsEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Meeting-decisions evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Meeting-decisions evidence contains duplicate legal source refs.")
        return self


class MeetingDecisionsFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    meeting_decision_asserted: bool
    meeting_decision_underpins_contract_term: bool
    quorum_present: bool
    required_majority_obtained: bool
    all_participants_took_part: bool
    question_outside_agenda: bool
    question_outside_competence: bool
    contrary_to_public_order_or_morality: bool
    convocation_or_conduct_procedure_breached: bool
    participant_equality_breached: bool
    representative_authority_defect: bool
    minutes_requirements_breached: bool
    vote_could_not_affect_outcome: bool
    no_material_adverse_consequences: bool
    decision_confirmed_by_later_decision: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "MeetingDecisionsFactSet":
        if self.all_participants_took_part and not self.quorum_present:
            raise ValueError(
                "Участие всех лиц в собрании означает наличие кворума: кворум не может "
                "отсутствовать при полном участии (статья 181.2 ГК РФ)."
            )
        if self.meeting_decision_underpins_contract_term and not self.meeting_decision_asserted:
            raise ValueError(
                "Условие договора не может держаться на решении собрания, которое в деле "
                "не заявлено (статья 181.1 ГК РФ)."
            )
        if self.decision_confirmed_by_later_decision and not self.meeting_decision_asserted:
            raise ValueError(
                "Подтверждение решения последующим решением предполагает, что решение "
                "собрания в деле заявлено (статья 181.4 ГК РФ)."
            )
        return self


class MeetingDecisionsFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class MeetingDecisionsEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: MeetingDecisionsFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[MeetingDecisionsFactProvenance] = Field(default_factory=list)


class MeetingDecisionsConstraintSet(BaseModel):
    id: str
    model_version: str = MEETING_DECISIONS_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class MeetingDecisionsEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    meeting_decision_qualified: bool
    # Отсутствие большинства — это отсутствие решения, а не его порок.
    decision_not_adopted: bool
    quorum_absent: bool
    agenda_violation_void: bool
    competence_violation_void: bool
    public_order_violation_void: bool
    # Ничтожность по статье 181.5: недействительно независимо от признания судом.
    decision_void: bool
    procedural_defect_established: bool
    voidability_cured_by_immateriality: bool
    voidability_cured_by_confirmation: bool
    # Оспоримость по статье 181.4: действует, пока не признано недействительным.
    decision_voidable: bool
    # Ключевой вывод: решение обязательно для всех, имевших право участвовать.
    decision_binds_all_participants: bool
    # Судьба договорного условия, которое держится на решении (дело 45-КГ23-2-К7).
    contract_term_lacks_meeting_basis: bool
    contract_term_basis_voidable: bool
    contract_term_binds_all_participants: bool
    requires_human_meeting_decision_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_meeting_decisions_evidence(
    evidence: ReviewedMeetingDecisionsEvidence,
) -> MeetingDecisionsEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Meeting-decisions evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Meeting-decisions evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_MEETING_DECISIONS_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed meeting-decisions evidence is incomplete; missing predicates: "
            + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value
        for predicate in REQUIRED_MEETING_DECISIONS_PREDICATES
    }
    return MeetingDecisionsEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=MEETING_DECISIONS_MAPPING_VERSION,
        facts=MeetingDecisionsFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            MeetingDecisionsFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(
                REQUIRED_MEETING_DECISIONS_PREDICATES, key=lambda item: item.value
            )
        ],
    )


def build_meeting_decisions_constraint_set(
    mapping: MeetingDecisionsEvidenceMappingResult,
) -> MeetingDecisionsConstraintSet:
    return MeetingDecisionsConstraintSet(
        id=f"meeting-decisions-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "meeting_decision_qualified == meeting_decision_asserted",
            "decision_not_adopted == meeting_decision_qualified AND NOT required_majority_obtained",
            "quorum_absent == meeting_decision_qualified AND NOT quorum_present",
            "agenda_violation_void == meeting_decision_qualified AND question_outside_agenda AND NOT all_participants_took_part",
            "competence_violation_void == meeting_decision_qualified AND question_outside_competence",
            "public_order_violation_void == meeting_decision_qualified AND contrary_to_public_order_or_morality",
            "decision_void == quorum_absent OR agenda_violation_void OR competence_violation_void OR public_order_violation_void",
            "procedural_defect_established == meeting_decision_qualified AND (convocation_or_conduct_procedure_breached OR participant_equality_breached OR representative_authority_defect OR minutes_requirements_breached)",
            "voidability_cured_by_immateriality == procedural_defect_established AND vote_could_not_affect_outcome AND no_material_adverse_consequences",
            "voidability_cured_by_confirmation == procedural_defect_established AND decision_confirmed_by_later_decision",
            "decision_voidable == procedural_defect_established AND NOT decision_void AND NOT voidability_cured_by_immateriality AND NOT voidability_cured_by_confirmation",
            "decision_binds_all_participants == meeting_decision_qualified AND NOT decision_void AND NOT decision_not_adopted",
            "contract_term_lacks_meeting_basis == meeting_decision_underpins_contract_term AND (decision_void OR decision_not_adopted)",
            "contract_term_basis_voidable == meeting_decision_underpins_contract_term AND decision_voidable AND NOT contract_term_lacks_meeting_basis",
            "contract_term_binds_all_participants == meeting_decision_underpins_contract_term AND decision_binds_all_participants",
            "requires_human_meeting_decision_assessment == decision_void OR decision_voidable OR decision_not_adopted OR voidability_cured_by_immateriality OR voidability_cured_by_confirmation OR contract_term_lacks_meeting_basis",
        ],
    )


def evaluate_meeting_decisions_constraints(
    constraint_set: MeetingDecisionsConstraintSet,
    facts: MeetingDecisionsFactSet,
) -> MeetingDecisionsEvaluation:
    variables = {
        field_name: Bool(field_name) for field_name in MeetingDecisionsFactSet.model_fields
    }
    meeting_decision_qualified = Bool("meeting_decision_qualified")
    decision_not_adopted = Bool("decision_not_adopted")
    quorum_absent = Bool("quorum_absent")
    agenda_violation_void = Bool("agenda_violation_void")
    competence_violation_void = Bool("competence_violation_void")
    public_order_violation_void = Bool("public_order_violation_void")
    decision_void = Bool("decision_void")
    procedural_defect_established = Bool("procedural_defect_established")
    voidability_cured_by_immateriality = Bool("voidability_cured_by_immateriality")
    voidability_cured_by_confirmation = Bool("voidability_cured_by_confirmation")
    decision_voidable = Bool("decision_voidable")
    decision_binds_all_participants = Bool("decision_binds_all_participants")
    contract_term_lacks_meeting_basis = Bool("contract_term_lacks_meeting_basis")
    contract_term_basis_voidable = Bool("contract_term_basis_voidable")
    contract_term_binds_all_participants = Bool("contract_term_binds_all_participants")
    requires_human_meeting_decision_assessment = Bool("requires_human_meeting_decision_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(meeting_decision_qualified == variables["meeting_decision_asserted"])
    solver.add(
        decision_not_adopted
        == And(meeting_decision_qualified, Not(variables["required_majority_obtained"]))
    )
    solver.add(quorum_absent == And(meeting_decision_qualified, Not(variables["quorum_present"])))
    solver.add(
        agenda_violation_void
        == And(
            meeting_decision_qualified,
            variables["question_outside_agenda"],
            Not(variables["all_participants_took_part"]),
        )
    )
    solver.add(
        competence_violation_void
        == And(meeting_decision_qualified, variables["question_outside_competence"])
    )
    solver.add(
        public_order_violation_void
        == And(meeting_decision_qualified, variables["contrary_to_public_order_or_morality"])
    )
    solver.add(
        decision_void
        == Or(
            quorum_absent,
            agenda_violation_void,
            competence_violation_void,
            public_order_violation_void,
        )
    )
    solver.add(
        procedural_defect_established
        == And(
            meeting_decision_qualified,
            Or(
                variables["convocation_or_conduct_procedure_breached"],
                variables["participant_equality_breached"],
                variables["representative_authority_defect"],
                variables["minutes_requirements_breached"],
            ),
        )
    )
    solver.add(
        voidability_cured_by_immateriality
        == And(
            procedural_defect_established,
            variables["vote_could_not_affect_outcome"],
            variables["no_material_adverse_consequences"],
        )
    )
    solver.add(
        voidability_cured_by_confirmation
        == And(procedural_defect_established, variables["decision_confirmed_by_later_decision"])
    )
    solver.add(
        decision_voidable
        == And(
            procedural_defect_established,
            Not(decision_void),
            Not(voidability_cured_by_immateriality),
            Not(voidability_cured_by_confirmation),
        )
    )
    solver.add(
        decision_binds_all_participants
        == And(meeting_decision_qualified, Not(decision_void), Not(decision_not_adopted))
    )
    # Условие договора, которое держится на решении собрания, разделяет его
    # судьбу: ничтожное решение (статья 181.5) и непринятое решение
    # (статья 181.2) оставляют условие без основания.
    solver.add(
        contract_term_lacks_meeting_basis
        == And(
            variables["meeting_decision_underpins_contract_term"],
            Or(decision_void, decision_not_adopted),
        )
    )
    # Оспоримое решение действует, пока суд не признал его недействительным
    # (статья 181.4), поэтому основание условия не отпадает, а становится
    # спорным. Ничтожность сильнее: там основания уже нет.
    solver.add(
        contract_term_basis_voidable
        == And(
            variables["meeting_decision_underpins_contract_term"],
            decision_voidable,
            Not(contract_term_lacks_meeting_basis),
        )
    )
    solver.add(
        contract_term_binds_all_participants
        == And(
            variables["meeting_decision_underpins_contract_term"],
            decision_binds_all_participants,
        )
    )
    solver.add(
        requires_human_meeting_decision_assessment
        == Or(
            decision_void,
            decision_voidable,
            decision_not_adopted,
            voidability_cured_by_immateriality,
            voidability_cured_by_confirmation,
            contract_term_lacks_meeting_basis,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return MeetingDecisionsEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            meeting_decision_qualified=False,
            decision_not_adopted=False,
            quorum_absent=False,
            agenda_violation_void=False,
            competence_violation_void=False,
            public_order_violation_void=False,
            decision_void=False,
            procedural_defect_established=False,
            voidability_cured_by_immateriality=False,
            voidability_cured_by_confirmation=False,
            decision_voidable=False,
            decision_binds_all_participants=False,
            contract_term_lacks_meeting_basis=False,
            contract_term_basis_voidable=False,
            contract_term_binds_all_participants=False,
            requires_human_meeting_decision_assessment=True,
            reasons_ru=["Набор фактов о решении собрания противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Заявлено решение собрания: оно порождает правовые последствия для всех лиц, "
            "имевших право участвовать в данном собрании, если принято в установленном "
            "порядке (статья 181.1 ГК РФ)."
            if truth(meeting_decision_qualified)
            else "Решение собрания в деле не заявлено."
        ),
    ]
    if truth(decision_not_adopted):
        reasons_ru.append(
            "Решение не принято: требуемое большинство голосов участников собрания не "
            "набрано. Это отсутствие решения, а не его порок (статья 181.2 ГК РФ)."
        )
    if truth(quorum_absent):
        reasons_ru.append(
            "Решение ничтожно: собрание было неправомочно, поскольку в нём приняли участие "
            "менее половины участников соответствующего гражданско-правового сообщества "
            "(статьи 181.2 и 181.5 ГК РФ)."
        )
    if truth(agenda_violation_void):
        reasons_ru.append(
            "Решение ничтожно: оно принято по вопросу, не включённому в повестку дня, при "
            "том что в собрании участвовали не все участники сообщества "
            "(статья 181.5 ГК РФ)."
        )
    if truth(competence_violation_void):
        reasons_ru.append(
            "Решение ничтожно: оно принято по вопросу, не относящемуся к компетенции "
            "собрания (статья 181.5 ГК РФ)."
        )
    if truth(public_order_violation_void):
        reasons_ru.append(
            "Решение ничтожно: оно противоречит основам правопорядка или нравственности "
            "(статья 181.5 ГК РФ)."
        )
    if truth(procedural_defect_established):
        reasons_ru.append(
            "Установлено нарушение порядка принятия решения: порядка созыва, подготовки или "
            "проведения собрания, равенства прав участников, полномочий лица, выступавшего "
            "от имени участника, либо правил составления протокола (статья 181.4 ГК РФ)."
        )
    if truth(voidability_cured_by_immateriality):
        reasons_ru.append(
            "Оспоримость снята: голос лица, обращающегося с иском, не мог повлиять на "
            "принятие решения, и решение не влечёт для этого лица существенных "
            "неблагоприятных последствий (статья 181.4 ГК РФ)."
        )
    if truth(voidability_cured_by_confirmation):
        reasons_ru.append(
            "Оспоримость снята: решение подтверждено последующим решением собрания, "
            "принятым до вынесения решения суда (статья 181.4 ГК РФ)."
        )
    if truth(decision_voidable):
        reasons_ru.append(
            "Решение оспоримо: оно может быть признано судом недействительным по "
            "установленному нарушению и действует, пока не признано недействительным "
            "(статья 181.4 ГК РФ)."
        )
    if truth(decision_binds_all_participants):
        reasons_ru.append(
            "Решение обязательно для всех лиц, имевших право участвовать в собрании, в том "
            "числе для голосовавших против и не участвовавших (статья 181.1 ГК РФ)."
        )
    if truth(contract_term_lacks_meeting_basis):
        reasons_ru.append(
            "Условие договора держится на решении собрания, которое ничтожно либо не "
            "принято, поэтому условие лишилось основания: недействительное решение "
            "недействительно с момента принятия независимо от признания судом, а "
            "непринятое решение правовых последствий не порождает "
            "(статьи 181.2, 181.3 и 181.5 ГК РФ)."
        )
    if truth(contract_term_basis_voidable):
        reasons_ru.append(
            "Основание договорного условия оспоримо: решение собрания, на котором условие "
            "держится, может быть признано судом недействительным, но до этого момента "
            "действует, поэтому условие сохраняет силу (статья 181.4 ГК РФ)."
        )
    if truth(contract_term_binds_all_participants):
        reasons_ru.append(
            "Условие договора, принятое решением собрания, обязательно для всех лиц, "
            "имевших право участвовать в собрании, и не может быть изменено в "
            "одностороннем порядке вопреки этому решению (статьи 181.1 и 181.3 ГК РФ)."
        )
    return MeetingDecisionsEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        meeting_decision_qualified=truth(meeting_decision_qualified),
        decision_not_adopted=truth(decision_not_adopted),
        quorum_absent=truth(quorum_absent),
        agenda_violation_void=truth(agenda_violation_void),
        competence_violation_void=truth(competence_violation_void),
        public_order_violation_void=truth(public_order_violation_void),
        decision_void=truth(decision_void),
        procedural_defect_established=truth(procedural_defect_established),
        voidability_cured_by_immateriality=truth(voidability_cured_by_immateriality),
        voidability_cured_by_confirmation=truth(voidability_cured_by_confirmation),
        decision_voidable=truth(decision_voidable),
        decision_binds_all_participants=truth(decision_binds_all_participants),
        contract_term_lacks_meeting_basis=truth(contract_term_lacks_meeting_basis),
        contract_term_basis_voidable=truth(contract_term_basis_voidable),
        contract_term_binds_all_participants=truth(contract_term_binds_all_participants),
        requires_human_meeting_decision_assessment=truth(
            requires_human_meeting_decision_assessment
        ),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель не исчисляет сроки оспаривания решения: шесть месяцев со дня, когда "
            "участник узнал или должен был узнать о нарушении своего права, но не позднее "
            "двух лет со дня общедоступности сведений о решении, проверяются институтами "
            "исчисления сроков и исковой давности (статья 181.4 ГК РФ).",
            "Существенность неблагоприятных последствий решения для участника и влияние "
            "его голоса на итог оцениваются экспертом и судом (статья 181.4 ГК РФ).",
            "Решение собрания не является сделкой: пороки главы 9.1 оцениваются по её "
            "правилам, а не по статьям 166–181 ГК РФ.",
        ],
    )
