import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_servers/observability/server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            # 1. Initialize MCP connection
            await session.initialize()

            print("\n=== MCP INITIALIZED ===")

            # 2. Discover available tools
            tools = await session.list_tools()

            print("\n=== AVAILABLE TOOLS ===")

            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            # 3. Call search_logs through MCP
            result = await session.call_tool(
                "search_logs",
                arguments={
                    "query": "payment_success",
                    "service": "payment-service",
                    "limit": 10,
                },
            )
            
            print("\n=== search_logs RESULT ===")
            
            for content in result.content:
                if hasattr(content, "text"):
                    print(content.text)
                else:
                    print(content)
            
            # 4. Query metrics through MCP
            metric_result = await session.call_tool(
                "query_metrics",
                arguments={
                    "query": "payment_requests_total",
                },
            )

            print("\n=== query_metrics RESULT ===")

            for content in metric_result.content:
                if hasattr(content, "text"):
                    print(content.text)
                else:
                    print(content)

            # 5. Find traces through MCP
            trace_result = await session.call_tool(
                "find_traces",
                arguments={
                    "service": "payment-service",
                    "trace_id": "f83d1eadb5451abfe8f913cead3922d9",
                    "limit": 5,
                },
            )

            print("\n=== find_traces RESULT ===")

            for content in trace_result.content:
                if hasattr(content, "text"):
                    print(content.text)
                else:
                    print(content)

if __name__ == "__main__":
    asyncio.run(main())