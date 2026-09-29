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
        "service": "payment-service",
        "status": "degraded",
    }


def fake_logs(**kwargs):

    return {
        "service": "payment-service",
        "count": 1,
        "results": [
            {
                "timestamp": (
                    "2026-09-18T10:00:00Z"
                ),
                "service": "payment-service",
                "level": "ERROR",
                "message": (
                    "Payment amount must be "
                    "greater than zero."
                ),
                "trace_id": "trace-001",
                "span_id": "span-001",
                "request_id": "req-001",
            }
        ],
    }

def fake_search_code(**kwargs):

    return {
        "status": "success",
        "query": kwargs.get("query"),
        "repository": "Suryaaaa27/devrescue",
        "total_count": 1,
        "results": [
            {
                "name": "main.py",
                "path": (
                    "services/payment_service/main.py"
                ),
                "sha": "abc123",
                "html_url": (
                    "https://github.com/"
                    "Suryaaaa27/devrescue/"
                    "blob/main/"
                    "services/payment_service/main.py"
                ),
                "repository": (
                    "Suryaaaa27/devrescue"
                ),
            }
        ],
    }


def test_agent_uses_decision_driven_search_code():

    tools = {
        "get_service_health": fake_health,
        "search_logs": fake_logs,
        "search_code": fake_search_code,
    }

    agent = InvestigationAgent(
        tools=tools,
        max_iterations=5,
    )

    result = agent.investigate(
        incident="payment failure",
        service="payment-service",
    )

    assert "search_code" in result.tools_called

    assert result.tools_called.count(
        "search_code"
    ) == 1