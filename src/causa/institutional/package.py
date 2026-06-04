from pydantic import BaseModel, Field


class InstitutionalPackageManifest(BaseModel):
    id: str
    legal_institute: str
    version: str
    core_compatibility: str
    vocabulary_refs: list[str] = Field(default_factory=list)
    authority_model_refs: list[str] = Field(default_factory=list)
    temporal_model_refs: list[str] = Field(default_factory=list)
    bootstrap_schema_refs: list[str] = Field(default_factory=list)
    mapping_rule_refs: list[str] = Field(default_factory=list)
    contradiction_taxonomy_refs: list[str] = Field(default_factory=list)
    legal_operator_refs: list[str] = Field(default_factory=list)
    benchmark_refs: list[str] = Field(default_factory=list)
    red_team_refs: list[str] = Field(default_factory=list)
    confidence_policy_refs: list[str] = Field(default_factory=list)
    activation_policy_refs: list[str] = Field(default_factory=list)
    domain_owner_responsibilities_ref: str | None = None

    def missing_required_sections(self) -> list[str]:
        required = {
            "vocabulary_refs": self.vocabulary_refs,
            "authority_model_refs": self.authority_model_refs,
            "temporal_model_refs": self.temporal_model_refs,
            "bootstrap_schema_refs": self.bootstrap_schema_refs,
            "mapping_rule_refs": self.mapping_rule_refs,
            "contradiction_taxonomy_refs": self.contradiction_taxonomy_refs,
            "legal_operator_refs": self.legal_operator_refs,
            "benchmark_refs": self.benchmark_refs,
            "red_team_refs": self.red_team_refs,
            "confidence_policy_refs": self.confidence_policy_refs,
            "activation_policy_refs": self.activation_policy_refs,
        }
        missing = [name for name, value in required.items() if not value]
        if not self.domain_owner_responsibilities_ref:
            missing.append("domain_owner_responsibilities_ref")
        return missing

    @property
    def is_phase0_complete(self) -> bool:
        return not self.missing_required_sections()
