import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
    )
)

from agent.investigator import InvestigationAgent


def fake_health(**kwargs):

    return {
        "service": kwargs.get(
            "service"
        ),
        "status": "degraded",
    }


def fake_logs(**kwargs):

    return {
        "results": [
            {
                "timestamp": (
                    "2026-09-10T16:30:00Z"
                ),
                "service": "payment-service",
                "level": "ERROR",
                "message": (
                    "database connection refused"
                ),
                "trace_id": "trace-001",
                "span_id": "span-001",
                "request_id": "req-001",
            }
        ]
    }


def fake_database(**kwargs):

    return {
        "service": kwargs.get(
            "service"
        ),
        "database": "payments-db",
        "status": "unavailable",
        "error": "connection refused",
    }


def test_investigation_exposes_planning_history():

    agent = InvestigationAgent(
        tools={
            "get_service_health": fake_health,
            "search_logs": fake_logs,
            "investigate_database": fake_database,
        },
        max_iterations=5,
    )

    result = agent.investigate(
        incident=(
            "payment-service database failures"
        ),
        service="payment-service",
    )

    assert (
        result.status
        == "ROOT_CAUSE_IDENTIFIED"
    )

    assert (
        result.root_cause
        == "Database dependency unavailable"
    )

    assert result.planning_history

    tools = [
        item["tool"]
        for item in result.planning_history
    ]

    assert (
        "get_service_health"
        in tools
    )

    assert (
        "search_logs"
        in tools
    )

    assert (
        "investigate_database"
        in tools
    )

    database_plans = [
        item
        for item in result.planning_history
        if item["tool"]
        == "investigate_database"
    ]

    assert len(
        database_plans
    ) == 1

    database_plan = database_plans[0]

    assert (
        database_plan["hypothesis"]
        is None
    )
    assert (
    database_plan["mode"]
    == "discovery"
    )
    assert (
       "database"
       in database_plan["reason"].lower()
    )
    assert (
       "database dependency failure"
        in database_plan["reason"].lower()
    )

    assert (
        result.investigation_notes
        == []
    )
    
def test_planning_history_records_hypothesis_when_hypothesis_drives_action():

    from agent.models import InvestigationAction
    from agent.state import InvestigationState
    from hypothesis.models import Hypothesis

    agent = InvestigationAgent(
        tools={},
        max_iterations=5,
    )

    evidence = agent.evidence_engine.build(
        service="payment-service",
        log_result={
            "results": [
                {
                    "timestamp": (
                        "2026-09-10T16:30:00Z"
                    ),
                    "service": "payment-service",
                    "level": "ERROR",
                    "message": (
                        "database connection refused"
                    ),
                    "trace_id": "trace-001",
                    "span_id": "span-001",
                    "request_id": "req-001",
                }
            ]
        },
        metric_results=[],
        trace_result={},
    )

    evidence.signals.extend(
        [
            "database_connection_failure",
        ]
    )

    state = InvestigationState(
        incident=(
            "payment-service database failure"
        ),
        service="payment-service",
        evidence=evidence,
    )

    hypothesis = Hypothesis(
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
        ],
        missing_signals=[],
        evidence_score=0.9,
        specificity_score=0.95,
        temporal_score=0.0,
        contradiction_penalty=0.0,
        supporting_evidence=[],
        contradicting_evidence=[],
    )

    state.hypotheses = [
        hypothesis
    ]

    state.selected_hypothesis = (
        hypothesis
    )

    action = (
        agent.hypothesis_planner
        .plan_for_hypothesis(
            hypothesis,
            state,
        )
    )

    assert action is not None

    assert (
        action.tool
        == "investigate_database"
    )

    state.iteration = 3

    state.record_plan(
        tool=action.tool,
        reason=action.reason,
        hypothesis=(
            state.selected_hypothesis.name
        ),
    )

    assert (
        len(state.planning_history)
        == 1
    )

    assert (
        state.planning_history[0][
            "hypothesis"
        ]
        == "Database dependency unavailable"
    )
    assert (
    state.planning_history[0][
        "mode"
    ]
    == "hypothesis_driven"
    )

    assert (
        "database_health"
        in state.planning_history[0][
            "reason"
        ]
    )
    
def test_planning_modes_are_explicit():

    from agent.state import InvestigationState

    state = InvestigationState(
        incident="test incident",
        service="payment-service",
    )

    state.iteration = 1

    state.record_plan(
        tool="search_logs",
        reason="Initial evidence collection.",
    )

    state.iteration = 2

    state.record_plan(
        tool="investigate_database",
        reason=(
            "Investigate missing database health."
        ),
        hypothesis=(
            "Database dependency unavailable"
        ),
    )

    assert (
        state.planning_history[0]["mode"]
        == "discovery"
    )

    assert (
        state.planning_history[1]["mode"]
        == "hypothesis_driven"
    )

    assert (
        state.planning_history[0]["hypothesis"]
        is None
    )

    assert (
        state.planning_history[1]["hypothesis"]
        == "Database dependency unavailable"
    )