from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


FORM_EVIDENCE_SCHEMA_VERSION = "contracts.form-evidence.v0"
FORM_MAPPING_VERSION = "contracts-reviewed-form-to-facts-v0"
FORM_MODEL_VERSION = "contracts-form-articles-158-165-434-3-v0"


class FormEvidencePredicate(str, Enum):
    # Требуемая форма сделки (статьи 158, 159, 161, 163 ГК РФ).
    ORAL_FORM_PERMITTED = "oral_form_permitted"
    SIMPLE_WRITTEN_FORM_REQUIRED = "simple_written_form_required"
    NOTARIAL_FORM_REQUIRED = "notarial_form_required"
    # Способы соблюдения письменной формы (статьи 160, 434 ГК РФ).
    SIMPLE_WRITTEN_FORM_OBSERVED = "simple_written_form_observed"
    DOCUMENT_SIGNED_BY_PARTIES = "document_signed_by_parties"
    EXCHANGE_OF_DOCUMENTS = "exchange_of_documents"
    ELECTRONIC_SIGNATURE_VALID = "electronic_signature_valid"
    # Акцепт конклюдентными действиями (пункт 3 статьи 434 во взаимосвязи с
    # пунктом 3 статьи 438 ГК РФ).
    WRITTEN_OFFER_MADE = "written_offer_made"
    OFFER_TERMS_PERFORMED_AS_ACCEPTANCE = "offer_terms_performed_as_acceptance"
    NOTARIAL_FORM_OBSERVED = "notarial_form_observed"
    # Последствия несоблюдения формы (статьи 162, 163 ГК РФ).
    WRITTEN_NONCOMPLIANCE_INVALIDATES_BY_LAW_OR_AGREEMENT = (
        "written_noncompliance_invalidates_by_law_or_agreement"
    )
    PERFORMANCE_OR_WRITTEN_PROOF_AVAILABLE = "performance_or_written_proof_available"


REQUIRED_FORM_PREDICATES = frozenset(FormEvidencePredicate)


class FormEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: FormEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedFormEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = FORM_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[FormEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedFormEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Form evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Form evidence contains duplicate legal source refs.")
        return self


class FormFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    oral_form_permitted: bool
    simple_written_form_required: bool
    notarial_form_required: bool
    simple_written_form_observed: bool
    document_signed_by_parties: bool
    exchange_of_documents: bool
    electronic_signature_valid: bool
    written_offer_made: bool
    offer_terms_performed_as_acceptance: bool
    notarial_form_observed: bool
    written_noncompliance_invalidates_by_law_or_agreement: bool
    performance_or_written_proof_available: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "FormFactSet":
        if self.oral_form_permitted and (
            self.simple_written_form_required or self.notarial_form_required
        ):
            raise ValueError("Oral form cannot be permitted when a stricter form is required.")
        if self.notarial_form_required and not self.simple_written_form_required:
            raise ValueError("Notarial form presupposes a mandatory written form.")
        if self.offer_terms_performed_as_acceptance and not self.written_offer_made:
            raise ValueError(
                "Письменную форму соблюдает акцепт действиями именно письменной оферты: "
                "устное предложение, принятое действиями, письменной формы не даёт "
                "(пункт 3 статьи 434 ГК РФ)."
            )
        return self


class FormFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class FormEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: FormFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[FormFactProvenance] = Field(default_factory=list)


class FormConstraintSet(BaseModel):
    id: str
    model_version: str = FORM_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class FormEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    written_form_method_valid: bool
    acceptance_by_conduct_observes_written_form: bool
    written_form_satisfied: bool
    notarial_form_satisfied: bool
    form_requirement_satisfied: bool
    witness_testimony_barred: bool
    transaction_void_for_form: bool
    oral_form_valid: bool
    requires_human_form_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_form_evidence(
    evidence: ReviewedFormEvidence,
) -> FormEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Form evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Form evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(predicate.value for predicate in REQUIRED_FORM_PREDICATES - assertions.keys())
    if missing:
        raise ValueError(
            "Reviewed form evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_FORM_PREDICATES
    }
    return FormEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=FORM_MAPPING_VERSION,
        facts=FormFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            FormFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_FORM_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_form_constraint_set(
    mapping: FormEvidenceMappingResult,
) -> FormConstraintSet:
    return FormConstraintSet(
        id=f"form-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "written_form_method_valid == document_signed_by_parties OR exchange_of_documents OR electronic_signature_valid",
            "acceptance_by_conduct_observes_written_form == written_offer_made AND offer_terms_performed_as_acceptance",
            "written_form_satisfied == NOT simple_written_form_required OR (simple_written_form_observed AND written_form_method_valid) OR acceptance_by_conduct_observes_written_form",
            "notarial_form_satisfied == NOT notarial_form_required OR notarial_form_observed",
            "form_requirement_satisfied == written_form_satisfied AND notarial_form_satisfied",
            "witness_testimony_barred == simple_written_form_required AND NOT written_form_satisfied",
            "transaction_void_for_form == (notarial_form_required AND NOT notarial_form_observed) OR (simple_written_form_required AND NOT written_form_satisfied AND written_noncompliance_invalidates_by_law_or_agreement)",
            "oral_form_valid == oral_form_permitted AND NOT simple_written_form_required AND NOT notarial_form_required",
            "requires_human_form_assessment == transaction_void_for_form OR (witness_testimony_barred AND NOT performance_or_written_proof_available)",
        ],
    )


def evaluate_form_constraints(
    constraint_set: FormConstraintSet,
    facts: FormFactSet,
) -> FormEvaluation:
    variables = {field_name: Bool(field_name) for field_name in FormFactSet.model_fields}
    written_form_method_valid = Bool("written_form_method_valid")
    acceptance_by_conduct_observes_written_form = Bool(
        "acceptance_by_conduct_observes_written_form"
    )
    written_form_satisfied = Bool("written_form_satisfied")
    notarial_form_satisfied = Bool("notarial_form_satisfied")
    form_requirement_satisfied = Bool("form_requirement_satisfied")
    witness_testimony_barred = Bool("witness_testimony_barred")
    transaction_void_for_form = Bool("transaction_void_for_form")
    oral_form_valid = Bool("oral_form_valid")
    requires_human_form_assessment = Bool("requires_human_form_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        written_form_method_valid
        == Or(
            variables["document_signed_by_parties"],
            variables["exchange_of_documents"],
            variables["electronic_signature_valid"],
        )
    )
    solver.add(
        acceptance_by_conduct_observes_written_form
        == And(
            variables["written_offer_made"],
            variables["offer_terms_performed_as_acceptance"],
        )
    )
    solver.add(
        written_form_satisfied
        == Or(
            Not(variables["simple_written_form_required"]),
            And(variables["simple_written_form_observed"], written_form_method_valid),
            acceptance_by_conduct_observes_written_form,
        )
    )
    solver.add(
        notarial_form_satisfied
        == Or(
            Not(variables["notarial_form_required"]),
            variables["notarial_form_observed"],
        )
    )
    solver.add(form_requirement_satisfied == And(written_form_satisfied, notarial_form_satisfied))
    solver.add(
        witness_testimony_barred
        == And(variables["simple_written_form_required"], Not(written_form_satisfied))
    )
    solver.add(
        transaction_void_for_form
        == Or(
            And(
                variables["notarial_form_required"],
                Not(variables["notarial_form_observed"]),
            ),
            And(
                variables["simple_written_form_required"],
                Not(written_form_satisfied),
                variables["written_noncompliance_invalidates_by_law_or_agreement"],
            ),
        )
    )
    solver.add(
        oral_form_valid
        == And(
            variables["oral_form_permitted"],
            Not(variables["simple_written_form_required"]),
            Not(variables["notarial_form_required"]),
        )
    )
    solver.add(
        requires_human_form_assessment
        == Or(
            transaction_void_for_form,
            And(
                witness_testimony_barred,
                Not(variables["performance_or_written_proof_available"]),
            ),
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return FormEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            written_form_method_valid=False,
            acceptance_by_conduct_observes_written_form=False,
            written_form_satisfied=False,
            notarial_form_satisfied=False,
            form_requirement_satisfied=False,
            witness_testimony_barred=False,
            transaction_void_for_form=False,
            oral_form_valid=False,
            requires_human_form_assessment=True,
            reasons_ru=["Набор фактов о форме сделки противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Требования к форме сделки соблюдены."
            if truth(form_requirement_satisfied)
            else "Требования к форме сделки не соблюдены."
        ),
    ]
    if truth(oral_form_valid):
        reasons_ru.append("Для сделки допустима устная форма (статья 159 ГК РФ).")
    if truth(transaction_void_for_form):
        reasons_ru.append(
            "Несоблюдение формы влечет недействительность сделки (статьи 162, 163 ГК РФ)."
        )
    elif truth(witness_testimony_barred):
        reasons_ru.append(
            "Несоблюдение простой письменной формы лишает права ссылаться на свидетельские "
            "показания, но само по себе не влечет недействительности (статья 162 ГК РФ)."
        )
    if truth(acceptance_by_conduct_observes_written_form):
        reasons_ru.append(
            "Письменная форма договора считается соблюдённой: письменное предложение заключить "
            "договор принято совершением действий по выполнению указанных в нём условий — "
            "отгрузкой товара, выполнением работ, уплатой суммы и тому подобным (пункт 3 статьи "
            "434 и пункт 3 статьи 438 ГК РФ). Подписанного сторонами документа для этого не "
            "требуется, и его отсутствие само по себе о несоблюдении формы не говорит."
        )
    return FormEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        written_form_method_valid=truth(written_form_method_valid),
        acceptance_by_conduct_observes_written_form=truth(
            acceptance_by_conduct_observes_written_form
        ),
        written_form_satisfied=truth(written_form_satisfied),
        notarial_form_satisfied=truth(notarial_form_satisfied),
        form_requirement_satisfied=truth(form_requirement_satisfied),
        witness_testimony_barred=truth(witness_testimony_barred),
        transaction_void_for_form=truth(transaction_void_for_form),
        oral_form_valid=truth(oral_form_valid),
        requires_human_form_assessment=truth(requires_human_form_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о форме сделки и не заменяет судебную оценку.",
            "Достаточность доказательств формы и соблюдение способа ее совершения оцениваются экспертом и судом.",
            "Совершены ли действия именно по выполнению условий оферты и в срок, установленный "
            "для акцепта, оценивает человек: модель принимает это как установленный факт "
            "(пункт 3 статьи 438 ГК РФ).",
        ],
    )
