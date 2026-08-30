from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator
from z3 import And, Bool, Not, Or, Solver, sat

from causa.core.bootstrap import BootstrapReviewStatus


FREEDOM_EVIDENCE_SCHEMA_VERSION = "contracts.freedom-evidence.v0"
FREEDOM_MAPPING_VERSION = "contracts-reviewed-freedom-to-facts-v0"
FREEDOM_MODEL_VERSION = "contracts-freedom-price-articles-421-424-427-v0"


class FreedomEvidencePredicate(str, Enum):
    # Заявлен ли в деле договор вообще. Предпосылка всей модели: и свобода
    # заключения (статья 421), и презумпция возмездности (пункт 3 статьи 423)
    # — суждения О ДОГОВОРЕ. Пока институт стоял без ворот, набор фактов, где
    # всё ложно, читался как «договор свободно заключён и предполагается
    # возмездным», а через требование определить цену поднимал ещё и флаг
    # проверки юристом — в деле, где договора нет вовсе.
    CONTRACT_ASSERTED = "contract_asserted"
    # Свобода договора (статья 421 ГК РФ).
    CONTRACT_CONCLUSION_COMPELLED_BY_LAW = "contract_conclusion_compelled_by_law"
    CONTRACT_TYPE_UNNAMED = "contract_type_unnamed"
    MIXED_CONTRACT_ELEMENTS = "mixed_contract_elements"
    TERMS_PRESCRIBED_BY_MANDATORY_NORM = "terms_prescribed_by_mandatory_norm"
    # Договор и закон (статья 422 ГК РФ).
    CONTRACT_CONFORMS_MANDATORY_RULES = "contract_conforms_mandatory_rules"
    NEW_MANDATORY_LAW_AFTER_CONCLUSION = "new_mandatory_law_after_conclusion"
    NEW_LAW_GIVEN_RETROACTIVE_EFFECT = "new_law_given_retroactive_effect"
    # Возмездность и цена (статьи 423 и 424 ГК РФ).
    CONTRACT_GRATUITOUS_BY_NATURE = "contract_gratuitous_by_nature"
    PRICE_AGREED_BY_PARTIES = "price_agreed_by_parties"
    REGULATED_PRICE_MANDATED = "regulated_price_mandated"
    COMPARABLE_PRICE_AVAILABLE = "comparable_price_available"
    # Восполнение пробела в условии и примерные условия (пункты 4-5 статьи 421,
    # статья 427 ГК РФ).
    TERM_NOT_DETERMINED_BY_PARTIES = "term_not_determined_by_parties"
    TERM_NOT_COVERED_BY_DISPOSITIVE_NORM = "term_not_covered_by_dispositive_norm"
    STANDARD_TERMS_ASSERTED = "standard_terms_asserted"
    STANDARD_TERMS_PUBLISHED_FOR_CONTRACT_TYPE = "standard_terms_published_for_contract_type"
    CONTRACT_REFERS_TO_STANDARD_TERMS = "contract_refers_to_standard_terms"
    STANDARD_TERMS_MEET_CUSTOM_REQUIREMENTS = "standard_terms_meet_custom_requirements"


REQUIRED_FREEDOM_PREDICATES = frozenset(FreedomEvidencePredicate)


class FreedomEvidenceAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    predicate: FreedomEvidencePredicate
    value: bool
    source_refs: tuple[str, ...] = Field(min_length=1)


class ReviewedFreedomEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    case_id: str
    schema_version: str = FREEDOM_EVIDENCE_SCHEMA_VERSION
    assertions: tuple[FreedomEvidenceAssertion, ...]
    legal_source_refs: tuple[str, ...] = Field(min_length=2)
    review_status: BootstrapReviewStatus = BootstrapReviewStatus.DRAFT
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def reject_duplicates(self) -> "ReviewedFreedomEvidence":
        predicates = [assertion.predicate for assertion in self.assertions]
        if len(predicates) != len(set(predicates)):
            raise ValueError("Freedom evidence contains duplicate predicates.")
        if len(self.legal_source_refs) != len(set(self.legal_source_refs)):
            raise ValueError("Freedom evidence contains duplicate legal source refs.")
        return self


class FreedomFactSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_asserted: bool
    contract_conclusion_compelled_by_law: bool
    contract_type_unnamed: bool
    mixed_contract_elements: bool
    terms_prescribed_by_mandatory_norm: bool
    contract_conforms_mandatory_rules: bool
    new_mandatory_law_after_conclusion: bool
    new_law_given_retroactive_effect: bool
    contract_gratuitous_by_nature: bool
    price_agreed_by_parties: bool
    regulated_price_mandated: bool
    comparable_price_available: bool
    term_not_determined_by_parties: bool
    term_not_covered_by_dispositive_norm: bool
    standard_terms_asserted: bool
    standard_terms_published_for_contract_type: bool
    contract_refers_to_standard_terms: bool
    standard_terms_meet_custom_requirements: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "FreedomFactSet":
        if self.new_law_given_retroactive_effect and not self.new_mandatory_law_after_conclusion:
            raise ValueError("Обратная сила невозможна без принятого после заключения закона.")
        if self.contract_refers_to_standard_terms and not self.standard_terms_asserted:
            raise ValueError("Отсылка к примерным условиям невозможна без их заявления в деле.")
        if self.standard_terms_published_for_contract_type and not self.standard_terms_asserted:
            raise ValueError("Квалификация примерных условий невозможна без их заявления в деле.")
        if self.standard_terms_meet_custom_requirements and not self.standard_terms_asserted:
            raise ValueError(
                "Соответствие требованиям обычая невозможно без заявленных примерных условий."
            )
        return self


class FreedomFactProvenance(BaseModel):
    fact_name: str
    assertion_id: str
    source_refs: list[str] = Field(default_factory=list)


class FreedomEvidenceMappingResult(BaseModel):
    evidence_id: str
    schema_version: str
    mapping_version: str
    facts: FreedomFactSet
    legal_source_refs: list[str] = Field(default_factory=list)
    provenance: list[FreedomFactProvenance] = Field(default_factory=list)


class FreedomConstraintSet(BaseModel):
    id: str
    model_version: str = FREEDOM_MODEL_VERSION
    legal_source_refs: list[str] = Field(default_factory=list)
    expressions: list[str] = Field(default_factory=list)


class FreedomEvaluation(BaseModel):
    constraint_set_id: str
    satisfiable: bool
    contract_conclusion_free: bool
    terms_by_party_discretion: bool
    mixed_contract_rules_apply: bool
    contract_valid_against_mandatory_rules: bool
    prior_terms_survive_new_law: bool
    contract_presumed_onerous: bool
    price_determined: bool
    term_gap_open_for_custom: bool
    standard_terms_incorporated_by_reference: bool
    standard_terms_applied_as_custom: bool
    standard_terms_govern_the_term: bool
    requires_human_freedom_assessment: bool
    reasons_ru: list[str] = Field(default_factory=list)
    warnings_ru: list[str] = Field(default_factory=list)


def map_reviewed_freedom_evidence(
    evidence: ReviewedFreedomEvidence,
) -> FreedomEvidenceMappingResult:
    if evidence.review_status != BootstrapReviewStatus.REVIEWED:
        raise ValueError("Freedom evidence must be reviewed before analysis.")
    if not evidence.reviewer_id:
        raise ValueError("Freedom evidence requires a reviewer_id before analysis.")
    assertions = {assertion.predicate: assertion for assertion in evidence.assertions}
    missing = sorted(
        predicate.value for predicate in REQUIRED_FREEDOM_PREDICATES - assertions.keys()
    )
    if missing:
        raise ValueError(
            "Reviewed freedom evidence is incomplete; missing predicates: " + ", ".join(missing)
        )
    values = {
        predicate.value: assertions[predicate].value for predicate in REQUIRED_FREEDOM_PREDICATES
    }
    return FreedomEvidenceMappingResult(
        evidence_id=evidence.id,
        schema_version=evidence.schema_version,
        mapping_version=FREEDOM_MAPPING_VERSION,
        facts=FreedomFactSet(**values),
        legal_source_refs=list(evidence.legal_source_refs),
        provenance=[
            FreedomFactProvenance(
                fact_name=predicate.value,
                assertion_id=assertions[predicate].id,
                source_refs=list(assertions[predicate].source_refs),
            )
            for predicate in sorted(REQUIRED_FREEDOM_PREDICATES, key=lambda item: item.value)
        ],
    )


def build_freedom_constraint_set(
    mapping: FreedomEvidenceMappingResult,
) -> FreedomConstraintSet:
    return FreedomConstraintSet(
        id=f"freedom-constraint-set:{mapping.evidence_id}",
        legal_source_refs=mapping.legal_source_refs,
        expressions=[
            "contract_conclusion_free == contract_asserted AND NOT contract_conclusion_compelled_by_law",
            "terms_by_party_discretion == contract_asserted AND NOT terms_prescribed_by_mandatory_norm",
            "mixed_contract_rules_apply == mixed_contract_elements",
            "contract_valid_against_mandatory_rules == contract_conforms_mandatory_rules",
            "prior_terms_survive_new_law == new_mandatory_law_after_conclusion AND NOT new_law_given_retroactive_effect",
            "contract_presumed_onerous == contract_asserted AND NOT contract_gratuitous_by_nature",
            "price_determined == price_agreed_by_parties OR regulated_price_mandated OR (contract_presumed_onerous AND comparable_price_available)",
            "term_gap_open_for_custom == term_not_determined_by_parties AND term_not_covered_by_dispositive_norm",
            "standard_terms_incorporated_by_reference == standard_terms_asserted AND standard_terms_published_for_contract_type AND contract_refers_to_standard_terms",
            "standard_terms_applied_as_custom == standard_terms_asserted AND standard_terms_published_for_contract_type AND NOT contract_refers_to_standard_terms AND standard_terms_meet_custom_requirements AND term_gap_open_for_custom",
            "standard_terms_govern_the_term == standard_terms_incorporated_by_reference OR standard_terms_applied_as_custom",
            "requires_human_freedom_assessment == contract_type_unnamed OR mixed_contract_elements OR (new_mandatory_law_after_conclusion AND new_law_given_retroactive_effect) OR (contract_presumed_onerous AND NOT price_agreed_by_parties AND NOT regulated_price_mandated) OR standard_terms_asserted",
        ],
    )


def evaluate_freedom_constraints(
    constraint_set: FreedomConstraintSet,
    facts: FreedomFactSet,
) -> FreedomEvaluation:
    variables = {field_name: Bool(field_name) for field_name in FreedomFactSet.model_fields}
    contract_conclusion_free = Bool("contract_conclusion_free")
    terms_by_party_discretion = Bool("terms_by_party_discretion")
    mixed_contract_rules_apply = Bool("mixed_contract_rules_apply")
    contract_valid_against_mandatory_rules = Bool("contract_valid_against_mandatory_rules")
    prior_terms_survive_new_law = Bool("prior_terms_survive_new_law")
    contract_presumed_onerous = Bool("contract_presumed_onerous")
    price_determined = Bool("price_determined")
    term_gap_open_for_custom = Bool("term_gap_open_for_custom")
    standard_terms_incorporated_by_reference = Bool("standard_terms_incorporated_by_reference")
    standard_terms_applied_as_custom = Bool("standard_terms_applied_as_custom")
    standard_terms_govern_the_term = Bool("standard_terms_govern_the_term")
    requires_human_freedom_assessment = Bool("requires_human_freedom_assessment")

    solver = Solver()
    for field_name, variable in variables.items():
        solver.add(variable == getattr(facts, field_name))
    solver.add(
        contract_conclusion_free
        == And(
            variables["contract_asserted"],
            Not(variables["contract_conclusion_compelled_by_law"]),
        )
    )
    solver.add(
        terms_by_party_discretion
        == And(
            variables["contract_asserted"],
            Not(variables["terms_prescribed_by_mandatory_norm"]),
        )
    )
    solver.add(mixed_contract_rules_apply == variables["mixed_contract_elements"])
    solver.add(
        contract_valid_against_mandatory_rules == variables["contract_conforms_mandatory_rules"]
    )
    solver.add(
        prior_terms_survive_new_law
        == And(
            variables["new_mandatory_law_after_conclusion"],
            Not(variables["new_law_given_retroactive_effect"]),
        )
    )
    solver.add(
        contract_presumed_onerous
        == And(
            variables["contract_asserted"],
            Not(variables["contract_gratuitous_by_nature"]),
        )
    )
    solver.add(
        price_determined
        == Or(
            variables["price_agreed_by_parties"],
            variables["regulated_price_mandated"],
            And(contract_presumed_onerous, variables["comparable_price_available"]),
        )
    )
    solver.add(
        term_gap_open_for_custom
        == And(
            variables["term_not_determined_by_parties"],
            variables["term_not_covered_by_dispositive_norm"],
        )
    )
    solver.add(
        standard_terms_incorporated_by_reference
        == And(
            variables["standard_terms_asserted"],
            variables["standard_terms_published_for_contract_type"],
            variables["contract_refers_to_standard_terms"],
        )
    )
    solver.add(
        standard_terms_applied_as_custom
        == And(
            variables["standard_terms_asserted"],
            variables["standard_terms_published_for_contract_type"],
            Not(variables["contract_refers_to_standard_terms"]),
            variables["standard_terms_meet_custom_requirements"],
            term_gap_open_for_custom,
        )
    )
    solver.add(
        standard_terms_govern_the_term
        == Or(standard_terms_incorporated_by_reference, standard_terms_applied_as_custom)
    )
    solver.add(
        requires_human_freedom_assessment
        == Or(
            variables["contract_type_unnamed"],
            variables["mixed_contract_elements"],
            And(
                variables["new_mandatory_law_after_conclusion"],
                variables["new_law_given_retroactive_effect"],
            ),
            And(
                contract_presumed_onerous,
                Not(variables["price_agreed_by_parties"]),
                Not(variables["regulated_price_mandated"]),
            ),
            variables["standard_terms_asserted"],
        )
    )

    satisfiable = solver.check() == sat
    if not satisfiable:
        return FreedomEvaluation(
            constraint_set_id=constraint_set.id,
            satisfiable=False,
            contract_conclusion_free=False,
            terms_by_party_discretion=False,
            mixed_contract_rules_apply=False,
            contract_valid_against_mandatory_rules=False,
            prior_terms_survive_new_law=False,
            contract_presumed_onerous=False,
            price_determined=False,
            term_gap_open_for_custom=False,
            standard_terms_incorporated_by_reference=False,
            standard_terms_applied_as_custom=False,
            standard_terms_govern_the_term=False,
            requires_human_freedom_assessment=True,
            reasons_ru=["Набор фактов о свободе договора и цене противоречив."],
            warnings_ru=["Требуется проверка исходных доказательств юристом."],
        )
    model = solver.model()

    def truth(variable):
        return bool(model.eval(variable, model_completion=True))

    reasons_ru = [
        (
            "Стороны свободны в заключении договора; понуждение не допускается "
            "(пункт 1 статьи 421 ГК РФ)."
            if truth(contract_conclusion_free)
            else "Заключение договора обязательно в силу закона или обязательства."
        ),
    ]
    if truth(terms_by_party_discretion):
        reasons_ru.append(
            "Условия договора определяются по усмотрению сторон, кроме случаев, когда "
            "содержание условия предписано законом (пункт 4 статьи 421 ГК РФ)."
        )
    if truth(mixed_contract_rules_apply):
        reasons_ru.append(
            "К смешанному договору применяются в соответствующих частях правила о "
            "договорах, элементы которых он содержит (пункт 3 статьи 421 ГК РФ)."
        )
    if truth(contract_valid_against_mandatory_rules):
        reasons_ru.append(
            "Договор соответствует обязательным для сторон правилам, действующим в "
            "момент его заключения (пункт 1 статьи 422 ГК РФ)."
        )
    if truth(prior_terms_survive_new_law):
        reasons_ru.append(
            "Условия договора сохраняют силу при принятии нового закона, если ему не "
            "придана обратная сила (пункт 2 статьи 422 ГК РФ)."
        )
    if truth(contract_presumed_onerous):
        reasons_ru.append(
            "Договор предполагается возмездным, если из закона, содержания или существа "
            "договора не вытекает иное (пункт 3 статьи 423 ГК РФ)."
        )
    if truth(price_determined):
        reasons_ru.append(
            "Цена исполнения определена соглашением, регулируемой ценой либо ценой за "
            "сопоставимые товары, работы или услуги (статья 424 ГК РФ)."
        )
    if truth(standard_terms_incorporated_by_reference):
        reasons_ru.append(
            "Договор содержит отсылку к примерным условиям, разработанным для договоров "
            "соответствующего вида и опубликованным в печати, — эти условия входят в "
            "содержание договора по отсылке (пункт 1 статьи 427 ГК РФ)."
        )
    elif truth(standard_terms_applied_as_custom):
        reasons_ru.append(
            "Договор не содержит отсылки к примерным условиям, но условие, ими "
            "охватываемое, не определено ни сторонами, ни диспозитивной нормой — "
            "примерные условия применяются к отношениям сторон как обычай (пункт 2 "
            "статьи 427, пункт 5 статьи 421 ГК РФ)."
        )
    elif truth(variables["standard_terms_asserted"]):
        reasons_ru.append(
            "Примерные условия заявлены, но договор ими не определяется: либо они не "
            "отвечают требованиям обычая или квалификации по пункту 1 статьи 427 ГК РФ, "
            "либо условие уже определено сторонами или диспозитивной нормой и восполнения "
            "не требует (пункт 5 статьи 421 ГК РФ)."
        )
    return FreedomEvaluation(
        constraint_set_id=constraint_set.id,
        satisfiable=True,
        contract_conclusion_free=truth(contract_conclusion_free),
        terms_by_party_discretion=truth(terms_by_party_discretion),
        mixed_contract_rules_apply=truth(mixed_contract_rules_apply),
        contract_valid_against_mandatory_rules=truth(contract_valid_against_mandatory_rules),
        prior_terms_survive_new_law=truth(prior_terms_survive_new_law),
        contract_presumed_onerous=truth(contract_presumed_onerous),
        price_determined=truth(price_determined),
        term_gap_open_for_custom=truth(term_gap_open_for_custom),
        standard_terms_incorporated_by_reference=truth(standard_terms_incorporated_by_reference),
        standard_terms_applied_as_custom=truth(standard_terms_applied_as_custom),
        standard_terms_govern_the_term=truth(standard_terms_govern_the_term),
        requires_human_freedom_assessment=truth(requires_human_freedom_assessment),
        reasons_ru=reasons_ru,
        warnings_ru=[
            "Модель проверяет только формальные правила о свободе договора, его "
            "соответствии закону, определении цены и восполнении пробела в условии и не "
            "заменяет судебную оценку.",
            "Квалификация непоименованного и смешанного договора, императивность норм и "
            "размер цены оцениваются экспертом и судом.",
            "Соответствие примерных условий требованиям обычая по статье 5 ГК РФ и "
            "содержание диспозитивной нормы, покрывающей условие, модель не разбирает — "
            "она принимает эти оценки как установленный факт.",
        ],
    )
