from pydantic import BaseModel, Field, model_validator

from causa.institutional.contracts.public_contract import (
    PublicContractConstraintSet,
    PublicContractEvaluation,
    PublicContractEvidenceMappingResult,
    build_public_contract_constraint_set,
    evaluate_public_contract_constraints,
    map_reviewed_public_contract_evidence,
)
from causa.institutional.contracts.public_contract_evaluation import (
    PublicContractBenchmarkReport,
    PublicContractRedTeamReport,
    run_public_contract_benchmark_suite,
    run_public_contract_red_team_suite,
)
from causa.institutional.contracts.synthetic_reviewed_analysis import (
    build_synthetic_supply_analysis_request,
)


class SyntheticPublicContractEvaluationArtifact(BaseModel):
    locale: str = "ru-RU"
    disclaimer_ru: str
    reviewed_mapping: PublicContractEvidenceMappingResult
    constraint_set: PublicContractConstraintSet
    reviewed_evaluation: PublicContractEvaluation
    benchmark_report: PublicContractBenchmarkReport
    red_team_report: PublicContractRedTeamReport
    source_urls: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_replay(self) -> "SyntheticPublicContractEvaluationArtifact":
        expected_set = build_public_contract_constraint_set(self.reviewed_mapping)
        expected_evaluation = evaluate_public_contract_constraints(
            expected_set, self.reviewed_mapping.facts
        )
        if self.constraint_set != expected_set or self.reviewed_evaluation != expected_evaluation:
            raise ValueError(
                "Public-contract evaluation is not reproducible from reviewed evidence."
            )
        return self


def build_synthetic_public_contract_evaluation_artifact() -> (
    SyntheticPublicContractEvaluationArtifact
):
    evidence = build_synthetic_supply_analysis_request().public_contract_evidence
    mapping = map_reviewed_public_contract_evidence(evidence)
    constraint_set = build_public_contract_constraint_set(mapping)
    return SyntheticPublicContractEvaluationArtifact(
        disclaimer_ru=(
            "Синтетическая проверка правил о публичном договоре по статье 426 ГК РФ. "
            "Не устанавливает судебный факт и не является юридической консультацией."
        ),
        reviewed_mapping=mapping,
        constraint_set=constraint_set,
        reviewed_evaluation=evaluate_public_contract_constraints(constraint_set, mapping.facts),
        benchmark_report=run_public_contract_benchmark_suite(),
        red_team_report=run_public_contract_red_team_suite(),
        source_urls=[
            "https://government.ru/docs/all/95825/",
        ],
    )
