from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.research_work import (
    ResearchWorkConstraintSet,
    ResearchWorkEvaluation,
    ResearchWorkEvidenceMappingResult,
    build_research_work_constraint_set,
    evaluate_research_work_constraints,
    map_reviewed_research_work_evidence,
)
from causa.institutional.contracts.research_work_evaluation import (
    ResearchWorkBenchmarkReport,
    ResearchWorkRedTeamReport,
    run_research_work_benchmark_suite,
    run_research_work_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticResearchWorkEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: ResearchWorkEvidenceMappingResult
    constraint_set: ResearchWorkConstraintSet
    reviewed_evaluation: ResearchWorkEvaluation
    benchmark_report: ResearchWorkBenchmarkReport
    red_team_report: ResearchWorkRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticResearchWorkEvaluationArtifact":
        expected_set = build_research_work_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_research_work_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError("Research-work evaluation is not reproducible from reviewed evidence.")
        return self


def build_synthetic_research_work_evaluation_artifact() -> SyntheticResearchWorkEvaluationArtifact:
    evidence = build_synthetic_supply_analysis_request().research_work_evidence
    mapping = map_reviewed_research_work_evidence(evidence)
    constraint_set = build_research_work_constraint_set(mapping)
    return SyntheticResearchWorkEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о выполнении научно-исследовательских, "
            "опытно-конструкторских и технологических работ по статьям 769–778 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_research_work_constraints(constraint_set, mapping.facts),
        benchmark_report=run_research_work_benchmark_suite(),
        red_team_report=run_research_work_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
