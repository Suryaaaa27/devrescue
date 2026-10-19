import sys

from agent.mcp.registry import (
    DATABASE_TOOLS,
    GITHUB_TOOLS,
    OBSERVABILITY_TOOLS,
    build_mcp_tools,
)


def test_unified_mcp_registry_exposes_all_tools():

    tools = build_mcp_tools(
        python_executable=sys.executable,
        project_root=".",
    )

    expected_tools = (
        OBSERVABILITY_TOOLS
        | GITHUB_TOOLS
        | DATABASE_TOOLS
    )

    assert set(tools) == expected_tools
