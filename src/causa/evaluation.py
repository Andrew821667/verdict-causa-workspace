from pydantic import BaseModel, Field

from causa.governance.failure_taxonomy import FailureType


class BenchmarkTask(BaseModel):
    id: str
    title: str
    institutional_package_id: str
    expected_source_refs: list[str] = Field(default_factory=list)
    expected_failure_types: list[FailureType] = Field(default_factory=list)
    facts: dict[str, bool] = Field(default_factory=dict)
    expected_breach_issue: bool | None = None
    required_warning_fragments: list[str] = Field(default_factory=list)


class BenchmarkTaskResult(BaseModel):
    task_id: str
    passed: bool
    breach_issue: bool | None = None
    source_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class BenchmarkSuiteReport(BaseModel):
    id: str
    institutional_package_id: str
    total: int
    passed: int
    failed: int
    results: list[BenchmarkTaskResult] = Field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total


class RedTeamScenario(BaseModel):
    id: str
    title: str
    institutional_package_id: str
    unacceptable_outcome: str
    target_failure_type: FailureType


class IncidentRecord(BaseModel):
    id: str
    failure_type: FailureType
    description: str
    trace_id: str | None = None
