from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.design_work import (
    DesignWorkConstraintSet,
    DesignWorkEvaluation,
    DesignWorkEvidenceMappingResult,
    build_design_work_constraint_set,
    evaluate_design_work_constraints,
    map_reviewed_design_work_evidence,
)
from causa.institutional.contracts.design_work_evaluation import (
    DesignWorkBenchmarkReport,
    DesignWorkRedTeamReport,
    run_design_work_benchmark_suite,
    run_design_work_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticDesignWorkEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: DesignWorkEvidenceMappingResult
    constraint_set: DesignWorkConstraintSet
    reviewed_evaluation: DesignWorkEvaluation
    benchmark_report: DesignWorkBenchmarkReport
    red_team_report: DesignWorkRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticDesignWorkEvaluationArtifact":
        expected_set = build_design_work_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_design_work_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Design-work evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_design_work_evaluation_artifact() -> SyntheticDesignWorkEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().design_work_evidence
    mapping = map_reviewed_design_work_evidence(evidence)
    constraint_set = build_design_work_constraint_set(mapping)
    return SyntheticDesignWorkEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о подряде на выполнение проектных и изыскательских "
            "работ по статьям 758–762 ГК РФ. Не устанавливает судебный факт и не является "
            "юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_design_work_constraints(constraint_set, mapping.facts),
        benchmark_report=run_design_work_benchmark_suite(),
        red_team_report=run_design_work_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
