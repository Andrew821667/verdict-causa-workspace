from causa.institutional.package import InstitutionalPackageManifest


CONTRACTS_PACKAGE_MANIFEST = InstitutionalPackageManifest(
    id="contracts-ru-v0",
    legal_institute="Contractual relations: obligations, sale, supply, and breach liability",
    version="0.6.0",
    core_compatibility=">=0.1,<0.2",
    vocabulary_refs=["src/causa/institutional/contracts/vocabulary.py"],
    authority_model_refs=["src/causa/institutional/contracts/authority_model.py"],
    temporal_model_refs=["docs/first-institution-contracts.md#scope"],
    bootstrap_schema_refs=[
        "docs/bootstrap-pipeline-spec.md#phase-0-scope",
        "src/causa/institutional/contracts/reviewed_analysis.py",
    ],
    mapping_rule_refs=[
        "docs/bootstrap-pipeline-spec.md#translation-status",
        "src/causa/institutional/contracts/reviewed_analysis.py",
    ],
    contradiction_taxonomy_refs=["src/causa/institutional/contracts/contradiction_taxonomy.py"],
    legal_operator_refs=["docs/phase-0-backlog.md#p2-first-meaningful-legal-package-work"],
    benchmark_refs=["docs/evaluation-and-red-team-spec.md#phase-0-artifacts"],
    red_team_refs=["docs/evaluation-and-red-team-spec.md#red-team"],
    confidence_policy_refs=["docs/management-plane-spec.md#confidence-and-activation-policies"],
    activation_policy_refs=["docs/management-plane-spec.md#confidence-and-activation-policies"],
    domain_owner_responsibilities_ref="docs/institutional-packages.md#each-package-should-define",
    changelog_ref="docs/contracts-ru-v0-changelog.md",
    compatibility_matrix_ref="docs/contracts-ru-v0-compatibility.md#compatibility-matrix",
    migration_guide_ref="docs/contracts-ru-v0-compatibility.md#migration-guide",
    rollback_ref="docs/contracts-ru-v0-compatibility.md#rollback-path",
)
