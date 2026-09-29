import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
    )
)

from agent.decision import InvestigationDecisionEngine
from agent.state import InvestigationState
from evidence.models import (
    InvestigationEvidence,
    LogEvidence,
    MetricEvidence,
)
from hypothesis.models import Hypothesis


def test_no_hypothesis_requests_more_investigation():

    state = InvestigationState(
        incident="payment failure",
        service="payment-service",
        max_iterations=5,
    )

    engine = InvestigationDecisionEngine()

    decision = engine.decide(state)

    assert decision.decision == "INVESTIGATE"
    assert decision.confidence == 0.0


def test_confident_root_cause_can_conclude():

    state = InvestigationState(
        incident="payment failure",
        service="payment-service",
        max_iterations=5,
    )

    state.evidence = InvestigationEvidence(
        service="payment-service",
        logs=[
            LogEvidence(
                timestamp="2026-09-18T10:00:00Z",
                service="payment-service",
                level="ERROR",
                message="payment failed",
            )
        ],
        metrics=[
            MetricEvidence(
                metric={
                    "__name__": "payment_failures"
                },
                value=5,
                query="payment_failures",
            )
        ],
    )

    state.selected_hypothesis = Hypothesis(
        name="Application exception",
        category="application_error",
        role="root_cause",
        confidence=0.85,
        score=0.85,
        explanation=(
            "The payment request is failing because "
            "the application raises an exception."
        ),
    )

    engine = InvestigationDecisionEngine()

    decision = engine.decide(state)

    assert decision.decision == "CONCLUDE"
    assert decision.selected_hypothesis == (
        "Application exception"
    )
    assert decision.confidence == 0.85


def test_low_confidence_hypothesis_requests_investigation():

    state = InvestigationState(
        incident="payment failure",
        service="payment-service",
        max_iterations=5,
    )

    state.iteration = 2

    state.selected_hypothesis = Hypothesis(
        name="Application exception",
        category="application_error",
        role="root_cause",
        confidence=0.55,
        score=0.55,
        explanation="Possible application failure.",
    )

    class Gap:
        tool = "search_code"

    state.evidence_gaps = [Gap()]

    engine = InvestigationDecisionEngine()

    decision = engine.decide(state)

    assert decision.decision == "INVESTIGATE"
    assert decision.selected_hypothesis == (
        "Application exception"
    )
    assert decision.next_action == "search_code"


def test_max_iterations_produces_insufficient_evidence():

    state = InvestigationState(
        incident="unknown failure",
        service="payment-service",
        max_iterations=3,
    )

    state.iteration = 3

    state.selected_hypothesis = Hypothesis(
        name="Unknown failure",
        category="application_error",
        role="mechanism",
        confidence=0.40,
        score=0.40,
        explanation="Evidence is incomplete.",
    )

    engine = InvestigationDecisionEngine()

    decision = engine.decide(state)

    assert (
        decision.decision
        == "INSUFFICIENT_EVIDENCE"
    )


def test_decision_serialization():

    state = InvestigationState(
        incident="payment failure",
        service="payment-service",
        max_iterations=5,
    )

    engine = InvestigationDecisionEngine()

    decision = engine.decide(state)

    data = decision.to_dict()

    assert data["decision"] == "INVESTIGATE"
    assert "reason" in data
    assert "confidence" in data
    assert "evidence_gaps" in data
    assert "next_action" in data
    
def test_agent_state_can_store_decision():

    state = InvestigationState(
        incident="payment failure",
        service="payment-service",
    )

    engine = InvestigationDecisionEngine()

    decision = engine.decide(state)

    state.decision = decision.to_dict()

    assert state.decision is not None
    assert state.decision["decision"] == "INVESTIGATE"


def test_decision_contains_machine_readable_fields():

    state = InvestigationState(
        incident="payment failure",
        service="payment-service",
    )

    engine = InvestigationDecisionEngine()

    decision = engine.decide(state)

    data = decision.to_dict()

    required_fields = {
        "decision",
        "reason",
        "selected_hypothesis",
        "confidence",
        "evidence_gaps",
        "next_action",
    }

    assert required_fields.issubset(data.keys())
    
def test_investigate_decision_provides_next_action():

    state = InvestigationState(
        incident="payment failure",
        service="payment-service",
        max_iterations=5,
    )

    state.iteration = 2

    state.selected_hypothesis = Hypothesis(
        name="Application exception",
        category="application_error",
        role="root_cause",
        confidence=0.55,
        score=0.55,
        explanation="Possible application failure.",
    )

    class Gap:
        name = "relevant_source_code"
        tool = "search_code"

    state.evidence_gaps = [Gap()]

    engine = InvestigationDecisionEngine()

    decision = engine.decide(state)

    assert decision.decision == "INVESTIGATE"
    assert decision.next_action == "search_code"
    assert decision.evidence_gaps == [
        "relevant_source_code"
    ]