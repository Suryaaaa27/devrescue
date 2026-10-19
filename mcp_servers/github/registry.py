from __future__ import annotations

from typing import Any, Callable

from mcp_servers.github import server


GITHUB_READ_TOOLS: dict[str, Callable[..., Any]] = {
    "get_repository": server.get_repository,
    "get_file": server.get_file,
    "search_code": server.search_code,
    "list_commits": server.list_commits,
    "get_commit": server.get_commit,
    "get_diff": server.get_diff,
}


GITHUB_WRITE_TOOLS: dict[str, Callable[..., Any]] = {
    "create_branch": server.create_branch,
    "create_or_update_file": server.create_or_update_file,
    "create_pull_request": server.create_pull_request,
    "close_pull_request": server.close_pull_request,
    "delete_branch": server.delete_branch,
}


def build_github_read_tools() -> dict[str, Callable[..., Any]]:
    """Return read-only GitHub tools."""
    return dict(GITHUB_READ_TOOLS)


def build_github_write_tools() -> dict[str, Callable[..., Any]]:
    """Return explicitly approved GitHub write tools."""
    return dict(GITHUB_WRITE_TOOLS)
