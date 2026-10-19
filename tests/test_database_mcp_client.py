from pathlib import Path
import sys

from agent.mcp.registry import build_database_tools


def test_database_mcp_client_calls_real_server():

    project_root = str(
        Path(__file__).resolve().parents[1]
    )

    tools = build_database_tools(
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
