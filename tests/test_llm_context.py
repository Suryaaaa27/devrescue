from agent.llm.context import build_llm_context
from agent.state import InvestigationState
from agent.uncertainty import UncertaintyAssessment


def test_build_llm_context():

    state = InvestigationState(
        incident="Payment failed",
        service="payment-service",
    )

    uncertainty = UncertaintyAssessment(
        leading_hypothesis="Invalid payment input",
        leading_confidence=0.95,
        runner_up_hypothesis="Application exception",
        runner_up_confidence=0.40,
        confidence_gap=0.55,
        uncertainty=0.17,
        independent_evidence_count=3,
        sufficient_confidence=True,
        sufficient_separation=True,
        should_continue=False,
        reason="Evidence strongly supports the leading hypothesis.",
    )

    context = build_llm_context(
        state,
        uncertainty,
    )

    assert context["incident"] == "Payment failed"
    assert context["service"] == "payment-service"

    assert "evidence_summary" in context
    assert "hypotheses" in context
    assert "uncertainty" in context
    assert "investigation_history" in context

    assert (
        context["uncertainty"]["leading_hypothesis"]
        == "Invalid payment input"
    )