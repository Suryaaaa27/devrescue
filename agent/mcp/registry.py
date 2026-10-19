from __future__ import annotations

from typing import Any, Callable

from agent.mcp.client import MCPToolClient


Tool = Callable[..., dict[str, Any]]


OBSERVABILITY_TOOLS = {
    "get_service_health",
    "search_logs",
    "query_metrics",
    "find_traces",
}


GITHUB_TOOLS = {
    "get_repository",
    "get_file",
    "search_code",
    "list_commits",
    "get_commit",
    "get_diff",
}


DATABASE_TOOLS = {
    "check_database_health",
    "investigate_database",
    "get_database_metadata",
}


GITHUB_WRITE_TOOLS = {
    "create_branch",
    "create_or_update_file",
    "create_pull_request",
    "close_pull_request",
    "delete_branch",
}
def _bind_tools(
    client: MCPToolClient,
    tool_names: set[str],
) -> dict[str, Tool]:
    """
    Convert MCP tools into the synchronous callable
    contract expected by InvestigationAgent.
    """

    return {
        tool_name: (
            lambda _tool_name=tool_name, **kwargs:
            client.call(
                _tool_name,
                kwargs,
            )
        )
        for tool_name in tool_names
    }


def build_observability_tools(
    python_executable: str,
    project_root: str,
) -> dict[str, Tool]:
    """
    Build MCP-backed Observability tools.
    """

    client = MCPToolClient(
        command=python_executable,
        args=[
            "-m",
            "mcp_servers.observability.server",
        ],
        cwd=project_root,
    )

    return _bind_tools(
        client,
        OBSERVABILITY_TOOLS,
    )


def build_github_tools(
    python_executable: str,
    project_root: str,
) -> dict[str, Tool]:
    """
    Build MCP-backed GitHub tools.
    """

    client = MCPToolClient(
        command=python_executable,
        args=[
            "-m",
            "mcp_servers.github.server",
        ],
        cwd=project_root,
    )

    return _bind_tools(
        client,
        GITHUB_TOOLS,
    )


def build_database_tools(
    python_executable: str,
    project_root: str,
) -> dict[str, Tool]:
    """
    Build MCP-backed Database tools.
    """

    client = MCPToolClient(
        command=python_executable,
        args=[
            "-m",
            "mcp_servers.database.server",
        ],
        cwd=project_root,
    )

    return _bind_tools(
        client,
        DATABASE_TOOLS,
    )


def build_mcp_tools(
    python_executable: str,
    project_root: str,
) -> dict[str, Tool]:
    """
    Build the complete DevRescue MCP tool registry.

    The returned dictionary is intentionally compatible with
    InvestigationAgent's existing Tool contract.
    """

    tools: dict[str, Tool] = {}

    tools.update(
        build_observability_tools(
            python_executable=python_executable,
            project_root=project_root,
        )
    )

    tools.update(
        build_github_tools(
            python_executable=python_executable,
            project_root=project_root,
        )
    )

    tools.update(
        build_database_tools(
            python_executable=python_executable,
            project_root=project_root,
        )
    )

    return tools

def build_github_write_tools(
    python_executable=None,
    project_root=None,
):
    import sys
    from pathlib import Path

    python_executable = python_executable or sys.executable
    project_root = project_root or str(Path.cwd())

    client = MCPToolClient(
        command=python_executable,
        args=["-m", "mcp_servers.github.server"],
        cwd=project_root,
    )

    return _bind_tools(
        client,
        GITHUB_WRITE_TOOLS,
    )
