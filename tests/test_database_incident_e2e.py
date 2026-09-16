import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from agent.investigator import InvestigationAgent


def fake_health():
    return {
        "service": "payment-service",
        "status": "degraded",
    }


def fake_search_logs(**kwargs):
    return {
        "query": "",
        "service": kwargs.get("service"),
        "count": 1,
        "results": [
            {
                "timestamp": "2026-09-10T16:30:00Z",
                "service": "payment-service",
                "level": "ERROR",
                "message": (
                    "database connection refused "
                    "postgresql://payments-db"
                ),
                "trace_id": "trace-db-001",
                "span_id": "span-db-001",
                "request_id": "req-db-001",
            }
        ],
    }


def fake_database_investigation(**kwargs):
    return {
        "service": kwargs.get("service"),
        "database": "payments-db",
        "status": "unavailable",
        "error": "connection refused",
    }


def test_database_failure_incident():

    tools = {
        "get_service_health": fake_health,
        "search_logs": fake_search_logs,
        "investigate_database": (
            fake_database_investigation
        ),
    }

    agent = InvestigationAgent(
        tools=tools,
        max_iterations=5,
    )

    result = agent.investigate(
        incident=(
            "Payment failures are occurring because "
            "the payments database is unavailable."
        ),
        service="payment-service",
    )

    assert result.root_cause == (
        "Database dependency unavailable"
    )

    assert result.hypotheses

    assert result.hypotheses[0]["category"] == (
        "database_failure"
    )

    assert (
        "database_connection_failure"
        in result.evidence_summary["signals"]
    )

    assert (
        "investigate_database"
        in result.tools_called
    )
    
    assert any(
        plan["tool"] == "investigate_database"
        and "database dependency" in plan["reason"].lower()
        for plan in result.planning_history
    )