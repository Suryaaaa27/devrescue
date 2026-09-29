import asyncio
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]


async def run_github_mcp_test():
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_servers.github.server"],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:

            # ---------------------------------------------------------
            # MCP INITIALIZATION
            # ---------------------------------------------------------

            await session.initialize()

            # ---------------------------------------------------------
            # TOOLS/LIST
            # ---------------------------------------------------------

            tools = await session.list_tools()

            tool_names = {tool.name for tool in tools.tools}

            expected_tools = {
                "get_repository",
                "get_file",
                "search_code",
                "list_commits",
                "get_commit",
                "get_diff",
            }

            assert expected_tools.issubset(tool_names)

            # ---------------------------------------------------------
            # GET REPOSITORY
            # ---------------------------------------------------------

            repository_result = await session.call_tool(
                "get_repository",
                arguments={},
            )
            
            assert not repository_result.isError
            assert repository_result.structuredContent["status"] == "success"

            repository = repository_result.structuredContent["repository"]

            assert repository["full_name"] == "Suryaaaa27/devrescue"
            assert repository["default_branch"] == "main"

            # ---------------------------------------------------------
            # GET FILE
            # ---------------------------------------------------------

            file_result = await session.call_tool(
                "get_file",
                arguments={
                    "path": "README.md",
                },
            )

            assert not file_result.isError
            assert file_result.structuredContent["status"] == "success"

            file_data = file_result.structuredContent["file"]

            assert file_data["path"] == "README.md"
            assert "content" in file_data

            # ---------------------------------------------------------
            # SEARCH CODE
            # ---------------------------------------------------------

            search_result = await session.call_tool(
                "search_code",
                arguments={
                    "query": "FastAPI",
                    "limit": 5,
                },
            )

            assert not search_result.isError
            assert search_result.structuredContent["status"] == "success"

            assert "results" in search_result.structuredContent

            # ---------------------------------------------------------
            # LIST COMMITS
            # ---------------------------------------------------------

            commits_result = await session.call_tool(
                "list_commits",
                arguments={
                    "limit": 5,
                },
            )

            assert not commits_result.isError
            assert commits_result.structuredContent["status"] == "success"

            commits = commits_result.structuredContent["results"]

            assert len(commits) > 0

            commit_sha = commits[0]["sha"]

            assert commit_sha

            # ---------------------------------------------------------
            # GET COMMIT
            # ---------------------------------------------------------

            commit_result = await session.call_tool(
                "get_commit",
                arguments={
                    "sha": commit_sha,
                },
            )

            assert not commit_result.isError
            assert commit_result.structuredContent["status"] == "success"

            commit = commit_result.structuredContent["commit"]

            assert commit["sha"] == commit_sha

            # ---------------------------------------------------------
            # GET DIFF
            # ---------------------------------------------------------

            diff_result = await session.call_tool(
                "get_diff",
                arguments={
                    "sha": commit_sha,
                },
            )

            assert not diff_result.isError
            assert diff_result.structuredContent["status"] == "success"

            print("\nActual get_diff structured content:")
            print(diff_result.structuredContent)

            assert diff_result.structuredContent["status"] == "success"
            assert "files" in diff_result.structuredContent

            # ---------------------------------------------------------
            # FINAL ASSERTION
            # ---------------------------------------------------------

            return {
                "repository": repository["full_name"],
                "commit_sha": commit_sha,
                "tools": sorted(tool_names),
            }


def test_github_mcp_integration():
    result = asyncio.run(run_github_mcp_test())

    assert result["repository"] == "Suryaaaa27/devrescue"
    assert len(result["tools"]) == 6
    assert result["commit_sha"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])