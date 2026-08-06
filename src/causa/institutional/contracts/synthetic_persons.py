from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.persons import (
    PersonsConstraintSet,
    PersonsEvaluation,
    PersonsEvidenceMappingResult,
    build_persons_constraint_set,
    evaluate_persons_constraints,
    map_reviewed_persons_evidence,
)
from causa.institutional.contracts.persons_evaluation import (
    PersonsBenchmarkReport,
    PersonsRedTeamReport,
    run_persons_benchmark_suite,
    run_persons_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticPersonsEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: PersonsEvidenceMappingResult
    constraint_set: PersonsConstraintSet
    reviewed_evaluation: PersonsEvaluation
    benchmark_report: PersonsBenchmarkReport
    red_team_report: PersonsRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticPersonsEvaluationArtifact":
        expected_set = build_persons_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_persons_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Persons evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_persons_evaluation_artifact() -> SyntheticPersonsEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().persons_evidence
    mapping = map_reviewed_persons_evidence(evidence)
    constraint_set = build_persons_constraint_set(mapping)
    return SyntheticPersonsEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правоспособности и дееспособности граждан и юридических "
            "лиц по статьям 17–53 ГК РФ. Не устанавливает судебный факт и не является "
            "юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_persons_constraints(constraint_set, mapping.facts),
        benchmark_report=run_persons_benchmark_suite(),
        red_team_report=run_persons_red_team_suite(),
        source_urls=["https://government.ru/docs/all/95820/"],
    )
