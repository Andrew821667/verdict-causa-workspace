from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.energy_supply import (
    EnergySupplyConstraintSet,
    EnergySupplyEvaluation,
    EnergySupplyEvidenceMappingResult,
    build_energy_supply_constraint_set,
    evaluate_energy_supply_constraints,
    map_reviewed_energy_supply_evidence,
)
from causa.institutional.contracts.energy_supply_evaluation import (
    EnergySupplyBenchmarkReport,
    EnergySupplyRedTeamReport,
    run_energy_supply_benchmark_suite,
    run_energy_supply_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticEnergySupplyEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: EnergySupplyEvidenceMappingResult
    constraint_set: EnergySupplyConstraintSet
    reviewed_evaluation: EnergySupplyEvaluation
    benchmark_report: EnergySupplyBenchmarkReport
    red_team_report: EnergySupplyRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticEnergySupplyEvaluationArtifact":
        expected_set = build_energy_supply_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_energy_supply_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Energy supply evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_energy_supply_evaluation_artifact() -> SyntheticEnergySupplyEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().energy_supply_evidence
    mapping = map_reviewed_energy_supply_evidence(evidence)
    constraint_set = build_energy_supply_constraint_set(mapping)
    return SyntheticEnergySupplyEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил об энергоснабжении по статьям 539–548 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_energy_supply_constraints(constraint_set, mapping.facts),
        benchmark_report=run_energy_supply_benchmark_suite(),
        red_team_report=run_energy_supply_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
