from agent.planner import HypothesisPlanner
from agent.state import InvestigationState
from hypothesis.models import Hypothesis


def make_hypothesis(
    name,
    category,
    confidence=0.70,
    score=0.70,
    role="root_cause",
):
    return Hypothesis(
        name=name,
        category=category,
        role=role,
        confidence=confidence,
        score=score,
        severity="high",
        explanation="test hypothesis",
        matched_signals=[],
        missing_signals=[],
        evidence_score=0.7,
        specificity_score=0.7,
        temporal_score=0.5,
        contradiction_penalty=0.0,
        supporting_evidence=[],
        contradicting_evidence=[],
    )


def test_database_hypothesis_requests_database_evidence():
    state = InvestigationState(
        incident="database failure",
        service="payment-service",
    )

    state.evidence = type(
        "Evidence",
        (),
        {
            "signals": [
                "database_connection_failure",
            ]
        },
    )()

    hypothesis = make_hypothesis(
        "Database dependency unavailable",
        "database_failure",
    )

    state.hypotheses = [hypothesis]
    state.selected_hypothesis = hypothesis

    planner = HypothesisPlanner()

    action = planner.plan_for_hypothesis(
        hypothesis,
        state,
    )

    assert action is not None
    assert action.tool == "investigate_database"


def test_planner_does_not_repeat_database_investigation():
    state = InvestigationState(
        incident="database failure",
        service="payment-service",
    )

    state.evidence = type(
        "Evidence",
        (),
        {
            "signals": [
                "database_connection_failure",
            ]
        },
    )()

    state.tool_history = [
        "investigate_database",
    ]

    hypothesis = make_hypothesis(
        "Database dependency unavailable",
        "database_failure",
    )

    state.hypotheses = [hypothesis]
    state.selected_hypothesis = hypothesis

    planner = HypothesisPlanner()

    action = planner.plan_for_hypothesis(
        hypothesis,
        state,
    )

    assert action is not None
    assert action.tool != "investigate_database"


def test_competing_hypotheses_can_trigger_discriminating_evidence():
    state = InvestigationState(
        incident="payment failure",
        service="payment-service",
    )

    database = make_hypothesis(
        "Database dependency unavailable",
        "database_failure",
        confidence=0.62,
        score=0.62,
    )

    application = make_hypothesis(
        "Application exception",
        "application_error",
        confidence=0.60,
        score=0.60,
        role="mechanism",
    )

    state.hypotheses = [
        database,
        application,
    ]

    planner = HypothesisPlanner()

    gaps = planner.identify_discriminating_gaps(
        state.hypotheses,
        state,
    )

    assert gaps
    assert gaps[0].tool == "investigate_database"