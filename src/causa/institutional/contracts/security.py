from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


SECURITY_EVIDENCE_SCHEMA_VERSION = "contracts.security-evidence.v0"
SECURITY_MAPPING_VERSION = "contracts-reviewed-security-to-facts-v0"
SECURITY_MODEL_VERSION = "contracts-performance-security-articles-329-3812-v0"


class SecurityEvidencePredicate(str, Enum):
    MAIN_OBLIGATION_EXISTS = "main_obligation_exists"
    MAIN_OBLIGATION_BREACHED = "main_obligation_breached"
    MAIN_OBLIGATION_INVALID = "main_obligation_invalid"
    SECURED_AMOUNT_PROVEN = "secured_amount_proven"
    CREDITOR_DEMAND_MADE = "creditor_demand_made"
    CREDITOR_GOOD_FAITH = "creditor_good_faith"
    PENALTY_AGREED = "penalty_agreed"
    PENALTY_WRITING_OBSERVED = "penalty_writing_observed"
    PENALTY_TRIGGER_OCCURRED = "penalty_trigger_occurred"
    PLEDGE_CREATED = "pledge_created"
    PLEDGE_FORM_OBSERVED = "pledge_form_observed"
    PLEDGED_ASSET_IDENTIFIED = "pledged_asset_identified"
    PLEDGOR_OWNS_OR_AUTHORIZED = "pledgor_owns_or_authorized"
    PLEDGE_REGISTRATION_REQUIRED = "pledge_registration_required"
    PLEDGE_REGISTRATION_COMPLETED = "pledge_registration_completed"
    THIRD_PARTY_KNEW_PLEDGE = "third_party_knew_pledge"
    FORECLOSURE_GROUND_EXISTS = "foreclosure_ground_exists"
    BREACH_INSIGNIFICANT = "breach_insignificant"
    SECURED_CLAIM_MANIFESTLY_DISPROPORTIONATE = "secured_claim_manifestly_disproportionate"
    EXTRAJUDICIAL_FORECLOSURE_AGREED = "extrajudicial_foreclosure_agreed"
    EXTRAJUDICIAL_FORM_OBSERVED = "extrajudicial_form_observed"
    JUDICIAL_FORECLOSURE_MANDATORY = "judicial_foreclosure_mandatory"
    FORECLOSURE_NOTICE_DELIVERED = "foreclosure_notice_delivered"
    ASSET_LAWFULLY_IN_CREDITOR_POSSESSION = "asset_lawfully_in_creditor_possession"
    ASSET_RETURN_DUE = "asset_return_due"
    RETENTION_SECURED_CLAIM_DUE = "retention_secured_claim_due"
    CLAIM_RELATED_TO_ASSET = "claim_related_to_asset"
    PARTIES_ACTING_IN_BUSINESS = "parties_acting_in_business"
    SURETYSHIP_CREATED = "suretyship_created"
    SURETYSHIP_WRITING_OBSERVED = "suretyship_writing_observed"
    SURETY_SCOPE_PROVEN = "surety_scope_proven"
    SURETY_SUBSIDIARY_AGREED = "surety_subsidiary_agreed"
    SURETY_TERM_EXPIRED = "surety_term_expired"
    OBLIGATION_CHANGED_INCREASES_SURETY = "obligation_changed_increases_surety"
    SURETY_CONSENTED_TO_CHANGE = "surety_consented_to_change"
    DEBT_TRANSFERRED = "debt_transferred"
    SURETY_CONSENTED_TO_NEW_DEBTOR = "surety_consented_to_new_debtor"
    CREDITOR_REFUSED_PROPER_PERFORMANCE = "creditor_refused_proper_performance"
    SURETY_PERFORMED = "surety_performed"
    INDEPENDENT_GUARANTEE_ISSUED = "independent_guarantee_issued"
    GUARANTOR_ELIGIBLE = "guarantor_eligible"
    GUARANTEE_REPRODUCIBLE_FORM = "guarantee_reproducible_form"
    GUARANTEE_ESSENTIAL_TERMS_IDENTIFIABLE = "guarantee_essential_terms_identifiable"
    GUARANTEE_DEMAND_TIMELY = "guarantee_demand_timely"
    GUARANTEE_DEMAND_COMPLIES = "guarantee_demand_complies"
    GUARANTEE_EXPIRED = "guarantee_expired"
    GUARANTEE_PAYMENT_MADE = "guarantee_payment_made"
    BENEFICIARY_ABUSE_PROVEN = "beneficiary_abuse_proven"
    PAYMENT_TRANSFERRED_AT_CONCLUSION = "payment_transferred_at_conclusion"
    PAYMENT_IDENTIFIED_AS_DEPOSIT_IN_WRITING = "payment_identified_as_deposit_in_writing"
    DEPOSIT_NATURE_DOUBTFUL = "deposit_nature_doubtful"
    PERFORMANCE_IMPOSSIBLE_WITHOUT_FAULT = "performance_impossible_without_fault"
    AGREEMENT_TERMINATED_BEFORE_PERFORMANCE = "agreement_terminated_before_performance"
    DEPOSIT_GIVER_RESPONSIBLE = "deposit_giver_responsible"
    DEPOSIT_RECIPIENT_RESPONSIBLE = "deposit_recipient_responsible"
    SECURITY_PAYMENT_AGREED = "security_payment_agreed"
    SECURITY_PAYMENT_FUNDED = "security_payment_funded"
    SECURED_CIRCUMSTANCE_OCCURRED = "secured_circumstance_occurred"
    SECURITY_PAYMENT_CREDITED = "security_payment_credited"
    SECURITY_PAYMENT_RETURN_CONDITION_OCCURRED = "security_payment_return_condition_occurred"


REQUIRED_SECURITY_PREDICATES = frozenset(SecurityEvidencePredicate)


class SecurityEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: SecurityEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedSecurityEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = SECURITY_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[SecurityEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=3)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedSecurityEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Security evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Security evidence contains duplicate legal source refs.")
        return self


class SecurityFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    main_obligation_exists: bool
    main_obligation_breached: bool
    main_obligation_invalid: bool
    secured_amount_proven: bool
    creditor_demand_made: bool
    creditor_good_faith: bool
    penalty_agreed: bool
    penalty_writing_observed: bool
    penalty_trigger_occurred: bool
    pledge_created: bool
    pledge_form_observed: bool
    pledged_asset_identified: bool
    pledgor_owns_or_authorized: bool
    pledge_registration_required: bool
    pledge_registration_completed: bool
    third_party_knew_pledge: bool
    foreclosure_ground_exists: bool
    breach_insignificant: bool
    secured_claim_manifestly_disproportionate: bool
    extrajudicial_foreclosure_agreed: bool
    extrajudicial_form_observed: bool
    judicial_foreclosure_mandatory: bool
    foreclosure_notice_delivered: bool
    asset_lawfully_in_creditor_possession: bool
    asset_return_due: bool
    retention_secured_claim_due: bool
    claim_related_to_asset: bool
    parties_acting_in_business: bool
    suretyship_created: bool
    suretyship_writing_observed: bool
    surety_scope_proven: bool
    surety_subsidiary_agreed: bool
    surety_term_expired: bool
    obligation_changed_increases_surety: bool
    surety_consented_to_change: bool
    debt_transferred: bool
    surety_consented_to_new_debtor: bool
    creditor_refused_proper_performance: bool
    surety_performed: bool
    independent_guarantee_issued: bool
    guarantor_eligible: bool
    guarantee_reproducible_form: bool
    guarantee_essential_terms_identifiable: bool
    guarantee_demand_timely: bool
    guarantee_demand_complies: bool
    guarantee_expired: bool
    guarantee_payment_made: bool
    beneficiary_abuse_proven: bool
    payment_transferred_at_conclusion: bool
    payment_identified_as_deposit_in_writing: bool
    deposit_nature_doubtful: bool
    performance_impossible_without_fault: bool
    agreement_terminated_before_performance: bool
    deposit_giver_responsible: bool
    deposit_recipient_responsible: bool
    security_payment_agreed: bool
    security_payment_funded: bool
    secured_circumstance_occurred: bool
    security_payment_credited: bool
    security_payment_return_condition_occurred: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "SecurityFactSet":
        if self.main_obligation_breached and not self.main_obligation_exists:
            raise ValueError("A breached main obligation must exist.")
        if self.main_obligation_invalid and not self.main_obligation_exists:
            raise ValueError("An invalid main obligation must be identified as existing.")
        if self.penalty_writing_observed and not self.penalty_agreed:
            raise ValueError("Penalty writing requires an agreed penalty.")
        pledge_dependents = (
            self.pledge_form_observed,
            self.pledged_asset_identified,
            self.pledgor_owns_or_authorized,
            self.pledge_registration_required,
            self.pledge_registration_completed,
            self.third_party_knew_pledge,
            self.foreclosure_ground_exists,
            self.extrajudicial_foreclosure_agreed,
            self.judicial_foreclosure_mandatory,
        )
        if any(pledge_dependents) and not self.pledge_created:
            raise ValueError("Pledge facts require a created pledge.")
        if self.extrajudicial_form_observed and not self.extrajudicial_foreclosure_agreed:
            raise ValueError("Extrajudicial form requires an extrajudicial agreement.")
        if self.foreclosure_notice_delivered and not self.extrajudicial_foreclosure_agreed:
            raise ValueError("Foreclosure notice requires an extrajudicial agreement.")
        if self.suretyship_writing_observed and not self.suretyship_created:
            raise ValueError("Suretyship writing requires a created suretyship.")
        if self.surety_scope_proven and not self.suretyship_created:
            raise ValueError("Surety scope requires a created suretyship.")
        if self.surety_consented_to_change and not self.obligation_changed_increases_surety:
            raise ValueError("Surety consent to change requires an increased surety burden.")
        if self.surety_consented_to_new_debtor and not self.debt_transferred:
            raise ValueError("Surety consent to a debtor requires a debt transfer.")
        if self.surety_performed and not self.suretyship_created:
            raise ValueError("Surety performance requires a created suretyship.")
        guarantee_dependents = (
            self.guarantor_eligible,
            self.guarantee_reproducible_form,
            self.guarantee_essential_terms_identifiable,
            self.guarantee_demand_timely,
            self.guarantee_demand_complies,
            self.guarantee_expired,
            self.guarantee_payment_made,
            self.beneficiary_abuse_proven,
        )
        if any(guarantee_dependents) and not self.independent_guarantee_issued:
            raise ValueError("Guarantee facts require an issued independent guarantee.")
        if (
            self.payment_identified_as_deposit_in_writing or self.deposit_nature_doubtful
        ) and not self.payment_transferred_at_conclusion:
            raise ValueError("Deposit characterization requires a transferred payment.")
        if self.deposit_giver_responsible and self.deposit_recipient_responsible:
            raise ValueError("Both deposit parties cannot be solely responsible.")
        if self.security_payment_funded and not self.security_payment_agreed:
            raise ValueError("Security payment funding requires an agreement.")
        if self.security_payment_credited and not (
            self.security_payment_funded and self.secured_circumstance_occurred
        ):
            raise ValueError("Security payment credit requires funding and a secured event.")
        if self.security_payment_return_condition_occurred and not self.security_payment_agreed:
            raise ValueError("Security payment return requires an agreement.")
        return self


class SecurityFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class SecurityEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: SecurityFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[SecurityFactProvenance] = Field(default_factory=list)


class SecurityConstraintSet(BaseModel):
    id: str
    model_version: str = SECURITY_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class SecurityEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    accessory_security_displaced_by_main_invalidity: bool
    penalty_security_enforceable: bool
    pledge_valid_between_parties: bool
    pledge_opposable_to_third_parties: bool
    pledge_foreclosure_bar: bool
    pledge_foreclosure_prerequisites: bool
    pledge_judicial_route: bool
    pledge_extrajudicial_route: bool
    retention_available: bool
    retention_enforcement_issue: bool
    surety_enforceable: bool
    surety_terminated: bool
    surety_scope_change_excluded: bool
    surety_solidary_liability: bool
    surety_subsidiary_liability: bool
    surety_regress_issue: bool
    guarantee_formally_effective: bool
    guarantee_demand_payable: bool
    guarantee_refusal_ground: bool
    guarantee_survives_main_invalidity: bool
    guarantee_regress_issue: bool
    deposit_proven: bool
    payment_treated_as_advance: bool
    deposit_retained: bool
    deposit_return_single: bool
    deposit_return_double: bool
    deposit_losses_issue: bool
    security_payment_active: bool
    security_payment_credit_available: bool
    security_payment_return_issue: bool
    security_mechanism_detected: bool
    security_enforcement_available: bool
    competing_security_paths: bool
    main_obligation_unaffected_by_security_defect: bool
    requires_human_security_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_security_evidence(
    evidence: ReviewedSecurityEvidence,
) -> SecurityEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Security evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Security evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_SECURITY_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed security evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_SECURITY_PREDICATES
    }
    return SecurityEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=SECURITY_MAPPING_VERSION,
        facts=SecurityFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            SecurityFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_SECURITY_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_security_constraint_set(
    mapping: SecurityEvidenceMappingResult,
) -> SecurityConstraintSet:
    return SecurityConstraintSet(
        id=f"security-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "accessory_security_displaced_by_main_invalidity == main_obligation_invalid AND accessory_security_created",
            "penalty_security_enforceable == valid_main_obligation AND breach AND written_penalty AND trigger",
            "pledge_valid_between_parties == valid_main_obligation AND pledge_created AND form AND asset AND authority",
            "pledge_opposable_to_third_parties == pledge_valid_between_parties AND (NOT registration_required OR registration_completed OR third_party_knew)",
            "pledge_foreclosure_bar == breach_insignificant AND secured_claim_manifestly_disproportionate",
            "pledge_foreclosure_prerequisites == pledge_valid_between_parties AND breach AND foreclosure_ground AND amount_proven AND NOT bar",
            "pledge_extrajudicial_route == foreclosure_prerequisites AND agreement AND form AND notice AND NOT judicial_mandatory",
            "retention_available == lawful_possession AND return_due AND claim_due AND (claim_related_to_asset OR parties_acting_in_business)",
            "surety_enforceable == valid_main_obligation AND written_surety AND scope AND NOT terminated",
            "guarantee_demand_payable == effective_independent_guarantee AND timely_compliant_demand AND NOT abuse",
            "deposit_proven == transferred_payment AND written_deposit AND NOT doubt",
            "security_payment_credit_available == active_security_payment AND secured_event",
            "security_enforcement_available == OR(enforceable mechanism outputs)",
        ],
    )


def evaluate_security_constraints(
    constraint_set: SecurityConstraintSet,
    facts: SecurityFactSet,
) -> SecurityEvaluation:
    variables = {field_name: Bool(field_name) for field_name in SecurityFactSet.model_fields}
    outputs = {
        field_name: Bool(field_name)
        for field_name in SecurityEvaluation.model_fields
        if field_name not in {"constraint_set_id", "satisfiable", "reasons_ru", "warnings_ru"}
    }
    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))

    valid_main = And(variables["main_obligation_exists"], Not(variables["main_obligation_invalid"]))
    accessory_created = Or(
        variables["penalty_agreed"],
        variables["pledge_created"],
        variables["suretyship_created"],
        And(
            variables["payment_transferred_at_conclusion"],
            variables["payment_identified_as_deposit_in_writing"],
            Not(variables["deposit_nature_doubtful"]),
        ),
        variables["security_payment_agreed"],
    )
    solver.add(
        outputs["accessory_security_displaced_by_main_invalidity"]
        == And(variables["main_obligation_invalid"], accessory_created)
    )
    solver.add(
        outputs["penalty_security_enforceable"]
        == And(
            valid_main,
            variables["main_obligation_breached"],
            variables["penalty_agreed"],
            variables["penalty_writing_observed"],
            variables["penalty_trigger_occurred"],
        )
    )
    solver.add(
        outputs["pledge_valid_between_parties"]
        == And(
            valid_main,
            variables["pledge_created"],
            variables["pledge_form_observed"],
            variables["pledged_asset_identified"],
            variables["pledgor_owns_or_authorized"],
        )
    )
    solver.add(
        outputs["pledge_opposable_to_third_parties"]
        == And(
            outputs["pledge_valid_between_parties"],
            Or(
                Not(variables["pledge_registration_required"]),
                variables["pledge_registration_completed"],
                variables["third_party_knew_pledge"],
            ),
        )
    )
    solver.add(
        outputs["pledge_foreclosure_bar"]
        == And(
            variables["breach_insignificant"],
            variables["secured_claim_manifestly_disproportionate"],
        )
    )
    solver.add(
        outputs["pledge_foreclosure_prerequisites"]
        == And(
            outputs["pledge_valid_between_parties"],
            variables["main_obligation_breached"],
            variables["foreclosure_ground_exists"],
            variables["secured_amount_proven"],
            Not(outputs["pledge_foreclosure_bar"]),
        )
    )
    solver.add(
        outputs["pledge_extrajudicial_route"]
        == And(
            outputs["pledge_foreclosure_prerequisites"],
            variables["extrajudicial_foreclosure_agreed"],
            variables["extrajudicial_form_observed"],
            variables["foreclosure_notice_delivered"],
            Not(variables["judicial_foreclosure_mandatory"]),
        )
    )
    solver.add(
        outputs["pledge_judicial_route"]
        == And(
            outputs["pledge_foreclosure_prerequisites"],
            Or(
                variables["judicial_foreclosure_mandatory"],
                Not(outputs["pledge_extrajudicial_route"]),
            ),
        )
    )
    solver.add(
        outputs["retention_available"]
        == And(
            valid_main,
            variables["asset_lawfully_in_creditor_possession"],
            variables["asset_return_due"],
            variables["retention_secured_claim_due"],
            Or(
                variables["claim_related_to_asset"],
                variables["parties_acting_in_business"],
            ),
        )
    )
    solver.add(
        outputs["retention_enforcement_issue"]
        == And(outputs["retention_available"], variables["creditor_demand_made"])
    )
    solver.add(
        outputs["surety_terminated"]
        == And(
            variables["suretyship_created"],
            Or(
                variables["surety_term_expired"],
                variables["creditor_refused_proper_performance"],
                And(
                    variables["debt_transferred"],
                    Not(variables["surety_consented_to_new_debtor"]),
                ),
            ),
        )
    )
    solver.add(
        outputs["surety_scope_change_excluded"]
        == And(
            variables["suretyship_created"],
            variables["obligation_changed_increases_surety"],
            Not(variables["surety_consented_to_change"]),
        )
    )
    solver.add(
        outputs["surety_enforceable"]
        == And(
            valid_main,
            variables["main_obligation_breached"],
            variables["suretyship_created"],
            variables["suretyship_writing_observed"],
            variables["surety_scope_proven"],
            Not(outputs["surety_terminated"]),
        )
    )
    solver.add(
        outputs["surety_subsidiary_liability"]
        == And(outputs["surety_enforceable"], variables["surety_subsidiary_agreed"])
    )
    solver.add(
        outputs["surety_solidary_liability"]
        == And(outputs["surety_enforceable"], Not(variables["surety_subsidiary_agreed"]))
    )
    solver.add(
        outputs["surety_regress_issue"]
        == And(variables["surety_performed"], variables["main_obligation_exists"])
    )
    solver.add(
        outputs["guarantee_formally_effective"]
        == And(
            variables["independent_guarantee_issued"],
            variables["guarantor_eligible"],
            variables["guarantee_reproducible_form"],
            variables["guarantee_essential_terms_identifiable"],
            Not(variables["guarantee_expired"]),
        )
    )
    solver.add(
        outputs["guarantee_demand_payable"]
        == And(
            outputs["guarantee_formally_effective"],
            variables["creditor_demand_made"],
            variables["guarantee_demand_timely"],
            variables["guarantee_demand_complies"],
            Not(variables["beneficiary_abuse_proven"]),
        )
    )
    solver.add(
        outputs["guarantee_refusal_ground"]
        == And(
            variables["independent_guarantee_issued"],
            variables["creditor_demand_made"],
            Or(
                variables["guarantee_expired"],
                Not(variables["guarantee_demand_timely"]),
                Not(variables["guarantee_demand_complies"]),
                variables["beneficiary_abuse_proven"],
            ),
        )
    )
    solver.add(
        outputs["guarantee_survives_main_invalidity"]
        == And(outputs["guarantee_formally_effective"], variables["main_obligation_invalid"])
    )
    solver.add(
        outputs["guarantee_regress_issue"]
        == And(variables["guarantee_payment_made"], variables["main_obligation_exists"])
    )
    solver.add(
        outputs["deposit_proven"]
        == And(
            variables["payment_transferred_at_conclusion"],
            variables["payment_identified_as_deposit_in_writing"],
            Not(variables["deposit_nature_doubtful"]),
        )
    )
    solver.add(
        outputs["payment_treated_as_advance"]
        == And(
            variables["payment_transferred_at_conclusion"],
            Not(outputs["deposit_proven"]),
        )
    )
    solver.add(
        outputs["deposit_retained"]
        == And(
            valid_main,
            outputs["deposit_proven"],
            variables["deposit_giver_responsible"],
        )
    )
    solver.add(
        outputs["deposit_return_single"]
        == And(
            outputs["deposit_proven"],
            valid_main,
            Or(
                variables["performance_impossible_without_fault"],
                variables["agreement_terminated_before_performance"],
            ),
        )
    )
    solver.add(
        outputs["deposit_return_double"]
        == And(
            valid_main,
            outputs["deposit_proven"],
            variables["deposit_recipient_responsible"],
        )
    )
    solver.add(
        outputs["deposit_losses_issue"]
        == And(
            outputs["deposit_proven"],
            valid_main,
            Or(
                variables["deposit_giver_responsible"],
                variables["deposit_recipient_responsible"],
            ),
        )
    )
    solver.add(
        outputs["security_payment_active"]
        == And(
            valid_main,
            variables["security_payment_agreed"],
            variables["security_payment_funded"],
        )
    )
    solver.add(
        outputs["security_payment_credit_available"]
        == And(
            outputs["security_payment_active"],
            variables["secured_circumstance_occurred"],
            Not(variables["security_payment_credited"]),
        )
    )
    solver.add(
        outputs["security_payment_return_issue"]
        == And(
            valid_main,
            variables["security_payment_funded"],
            variables["security_payment_return_condition_occurred"],
            Not(variables["security_payment_credited"]),
        )
    )
    mechanisms = [
        outputs["penalty_security_enforceable"],
        outputs["pledge_valid_between_parties"],
        outputs["retention_available"],
        outputs["surety_enforceable"],
        outputs["guarantee_formally_effective"],
        outputs["deposit_proven"],
        outputs["security_payment_active"],
    ]
    solver.add(outputs["security_mechanism_detected"] == Or(*mechanisms))
    enforceable_paths = [
        outputs["penalty_security_enforceable"],
        outputs["pledge_foreclosure_prerequisites"],
        outputs["retention_available"],
        outputs["surety_enforceable"],
        outputs["guarantee_demand_payable"],
        outputs["deposit_retained"],
        outputs["deposit_return_double"],
        outputs["security_payment_credit_available"],
    ]
    solver.add(
        outputs["security_enforcement_available"]
        == And(variables["creditor_good_faith"], Or(*enforceable_paths))
    )
    solver.add(
        outputs["competing_security_paths"]
        == Or(
            *[
                And(left, right)
                for index, left in enumerate(enforceable_paths)
                for right in enforceable_paths[index + 1 :]
            ]
        )
    )
    security_defect = Or(
        And(variables["penalty_agreed"], Not(variables["penalty_writing_observed"])),
        And(variables["pledge_created"], Not(outputs["pledge_valid_between_parties"])),
        And(variables["suretyship_created"], Not(variables["suretyship_writing_observed"])),
        And(
            variables["independent_guarantee_issued"],
            Not(outputs["guarantee_formally_effective"]),
        ),
    )
    solver.add(
        outputs["main_obligation_unaffected_by_security_defect"] == And(valid_main, security_defect)
    )
    solver.add(
        outputs["requires_human_security_assessment"]
        == Or(
            outputs["security_mechanism_detected"],
            accessory_created,
            variables["independent_guarantee_issued"],
            variables["asset_lawfully_in_creditor_possession"],
            variables["creditor_demand_made"],
            outputs["pledge_foreclosure_bar"],
            outputs["competing_security_paths"],
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return SecurityEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            **{
                field_name: False
                for field_name in outputs
                if field_name != "requires_human_security_assessment"
            },
            requires_human_security_assessment=True,
            reasons_ru=["Набор фактов об обеспечении исполнения противоречив."],
            warnings_ru=["Требуется повторная проверка исходных данных юристом."],
        )
    model = solver.model()
    values = {
        field_name: bool(model.eval(variable, model_completion=True))
        for field_name, variable in outputs.items()
    }
    reasons_ru = []
    if values["security_enforcement_available"]:
        reasons_ru.append("Выявлен как минимум один формально доступный способ обеспечения.")
    elif values["security_mechanism_detected"]:
        reasons_ru.append("Способ обеспечения выявлен, но условия реализации не подтверждены.")
    else:
        reasons_ru.append("Активный способ обеспечения текущими фактами не подтвержден.")
    if values["accessory_security_displaced_by_main_invalidity"]:
        reasons_ru.append(
            "Недействительность основного обязательства затрагивает акцессорное обеспечение."
        )
    if values["guarantee_survives_main_invalidity"]:
        reasons_ru.append("Независимая гарантия формально отделена от основного обязательства.")
    return SecurityEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        **values,
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель не определяет стоимость предмета залога и размер обеспеченного требования.",
            "Добросовестность, злоупотребление, несоразмерность и порядок реализации оценивает юрист.",
            "Специальные правила ипотеки, банкротства и отдельных гарантий проверяются отдельно.",
        ],
    )
