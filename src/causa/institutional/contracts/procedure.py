from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


PROCEDURE_EVIDENCE_SCHEMA_VERSION = "contracts.procedure-evidence.v0"
PROCEDURE_MAPPING_VERSION = "contracts-reviewed-procedure-to-facts-v0"
PROCEDURE_MODEL_VERSION = "contracts-conclusion-procedure-articles-445-449-1-v0"


class ProcedureEvidencePredicate(str, Enum):
    # Заключение договора в обязательном порядке (статьи 445 и 446 ГК РФ).
    CONCLUSION_MANDATORY_FOR_PARTY = "conclusion_mandatory_for_party"
    OFFER_OR_DRAFT_SENT = "offer_or_draft_sent"
    OBLIGED_PARTY_EVADED = "obliged_party_evaded"
    PRECONTRACTUAL_DISPUTE_SUBMITTED_TO_COURT = "precontractual_dispute_submitted_to_court"
    # Заключение договора на торгах (статьи 447 и 448 ГК РФ).
    CONTRACT_CONCLUDED_AT_AUCTION = "contract_concluded_at_auction"
    AUCTION_NOTICE_TIMELY = "auction_notice_timely"
    WINNER_DETERMINED = "winner_determined"
    RESULTS_PROTOCOL_SIGNED = "results_protocol_signed"
    WINNER_EVADED_SIGNING = "winner_evaded_signing"
    # Недействительность торгов (статья 449 ГК РФ).
    AUCTION_RULES_VIOLATED = "auction_rules_violated"
    INTERESTED_PARTY_CHALLENGE = "interested_party_challenge"
    # Публичные торги в исполнительном производстве (статья 449.1 ГК РФ).
    PUBLIC_AUCTION_ASSERTED = "public_auction_asserted"
    PUBLIC_AUCTION_ORGANISER_AUTHORISED = "public_auction_organiser_authorised"
    PUBLIC_AUCTION_NOTICE_NAMES_OWNER = "public_auction_notice_names_owner"
    BARRED_PERSON_PARTICIPATED = "barred_person_participated"
    PUBLIC_AUCTION_PROTOCOL_LISTS_BIDS = "public_auction_protocol_lists_bids"


REQUIRED_PROCEDURE_PREDICATES = frozenset(ProcedureEvidencePredicate)


class ProcedureEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: ProcedureEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedProcedureEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = PROCEDURE_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[ProcedureEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedProcedureEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Procedure evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Procedure evidence contains duplicate legal source refs.")
        return self


class ProcedureFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    conclusion_mandatory_for_party: bool
    offer_or_draft_sent: bool
    obliged_party_evaded: bool
    precontractual_dispute_submitted_to_court: bool
    contract_concluded_at_auction: bool
    auction_notice_timely: bool
    winner_determined: bool
    results_protocol_signed: bool
    winner_evaded_signing: bool
    auction_rules_violated: bool
    interested_party_challenge: bool
    public_auction_asserted: bool
    public_auction_organiser_authorised: bool
    public_auction_notice_names_owner: bool
    barred_person_participated: bool
    public_auction_protocol_lists_bids: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "ProcedureFactSet":
        if self.winner_determined and not self.contract_concluded_at_auction:
            raise ValueError("Победитель не может быть определён без проведения торгов.")
        if self.results_protocol_signed and not self.winner_determined:
            raise ValueError("Протокол о результатах невозможен без определённого победителя.")
        if self.winner_evaded_signing and not self.winner_determined:
            raise ValueError("Уклонение победителя невозможно без определённого победителя.")
        if self.barred_person_participated and not self.public_auction_asserted:
            raise ValueError(
                "Запрет участия в торгах установлен статьёй 449.1 ГК РФ для публичных торгов; "
                "без заявленных публичных торгов он не применяется."
            )
        if self.public_auction_organiser_authorised and not self.public_auction_asserted:
            raise ValueError(
                "Полномочие организатора публичных торгов имеет смысл только для заявленных "
                "публичных торгов."
            )
        return self


class ProcedureFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class ProcedureEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: ProcedureFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[ProcedureFactProvenance] = Field(default_factory=list)


class ProcedureConstraintSet(BaseModel):
    id: str
    model_version: str = PROCEDURE_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class ProcedureEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    conclusion_compellable: bool
    precontractual_terms_set_by_court: bool
    damages_for_mandatory_evasion: bool
    auction_contract_formed: bool
    winner_liable_for_evasion: bool
    auction_voidable: bool
    auction_contract_invalid: bool
    public_auction_qualified: bool
    public_auction_organiser_defect: bool
    public_auction_notice_defect: bool
    public_auction_participation_ban_breached: bool
    public_auction_protocol_defect: bool
    # Нарушение правил именно публичных торгов: статья 449.1 называет их прямо,
    # тогда как общий предикат нарушения правил торгов модель принимает на веру.
    public_auction_rules_violated: bool
    requires_human_procedure_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_procedure_evidence(
    evidence: ReviewedProcedureEvidence,
) -> ProcedureEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Procedure evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Procedure evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_PROCEDURE_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed procedure evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_PROCEDURE_PREDICATES
    }
    return ProcedureEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=PROCEDURE_MAPPING_VERSION,
        facts=ProcedureFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            ProcedureFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_PROCEDURE_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_procedure_constraint_set(
    mapping: ProcedureEvidenceMappingResult,
) -> ProcedureConstraintSet:
    return ProcedureConstraintSet(
        id=f"procedure-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "conclusion_compellable == conclusion_mandatory_for_party AND offer_or_draft_sent AND obliged_party_evaded",
            "precontractual_terms_set_by_court == precontractual_dispute_submitted_to_court",
            "damages_for_mandatory_evasion == conclusion_mandatory_for_party AND obliged_party_evaded",
            "auction_contract_formed == contract_concluded_at_auction AND winner_determined AND results_protocol_signed",
            "winner_liable_for_evasion == winner_determined AND winner_evaded_signing",
            "public_auction_qualified == contract_concluded_at_auction AND public_auction_asserted",
            "public_auction_organiser_defect == public_auction_qualified AND NOT public_auction_organiser_authorised",
            "public_auction_notice_defect == public_auction_qualified AND NOT public_auction_notice_names_owner",
            "public_auction_participation_ban_breached == public_auction_qualified AND barred_person_participated",
            "public_auction_protocol_defect == public_auction_qualified AND NOT public_auction_protocol_lists_bids",
            "public_auction_rules_violated == public_auction_organiser_defect OR public_auction_notice_defect OR public_auction_participation_ban_breached OR public_auction_protocol_defect",
            "auction_voidable == (auction_rules_violated OR public_auction_rules_violated) AND interested_party_challenge",
            "auction_contract_invalid == (auction_rules_violated OR public_auction_rules_violated) AND interested_party_challenge",
            "requires_human_procedure_assessment == precontractual_dispute_submitted_to_court OR (conclusion_mandatory_for_party AND obliged_party_evaded) OR winner_evaded_signing OR ((auction_rules_violated OR public_auction_rules_violated) AND interested_party_challenge) OR public_auction_qualified",
        ],
    )


def evaluate_procedure_constraints(
    constraint_set: ProcedureConstraintSet,
    facts: ProcedureFactSet,
) -> ProcedureEvaluation:
    variables = {field_name: Bool(field_name) for field_name in ProcedureFactSet.model_fields}
    conclusion_compellable = Bool("conclusion_compellable")
    precontractual_terms_set_by_court = Bool("precontractual_terms_set_by_court")
    damages_for_mandatory_evasion = Bool("damages_for_mandatory_evasion")
    auction_contract_formed = Bool("auction_contract_formed")
    winner_liable_for_evasion = Bool("winner_liable_for_evasion")
    auction_voidable = Bool("auction_voidable")
    auction_contract_invalid = Bool("auction_contract_invalid")
    public_auction_qualified = Bool("public_auction_qualified")
    public_auction_organiser_defect = Bool("public_auction_organiser_defect")
    public_auction_notice_defect = Bool("public_auction_notice_defect")
    public_auction_participation_ban_breached = Bool("public_auction_participation_ban_breached")
    public_auction_protocol_defect = Bool("public_auction_protocol_defect")
    public_auction_rules_violated = Bool("public_auction_rules_violated")
    requires_human_procedure_assessment = Bool("requires_human_procedure_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        conclusion_compellable
        == And(
            variables["conclusion_mandatory_for_party"],
            variables["offer_or_draft_sent"],
            variables["obliged_party_evaded"],
        )
    )
    solver.add(
        precontractual_terms_set_by_court == variables["precontractual_dispute_submitted_to_court"]
    )
    solver.add(
        damages_for_mandatory_evasion
        == And(
            variables["conclusion_mandatory_for_party"],
            variables["obliged_party_evaded"],
        )
    )
    solver.add(
        auction_contract_formed
        == And(
            variables["contract_concluded_at_auction"],
            variables["winner_determined"],
            variables["results_protocol_signed"],
        )
    )
    solver.add(
        winner_liable_for_evasion
        == And(variables["winner_determined"], variables["winner_evaded_signing"])
    )
    solver.add(
        public_auction_qualified
        == And(
            variables["contract_concluded_at_auction"],
            variables["public_auction_asserted"],
        )
    )
    solver.add(
        public_auction_organiser_defect
        == And(
            public_auction_qualified,
            Not(variables["public_auction_organiser_authorised"]),
        )
    )
    solver.add(
        public_auction_notice_defect
        == And(
            public_auction_qualified,
            Not(variables["public_auction_notice_names_owner"]),
        )
    )
    solver.add(
        public_auction_participation_ban_breached
        == And(public_auction_qualified, variables["barred_person_participated"])
    )
    solver.add(
        public_auction_protocol_defect
        == And(
            public_auction_qualified,
            Not(variables["public_auction_protocol_lists_bids"]),
        )
    )
    solver.add(
        public_auction_rules_violated
        == Or(
            public_auction_organiser_defect,
            public_auction_notice_defect,
            public_auction_participation_ban_breached,
            public_auction_protocol_defect,
        )
    )
    solver.add(
        auction_voidable
        == And(
            Or(variables["auction_rules_violated"], public_auction_rules_violated),
            variables["interested_party_challenge"],
        )
    )
    solver.add(
        auction_contract_invalid
        == And(
            Or(variables["auction_rules_violated"], public_auction_rules_violated),
            variables["interested_party_challenge"],
        )
    )
    solver.add(
        requires_human_procedure_assessment
        == Or(
            variables["precontractual_dispute_submitted_to_court"],
            And(
                variables["conclusion_mandatory_for_party"],
                variables["obliged_party_evaded"],
            ),
            variables["winner_evaded_signing"],
            And(
                Or(variables["auction_rules_violated"], public_auction_rules_violated),
                variables["interested_party_challenge"],
            ),
            public_auction_qualified,
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return ProcedureEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            conclusion_compellable=False,
            precontractual_terms_set_by_court=False,
            damages_for_mandatory_evasion=False,
            auction_contract_formed=False,
            winner_liable_for_evasion=False,
            auction_voidable=False,
            auction_contract_invalid=False,
            public_auction_qualified=False,
            public_auction_organiser_defect=False,
            public_auction_notice_defect=False,
            public_auction_participation_ban_breached=False,
            public_auction_protocol_defect=False,
            public_auction_rules_violated=False,
            requires_human_procedure_assessment=True,
            reasons_ru=["Набор фактов о порядке заключения договора противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = []
    if truth(conclusion_compellable):
        reasons_ru.append(
            "Сторона, для которой заключение договора обязательно и которая уклоняется, "
            "может быть понуждена к заключению по суду (пункт 4 статьи 445 ГК РФ)."
        )
    if truth(precontractual_terms_set_by_court):
        reasons_ru.append(
            "Разногласия по договору переданы на рассмотрение суда; спорные условия "
            "определяются решением суда (статья 446 ГК РФ)."
        )
    if truth(damages_for_mandatory_evasion):
        reasons_ru.append(
            "Уклонение обязанной стороны от заключения договора влечёт возмещение "
            "причинённых этим убытков (пункт 4 статьи 445 ГК РФ)."
        )
    if truth(auction_contract_formed):
        reasons_ru.append(
            "Договор на торгах заключается с лицом, выигравшим торги, путём подписания "
            "протокола о результатах (статьи 447 и 448 ГК РФ)."
        )
    if truth(winner_liable_for_evasion):
        reasons_ru.append(
            "Уклонение победителя от подписания протокола влечёт установленные "
            "последствия, включая утрату задатка (пункт 6 статьи 448 ГК РФ)."
        )
    if truth(auction_voidable):
        reasons_ru.append(
            "Торги, проведённые с нарушением установленных правил, могут быть признаны "
            "судом недействительными по иску заинтересованного лица; это влечёт "
            "недействительность договора (статья 449 ГК РФ)."
        )
    if truth(public_auction_qualified):
        reasons_ru.append(
            "Торги квалифицированы как публичные: они проводятся в целях исполнения решения "
            "суда или исполнительных документов в порядке исполнительного производства. "
            "Правила статей 448 и 449 применяются к ним субсидиарно — если иное не "
            "установлено Кодексом и процессуальным законодательством (пункт 1 статьи 449.1 "
            "ГК РФ)."
        )
    if truth(public_auction_organiser_defect):
        reasons_ru.append(
            "Организатор публичных торгов не уполномочен отчуждать имущество в порядке "
            "исполнительного производства (пункт 2 статьи 449.1 ГК РФ)."
        )
    if truth(public_auction_notice_defect):
        reasons_ru.append(
            "Извещение о публичных торгах не отвечает требованиям: помимо сведений пункта 2 "
            "статьи 448 ГК РФ оно должно указывать собственника имущества и размещаться на "
            "сайте органа, осуществляющего исполнительное производство (пункт 4 статьи 449.1 "
            "ГК РФ)."
        )
    if truth(public_auction_participation_ban_breached):
        reasons_ru.append(
            "Нарушен запрет участия в публичных торгах: в них не могут участвовать должник, "
            "организации, на которые возложены оценка и реализация его имущества, и их "
            "работники, должностные лица органов власти, чьё участие может повлиять на условия "
            "и результаты торгов, а также члены семей этих лиц (пункт 5 статьи 449.1 ГК РФ)."
        )
    if truth(public_auction_protocol_defect):
        reasons_ru.append(
            "Протокол о результатах публичных торгов не содержит всех участников и внесённых "
            "ими предложений о цене (пункт 6 статьи 449.1 ГК РФ)."
        )
    if not reasons_ru:
        reasons_ru.append(
            "Формальные предпосылки понуждения к заключению или недействительности "
            "торгов не подтверждены."
        )
    return ProcedureEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        conclusion_compellable=truth(conclusion_compellable),
        precontractual_terms_set_by_court=truth(precontractual_terms_set_by_court),
        damages_for_mandatory_evasion=truth(damages_for_mandatory_evasion),
        auction_contract_formed=truth(auction_contract_formed),
        winner_liable_for_evasion=truth(winner_liable_for_evasion),
        auction_voidable=truth(auction_voidable),
        auction_contract_invalid=truth(auction_contract_invalid),
        public_auction_qualified=truth(public_auction_qualified),
        public_auction_organiser_defect=truth(public_auction_organiser_defect),
        public_auction_notice_defect=truth(public_auction_notice_defect),
        public_auction_participation_ban_breached=truth(public_auction_participation_ban_breached),
        public_auction_protocol_defect=truth(public_auction_protocol_defect),
        public_auction_rules_violated=truth(public_auction_rules_violated),
        requires_human_procedure_assessment=truth(requires_human_procedure_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о заключении договора в "
            "обязательном порядке и на торгах и не заменяет судебную оценку.",
            "Обязательность заключения, соблюдение правил торгов и размер убытков "
            "оцениваются экспертом и судом.",
            "Для публичных торгов модель проверяет прямо названные статьёй 449.1 ГК РФ "
            "требования — полномочие организатора, содержание извещения, запрет участия и "
            "состав протокола. Иные нарушения порядка исполнительного производства она "
            "принимает через общий предикат нарушения правил торгов.",
        ],
    )
