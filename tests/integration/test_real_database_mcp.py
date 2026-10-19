from pathlib import Path
import sys

from agent.mcp.registry import build_database_tools


def test_real_database_mcp_through_registry():
    project_root = str(Path(__file__).resolve().parents[2])

    tools = build_database_tools(
        python_executable=sys.executable,
        project_root=project_root,
    )

    result = tools["check_database_health"](
        service="payment-service"
    )

    assert result["status"] == "available"
    assert result["database"] == "payments"
    assert result["error"] is None
