import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]


async def main():
    server = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_servers.github.server"],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:

            # ---------------------------------------------------------
            # 1. MCP INITIALIZATION
            # ---------------------------------------------------------

            await session.initialize()
            print("MCP initialization: OK")

            # ---------------------------------------------------------
            # 2. TOOLS/LIST
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

            print("\nRegistered tools:")

            for name in sorted(tool_names):
                print(f"  - {name}")

            assert expected_tools.issubset(tool_names), (
                f"Missing tools: {expected_tools - tool_names}"
            )

            print("tools/list: OK")

            # ---------------------------------------------------------
            # 3. GET REPOSITORY
            # ---------------------------------------------------------

            result = await session.call_tool(
                "get_repository",
                arguments={},
            )

            print("\n[get_repository]")
            print(result)

            assert not result.isError
            print("get_repository: OK")

            # ---------------------------------------------------------
            # 4. GET FILE
            # ---------------------------------------------------------

            result = await session.call_tool(
                "get_file",
                arguments={
                    "path": "README.md",
                },
            )

            print("\n[get_file]")
            print(result)

            assert not result.isError
            print("get_file: OK")

            # ---------------------------------------------------------
            # 5. SEARCH CODE
            # ---------------------------------------------------------

            result = await session.call_tool(
                "search_code",
                arguments={
                    "query": "FastAPI",
                    "limit": 5,
                },
            )

            print("\n[search_code]")
            print(result)

            assert not result.isError
            print("search_code: OK")

            # ---------------------------------------------------------
            # 6. LIST COMMITS
            # ---------------------------------------------------------

            result = await session.call_tool(
                "list_commits",
                arguments={
                    "limit": 5,
                },
            )

            print("\n[list_commits]")
            print(result)

            assert not result.isError
            print("list_commits: OK")

            # ---------------------------------------------------------
            # 7. EXTRACT COMMIT SHA
            # ---------------------------------------------------------

            commit_sha = None

            if result.structuredContent:
                commits = result.structuredContent.get("commits", [])

                if commits:
                    commit_sha = commits[0].get("sha")

            assert commit_sha, "No commit SHA returned by list_commits"

            print(f"\nLatest commit SHA: {commit_sha}")

            # ---------------------------------------------------------
            # 8. GET COMMIT
            # ---------------------------------------------------------

            result = await session.call_tool(
                "get_commit",
                arguments={
                    "sha": commit_sha,
                },
            )

            print("\n[get_commit]")
            print(result)

            assert not result.isError
            print("get_commit: OK")

            # ---------------------------------------------------------
            # 9. GET DIFF
            # ---------------------------------------------------------

            result = await session.call_tool(
                "get_diff",
                arguments={
                    "sha": commit_sha,
                },
            )

            print("\n[get_diff]")
            print(result)

            assert not result.isError
            print("get_diff: OK")

            # ---------------------------------------------------------
            # FINAL
            # ---------------------------------------------------------

            print("\n========================================")
            print("GitHub MCP integration test: ALL PASSED")
            print("========================================")


if __name__ == "__main__":
    asyncio.run(main())