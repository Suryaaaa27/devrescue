from pathlib import Path
import sys

from agent.mcp.registry import build_mcp_tools


def test_unified_registry_calls_database_mcp():

    project_root = str(
        Path(__file__).resolve().parents[1]
    )

    tools = build_mcp_tools(
        python_executable=sys.executable,
        project_root=project_root,
    )

    result = tools["investigate_database"](
        service="payment-service"
    )

    assert result["service"] == "payment-service"
    assert result["database"] == "payments"
    assert result["status"] == "available"
    assert result["error"] is None
