from causa.core.knowledge_graph import (
    DecisionTrace,
    KnowledgeLayer,
    KnowledgeNode,
    VersionCoordinates,
)
from causa.evaluation import IncidentRecord, RedTeamScenario
from causa.governance.failure_taxonomy import FailureType
from causa.translation import TranslationArtifact, TranslationLevel


def test_decision_trace_records_version_coordinates() -> None:
    trace = DecisionTrace(
        id="trace-1",
        case_id="case-1",
        versions=VersionCoordinates(
            knowledge_version="knowledge-v0",
            institutional_package_version="contracts-ru-v0.1.0",
            policy_version="policy-v0",
            translation_template_version="translation-v0",
        ),
        nodes=[
            KnowledgeNode(
                id="source-1",
                layer=KnowledgeLayer.SOURCE,
                label="Synthetic source",
            )
        ],
    )

    assert trace.versions.policy_version == "policy-v0"
    assert trace.nodes[0].layer == KnowledgeLayer.SOURCE


def test_translation_artifact_has_governed_template_version() -> None:
    artifact = TranslationArtifact(
        id="translation-1",
        trace_id="trace-1",
        level=TranslationLevel.PROFESSIONAL,
        template_version="translation-v0",
        text="Professional legal explanation placeholder.",
    )

    assert artifact.template_version == "translation-v0"
    assert artifact.level == TranslationLevel.PROFESSIONAL


def test_red_team_scenario_targets_failure_type() -> None:
    scenario = RedTeamScenario(
        id="red-team-1",
        title="Overbroad penalty reduction",
        institutional_package_id="contracts-ru-v0",
        unacceptable_outcome="Erase all liability despite breach.",
        target_failure_type=FailureType.OVERBROAD_CANDIDATE_PRINCIPLE,
    )
    incident = IncidentRecord(
        id="incident-1",
        failure_type=scenario.target_failure_type,
        description="Candidate principle was too broad.",
    )

    assert incident.failure_type == FailureType.OVERBROAD_CANDIDATE_PRINCIPLE
