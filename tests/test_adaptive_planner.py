import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
    )
)

from agent.investigator import InvestigationAgent


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


def fake_health():
    return {
        "service": "payment-service",
        "status": "degraded",
    }


def fake_database_investigation(**kwargs):
    return {
        "service": kwargs.get("service"),
        "database": "payments-db",
        "status": "unavailable",
        "error": "connection refused",
    }


def test_database_adaptive_planning():

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
        incident="payment-service database failures",
        service="payment-service",
    )

    print(result.to_dict())

    assert result.status == (
        "ROOT_CAUSE_IDENTIFIED"
    )

    assert result.root_cause == (
        "Database dependency unavailable"
    )

    assert result.confidence >= 0.75

    assert result.tools_called == [
        "get_service_health",
        "search_logs",
        "investigate_database",
    ]

    assert (
        result.tools_called.count(
            "investigate_database"
        )
        == 1
    )

    assert (
        "database_unavailable"
        in result.evidence_summary["signals"]
    )

    assert (
        "database_connection_failure"
        in result.evidence_summary["signals"]
    )

    assert (
        result.evidence_summary[
            "domain_evidence_count"
        ]
        == 1
    )