from pathlib import Path
import sys

from agent.mcp.registry import build_github_tools


def test_github_mcp_client_calls_real_server():

    project_root = str(
        Path(__file__).resolve().parents[1]
    )

    tools = build_github_tools(
        python_executable=sys.executable,
        project_root=project_root,
    )

    result = tools["get_repository"]()

    assert result["status"] == "success"
    assert result["repository"]["name"] == "devrescue"
