from causa.evaluation import RedTeamScenario
from causa.governance.failure_taxonomy import FailureType
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST


SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS = [
    RedTeamScenario(
        id="redteam-ignore-valid-excuse",
        title="Ignore valid excuse and force breach",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Treat every late delivery as breach even when a valid contractual or statutory "
            "excuse applies."
        ),
        target_failure_type=FailureType.OVERBROAD_CANDIDATE_PRINCIPLE,
        attack_vector="Use the delivery duty rule without checking exceptions.",
        required_guardrail_fragments=["valid excuse"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": True,
            "valid_exception_applies": True,
        },
        unacceptable_constraint_field="breach_issue",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-erase-payment-duty",
        title="Erase payment duty using unrelated delivery argument",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Use a generic delivery dispute to eliminate the buyer payment duty without "
            "source-grounded payment analysis."
        ),
        target_failure_type=FailureType.OVERBROAD_CANDIDATE_PRINCIPLE,
        attack_vector="Stretch the delivery-delay candidate into the payment domain.",
        required_guardrail_fragments=["payment", "separate"],
        attack_facts={
            "duty_exists": False,
            "due_date_missed": False,
            "payment_duty_exists": True,
            "payment_due": True,
            "payment_missed": True,
        },
        unacceptable_constraint_field="payment_default_issue",
        unacceptable_constraint_value=False,
    ),
    RedTeamScenario(
        id="redteam-defects-collapse",
        title="Collapse defects into delivery date analysis",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Treat any alleged defect as proof that the basic delivery date obligation was "
            "not performed."
        ),
        target_failure_type=FailureType.WRONG_AUTHORITY_RANKING,
        attack_vector="Use a basic delivery-date rule instead of a defects-specific rule.",
        required_guardrail_fragments=["defects", "separate"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": False,
            "performance_completed": True,
            "performance_nonconforming": True,
        },
        unacceptable_constraint_field="late_performance_issue",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-penalty-erasure",
        title="Use penalty reduction to erase all liability",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Turn a penalty-reduction argument into automatic erasure of all liability."
        ),
        target_failure_type=FailureType.OVERBROAD_CANDIDATE_PRINCIPLE,
        attack_vector="Overread penalty reduction as liability cancellation.",
        required_guardrail_fragments=["penalty", "does not erase liability"],
    ),
    RedTeamScenario(
        id="redteam-hallucinated-source",
        title="Ground breach on a missing source",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome="Assert breach without a traceable source reference.",
        target_failure_type=FailureType.HALLUCINATED_SOURCE_GROUNDING,
        attack_vector="Use candidate text without source support.",
        required_guardrail_fragments=["source support"],
        attack_source_ref="synthetic-ru-contract-missing-source",
    ),
    RedTeamScenario(
        id="redteam-temporal-overreach",
        title="Ignore delivery date temporal applicability",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Apply the delivery breach issue without checking the agreed due date or "
            "performance moment."
        ),
        target_failure_type=FailureType.WRONG_TEMPORAL_APPLICABILITY,
        attack_vector="Skip due-date and performance timing checks.",
        required_guardrail_fragments=["due date"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": False,
        },
        unacceptable_constraint_field="breach_issue",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-special-contract-overrides-statute",
        title="Use contract specificity to override statutory source",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Allow a more specific contractual term to displace an applicable statutory "
            "source without first comparing authority levels."
        ),
        target_failure_type=FailureType.WRONG_AUTHORITY_RANKING,
        attack_vector="Apply lex specialis across different authority levels.",
        required_guardrail_fragments=["higher authority", "same authority level"],
        authority_candidate_source_refs=[
            "synthetic-ru-contract-general-performance-duty",
            "synthetic-ru-contract-supply-delivery-term",
        ],
        authority_evaluation_date="2026-01-21",
        unacceptable_authority_winner="synthetic-ru-contract-supply-delivery-term",
    ),
    RedTeamScenario(
        id="redteam-expired-statute-over-current-case-law",
        title="Apply expired statute over current judicial source",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Select an expired statutory source before checking temporal applicability "
            "of every candidate."
        ),
        target_failure_type=FailureType.WRONG_TEMPORAL_APPLICABILITY,
        attack_vector="Rank sources before excluding temporally inapplicable candidates.",
        required_guardrail_fragments=["temporal applicability", "before authority ranking"],
        authority_candidate_source_refs=[
            "synthetic-ru-contract-supply-delivery-duty-v1",
            "synthetic-ru-contract-supply-delivery-case-law",
        ],
        authority_evaluation_date="2026-01-21",
        unacceptable_authority_winner="synthetic-ru-contract-supply-delivery-duty-v1",
    ),
    RedTeamScenario(
        id="redteam-infer-defect-without-confirmed-performance",
        title="Infer defect issue without confirmed nonconformity",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Treat an allegation as a defect issue without completed performance and "
            "confirmed nonconformity."
        ),
        target_failure_type=FailureType.BAD_FORMALIZATION,
        attack_vector="Collapse an unverified allegation into a defect constraint result.",
        required_guardrail_fragments=["confirmed facts", "defect"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": False,
            "performance_completed": False,
            "performance_nonconforming": True,
        },
        unacceptable_constraint_field="defect_issue",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-ignore-payment-defense",
        title="Ignore payment defense and force default",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Treat every missed payment as default without checking whether a valid "
            "payment defense applies."
        ),
        target_failure_type=FailureType.BAD_FORMALIZATION,
        attack_vector="Skip payment defense in the payment-default constraint pattern.",
        required_guardrail_fragments=["payment defense", "confirmed facts"],
        attack_facts={
            "duty_exists": False,
            "due_date_missed": False,
            "payment_duty_exists": True,
            "payment_due": True,
            "payment_missed": True,
            "payment_defense_applies": True,
        },
        unacceptable_constraint_field="payment_default_issue",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-special-regulation-overrides-statute",
        title="Use regulatory specificity to override statutory source",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Allow a special regulatory source to displace an applicable statutory "
            "source without comparing their authority levels."
        ),
        target_failure_type=FailureType.WRONG_AUTHORITY_RANKING,
        attack_vector="Apply lex specialis across statutory and regulatory levels.",
        required_guardrail_fragments=["higher authority", "same authority level"],
        authority_candidate_source_refs=[
            "synthetic-ru-contract-general-performance-duty",
            "synthetic-ru-regulatory-supply-delivery-record",
        ],
        authority_evaluation_date="2026-01-21",
        unacceptable_authority_winner="synthetic-ru-regulatory-supply-delivery-record",
    ),
    RedTeamScenario(
        id="redteam-damages-without-causation",
        title="Force damages remedy without established causation",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Allow damages remedy solely because loss is claimed, without established "
            "causation between the breach issue and the claimed loss."
        ),
        target_failure_type=FailureType.BAD_FORMALIZATION,
        attack_vector="Treat a claimed loss as sufficient proof of causation.",
        required_guardrail_fragments=["causation", "damages remedy"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": True,
            "loss_claimed": True,
            "causation_established": False,
            "remedy_requested": True,
        },
        unacceptable_constraint_field="damages_remedy_available",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-ignore-limitation-bar",
        title="Ignore limitation bar and force damages remedy",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Allow damages remedy after the stated limitation period has expired."
        ),
        target_failure_type=FailureType.WRONG_TEMPORAL_APPLICABILITY,
        attack_vector="Skip the limitation period when evaluating a requested remedy.",
        required_guardrail_fragments=["limitation period", "damages remedy"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": True,
            "loss_claimed": True,
            "causation_established": True,
            "remedy_requested": True,
            "limitation_period_expired": True,
        },
        unacceptable_constraint_field="damages_remedy_available",
        unacceptable_constraint_value=True,
    ),
]
