from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.citizen_ranking import (
    CitizenRankingConstraintSet,
    CitizenRankingEvaluation,
    CitizenRankingEvidenceMappingResult,
    build_citizen_ranking_constraint_set,
    evaluate_citizen_ranking_constraints,
    map_reviewed_citizen_ranking_evidence,
)
from causa.institutional.contracts.citizen_ranking_evaluation import (
    CitizenRankingBenchmarkReport,
    CitizenRankingRedTeamReport,
    run_citizen_ranking_benchmark_suite,
    run_citizen_ranking_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticCitizenRankingEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: CitizenRankingEvidenceMappingResult
    constraint_set: CitizenRankingConstraintSet
    reviewed_evaluation: CitizenRankingEvaluation
    benchmark_report: CitizenRankingBenchmarkReport
    red_team_report: CitizenRankingRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticCitizenRankingEvaluationArtifact":
        expected_set = build_citizen_ranking_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_citizen_ranking_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Citizen-ranking evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_citizen_ranking_evaluation_artifact() -> (
    SyntheticCitizenRankingEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().citizen_ranking_evidence
    mapping = map_reviewed_citizen_ranking_evidence(evidence)
    constraint_set = build_citizen_ranking_constraint_set(mapping)
    return SyntheticCitizenRankingEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка очерёдности удовлетворения требований кредиторов "
            "гражданина по статье 213.27 закона 127-ФЗ. В демонстрационном деле спор о "
            "поставке ведут две организации, дела о банкротстве гражданина нет, и "
            "институт молчит: это и есть ожидаемый результат для такого дела. Не "
            "устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_citizen_ranking_constraints(constraint_set, mapping.facts),
        benchmark_report=run_citizen_ranking_benchmark_suite(),
        red_team_report=run_citizen_ranking_red_team_suite(),
        source_urls=["http://pravo.gov.ru/proxy/ips/?docbody=&nd=102078527"],
    )
