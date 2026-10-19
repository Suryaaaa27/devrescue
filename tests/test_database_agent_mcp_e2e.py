import os
from pathlib import Path
import sys

from agent.investigator import InvestigationAgent
from agent.mcp.registry import build_database_tools


DATABASE_INCIDENT = (
    "Payment failures are occurring because "
    "the payments database is unavailable."
)


def test_agent_investigates_database_through_mcp(
    monkeypatch,
):


    # Point the MCP server at an intentionally unavailable
    # PostgreSQL endpoint so this E2E test exercises the
    # real database-failure path.
    monkeypatch.setenv(
        "DEVRESCUE_DATABASE_HOST",
        "localhost",
    )

    monkeypatch.setenv(
        "DEVRESCUE_DATABASE_PORT",
        "5999",
    )
    project_root = str(
        Path(__file__).resolve().parents[1]
    )
    database_tools = build_database_tools(
        python_executable=sys.executable,
        project_root=project_root,
    )

    agent = InvestigationAgent(
        tools=database_tools,
        max_iterations=4,
    )

    result = agent.investigate(
        incident=DATABASE_INCIDENT,
        service="payment-service",
    )

    assert result is not None

    # MCP boundary was actually used.
    assert (
        "investigate_database"
        in result.tools_called
    )

    # Public evidence contract.
    assert result.evidence_summary

    # Database investigation produced evidence.
    assert (
        result.evidence_summary.get(
            "database"
        )
        is not None
        or result.evidence_summary.get(
            "signals"
        )
    )

    # Hypothesis engine produced hypotheses.
    assert result.hypotheses

    assert (
        result.hypotheses[0]["category"]
        == "database_failure"
    )
