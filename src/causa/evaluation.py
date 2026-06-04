from pydantic import BaseModel, Field

from causa.governance.failure_taxonomy import FailureType


class BenchmarkTask(BaseModel):
    id: str
    title: str
    institutional_package_id: str
    expected_source_refs: list[str] = Field(default_factory=list)
    expected_failure_types: list[FailureType] = Field(default_factory=list)


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
