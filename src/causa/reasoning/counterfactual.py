from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class LegalOperatorKind(str, Enum):
    ADD_OR_REMOVE_FACT = "add_or_remove_fact"
    CHANGE_QUALIFICATION = "change_qualification"
    ACTIVATE_EXCEPTION = "activate_exception"
    CHANGE_CAUSAL_LINK = "change_causal_link"
    CHANGE_TEMPORAL_ANCHOR = "change_temporal_anchor"
    CHANGE_REMEDY_PATH = "change_remedy_path"


class CounterfactualBudget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_scenarios: int = Field(default=8, ge=1, le=32)
    max_changed_facts_per_scenario: int = Field(default=4, ge=1, le=8)


class CounterfactualFactDelta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field_name: str
    field_label_ru: str
    before: bool
    after: bool


class CounterfactualOutcomeDelta(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field_name: str
    field_label_ru: str
    before: bool
    after: bool
