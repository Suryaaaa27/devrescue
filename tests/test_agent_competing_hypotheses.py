from agent.investigator import InvestigationAgent
from agent.planner import HypothesisPlanner
from agent.state import InvestigationState
from hypothesis.models import Hypothesis

def make_hypothesis(
    name,
    category,
    confidence,
    score,
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


def test_agent_prefers_discriminating_evidence_for_close_hypotheses():
    state = InvestigationState(
        incident="Payment failures",
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

    state.selected_hypothesis = database

    planner = HypothesisPlanner()

    action = planner.plan_for_hypothesis(
        database,
        state,
    )

    assert action is not None
    assert action.tool == "investigate_database"

    assert "distinguish" in action.reason.lower()
    
def test_agent_bootstraps_database_investigation_from_incident():

    from agent.investigator import InvestigationAgent
    from agent.state import InvestigationState

    def fake_health(service):
        return {
            "service": service,
            "status": "unhealthy",
        }

    def fake_logs(service):
        return {
            "service": service,
            "logs": [
                {
                    "message": "database connection refused",
                    "level": "ERROR",
                }
            ],
        }

    def fake_database(service):
        return {
            "service": service,
            "database": "postgres",
            "status": "unavailable",
            "error": "connection refused",
        }

    agent = InvestigationAgent(
        tools={
            "get_service_health": fake_health,
            "search_logs": fake_logs,
            "investigate_database": fake_database,
        },
        max_iterations=5,
    )

    state = InvestigationState(
        incident="payment-service database failures",
        service="payment-service",
    )

    state.record_tool_call(
        "get_service_health",
        fake_health("payment-service"),
    )

    state.record_tool_call(
        "search_logs",
        fake_logs("payment-service"),
    )

    action = agent._plan_next_action(state)

    assert action is not None
    assert action.tool == "investigate_database"