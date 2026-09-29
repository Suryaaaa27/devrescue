from agent.planner import HypothesisPlanner
from agent.state import InvestigationState
from hypothesis.models import Hypothesis
from evidence.models import (
    InvestigationEvidence,
    TraceEvidence,
    SpanEvidence,
    TraceLogEvidence,
)


def test_application_error_can_request_github_code():

    state = InvestigationState(
        incident="payment service is failing",
        service="payment-service",
    )

    state.available_tools = {
        "search_code",
        "list_commits",
        "get_file",
        "get_diff",
    }

    hypothesis = Hypothesis(
        name="Application exception",
        category="application_error",
        role="mechanism",
        score=0.7,
        confidence=0.7,
        explanation=(
            "The application error may be caused by a defect "
            "in the source code."
        ),
    )

    planner = HypothesisPlanner()

    gaps = planner.identify_gaps(
        hypothesis=hypothesis,
        state=state,
    )

    assert gaps
    assert gaps[0].tool == "search_code"
    assert gaps[0].name == "relevant_source_code"


def test_github_tools_are_not_selected_when_already_called():

    state = InvestigationState(
        incident="payment service is failing",
        service="payment-service",
    )

    state.available_tools = {
        "search_code",
        "list_commits",
        "get_file",
        "get_diff",
    }

    state.tool_history.append("search_code")

    hypothesis = Hypothesis(
        name="Application exception",
        category="application_error",
        role="mechanism",
        score=0.7,
        confidence=0.7,
        explanation=(
            "The application error may be caused by a defect "
            "in the source code."
        ),
    )

    planner = HypothesisPlanner()

    gaps = planner.identify_gaps(
        hypothesis=hypothesis,
        state=state,
    )

    assert gaps
    assert gaps[0].tool == "list_commits"
    
def test_search_code_query_uses_exception_evidence():
    planner = HypothesisPlanner()

    hypothesis = Hypothesis(
        name="Application error",
        category="application_error",
        role="mechanism",
        explanation="The application may be raising an exception.",
        score=0.8,
        confidence=0.8,
    )

    state = InvestigationState(
        incident="Payment request failed",
        service="payment-service",
        available_tools={"search_code"},
    )

    state.evidence = InvestigationEvidence(
        service="payment-service",
        traces=[
            TraceEvidence(
                trace_id="trace-123",
                spans=[
                    SpanEvidence(
                        trace_id="trace-123",
                        span_id="span-123",
                        operation="POST /payments",
                        start_time=None,
                        duration=None,
                        logs=[
                            TraceLogEvidence(
                                timestamp=None,
                                fields={
                                    "exception.type": "HTTPException",
                                    "exception.message": (
                                        "Payment amount must be "
                                        "greater than zero."
                                    ),
                                },
                            )
                        ],
                    )
                ],
            )
        ],
    )

    gaps = planner.identify_gaps(
        hypothesis,
        state,
    )

    search_gap = next(
        gap
        for gap in gaps
        if gap.tool == "search_code"
    )

    query = search_gap.arguments["query"]

    assert "POST /payments" in query
    assert "HTTPException" in query
    
def test_search_code_query_falls_back_to_service():
    planner = HypothesisPlanner()

    hypothesis = Hypothesis(
        name="Application error",
        category="application_error",
        role="mechanism",
        explanation="The application may be failing.",
        score=0.8,
        confidence=0.8,
    )

    state = InvestigationState(
        incident="Unknown application failure",
        service="payment-service",
        available_tools={"search_code"},
    )

    state.evidence = InvestigationEvidence(
        service="payment-service"
    )

    gaps = planner.identify_gaps(
        hypothesis,
        state,
    )

    search_gap = next(
        gap
        for gap in gaps
        if gap.tool == "search_code"
    )

    assert search_gap.arguments["query"] == "Application error"