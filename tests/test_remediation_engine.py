from hypothesis.models import Hypothesis
from evidence.models import CodeEvidence
from remediation.engine import RemediationEngine


def database_hypothesis():
    return Hypothesis(
        name="Database dependency unavailable",
        category="database_failure",
        role="root_cause",
        confidence=0.82,
        score=0.88,
        explanation=(
            "The database dependency is unavailable "
            "because its connection was refused."
        ),
        severity="high",
    )


def application_hypothesis():
    return Hypothesis(
        name="Application exception",
        category="application_error",
        role="root_cause",
        confidence=0.82,
        score=0.80,
        explanation=(
            "The application generated an exception "
            "during request processing."
        ),
        severity="high",
    )


def invalid_input_hypothesis():
    return Hypothesis(
        name="Invalid payment input",
        category="application_validation",
        role="root_cause",
        confidence=0.90,
        score=0.92,
        explanation=(
            "The payment request contains invalid input."
        ),
        severity="medium",
    )


def test_database_remediation_proposal():

    engine = RemediationEngine()

    decision = engine.propose(
        database_hypothesis(),
        {
            "database": [
                {
                    "database": "payments",
                    "status": "unavailable",
                    "error": "connection refused",
                }
            ]
        },
    )

    assert decision.allowed
    assert decision.proposal is not None

    proposal = decision.proposal

    assert proposal.hypothesis == (
        "Database dependency unavailable"
    )

    assert proposal.category == "database_failure"

    assert proposal.risk_level == "high"

    assert proposal.requires_human_approval is True

    assert proposal.patch_generation_allowed is False

    assert proposal.actions

    assert any(
        action.action_type
        == "restore_database_connectivity"
        for action in proposal.actions
    )


def test_application_exception_is_patchable_when_code_exists():

    engine = RemediationEngine()

    decision = engine.propose(
        application_hypothesis(),
        {
            "code": [
                {
                    "path": (
                        "services/payment_service/main.py"
                    )
                }
            ]
        },
    )

    assert decision.allowed
    assert decision.proposal is not None

    proposal = decision.proposal

    assert proposal.patch_generation_allowed is True

    assert (
        "services/payment_service/main.py"
        in proposal.affected_files
    )


def test_invalid_input_remediation():

    engine = RemediationEngine()

    decision = engine.propose(
        invalid_input_hypothesis(),
        {
            "code": [
                {
                    "path": (
                        "services/payment_service/main.py"
                    )
                }
            ]
        },
    )

    assert decision.allowed
    assert decision.proposal is not None

    assert decision.proposal.patch_generation_allowed is True


def test_non_root_cause_is_rejected():
    hypothesis = Hypothesis(
        name="Application exception",
        category="application_error",
        role="mechanism",
        confidence=0.90,
        score=0.90,
        explanation="The application generated an exception during request processing.",
        severity="high",
    )

    evidence_summary = {
        "code": [
            {
                "path": "services/payment_service/main.py",
                "content": "raise HTTPException(...)",
            }
        ]
    }

    decision = RemediationEngine().propose(
        hypothesis,
        evidence_summary,
    )

    assert decision.allowed is False
    assert "root-cause" in decision.reason.lower()


def test_low_confidence_is_rejected():

    engine = RemediationEngine()

    hypothesis = Hypothesis(
        name="Database dependency unavailable",
        category="database_failure",
        role="root_cause",
        confidence=0.50,
        score=0.50,
        explanation=(
            "The database dependency may be unavailable."
        ),
        severity="high",
    )

    decision = engine.propose(
        hypothesis,
        {
            "database": [
                {
                    "database": "payments",
                    "status": "unavailable",
                    "error": "connection refused",
                }
            ]
        },
    )

    assert decision.allowed is False
    assert decision.proposal is None


def test_unknown_hypothesis_category_is_rejected():

    engine = RemediationEngine()

    hypothesis = Hypothesis(
        name="Unknown failure",
        category="unknown_category",
        role="root_cause",
        confidence=0.90,
        score=0.90,
        explanation="Unknown",
        severity="high",
    )

    decision = engine.propose(
        hypothesis,
        {"code": []},
    )

    assert decision.allowed is False
    assert decision.proposal is None


def test_database_proposal_requires_human_approval():

    engine = RemediationEngine()

    decision = engine.propose(
        database_hypothesis(),
        {
            "database": [
                {
                    "database": "payments",
                    "status": "unavailable",
                    "error": "connection refused",
                }
            ]
        },
    )

    proposal = decision.proposal

    assert proposal is not None

    assert (
        proposal.requires_human_approval
        is True
    )

    assert all(
        action.requires_approval
        for action in proposal.actions
    )


def test_proposal_serialization():

    engine = RemediationEngine()

    decision = engine.propose(
        invalid_input_hypothesis(),
        {
            "code": [
                {
                    "path": (
                        "services/payment_service/main.py"
                    )
                }
            ]
        },
    )

    payload = decision.to_dict()

    assert payload["allowed"] is True
    assert payload["proposal"]["hypothesis"] == (
        "Invalid payment input"
    )
    assert payload["proposal"]["actions"]
    assert (
        payload["proposal"]["requires_human_approval"]
        is True
    )
