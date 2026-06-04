from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeLayer(str, Enum):
    SOURCE = "source"
    FORMAL_NORM = "formal_norm"
    DOCTRINE = "doctrine"
    CASE = "case"


class VersionCoordinates(BaseModel):
    knowledge_version: str
    institutional_package_version: str
    policy_version: str
    translation_template_version: str | None = None
    model_profile: str | None = None


class KnowledgeNode(BaseModel):
    id: str
    layer: KnowledgeLayer
    label: str
    source_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeEdge(BaseModel):
    source_id: str
    target_id: str
    relation: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DecisionTrace(BaseModel):
    id: str
    case_id: str
    versions: VersionCoordinates
    nodes: list[KnowledgeNode] = Field(default_factory=list)
    edges: list[KnowledgeEdge] = Field(default_factory=list)
    claims: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
