import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
    )
)

from agent.planner import HypothesisPlanner
from agent.state import InvestigationState
from evidence.models import InvestigationEvidence
from hypothesis.models import Hypothesis


def build_database_hypothesis():

    return Hypothesis(
        name="Database dependency unavailable",
        category="database_failure",
        role="root_cause",
        confidence=0.80,
        score=0.78,
        severity="high",
        explanation=(
            "The database dependency is unavailable."
        ),
        matched_signals=[
            "database_connection_failure",
            "database_unavailable",
        ],
        missing_signals=[],
        evidence_score=0.9,
        specificity_score=0.95,
        temporal_score=0.0,
        contradiction_penalty=0.0,
        supporting_evidence=[],
        contradicting_evidence=[],
    )


def test_database_hypothesis_selects_database_investigation():

    evidence = InvestigationEvidence(
        service="payment-service",
        signals=[
            "error_log",
            "database_connection_failure",
        ],
    )

    state = InvestigationState(
        incident="payment database failure",
        service="payment-service",
        evidence=evidence,
    )

    hypothesis = build_database_hypothesis()

    planner = HypothesisPlanner()

    action = planner.plan_for_hypothesis(
        hypothesis,
        state,
    )

    assert action is not None

    assert action.tool == (
        "investigate_database"
    )

    assert action.arguments == {
        "service": "payment-service",
    }

    assert (
        "database_health"
        in action.reason
    )


def test_planner_does_not_repeat_database_investigation():

    evidence = InvestigationEvidence(
        service="payment-service",
        signals=[
            "error_log",
            "database_connection_failure",
        ],
    )

    state = InvestigationState(
        incident="payment database failure",
        service="payment-service",
        evidence=evidence,
    )

    state.tool_history.append(
        "investigate_database"
    )

    hypothesis = build_database_hypothesis()

    planner = HypothesisPlanner()

    action = planner.plan_for_hypothesis(
        hypothesis,
        state,
    )

    assert action is not None

    assert action.tool != (
        "investigate_database"
    )