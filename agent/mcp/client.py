from __future__ import annotations

import asyncio
import os
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPToolClient:
    """
    Synchronous adapter around an MCP stdio client.

    The investigation agent currently expects tools with the
    synchronous contract:

        callable(**arguments) -> dict

    This class keeps that contract while communicating with
    MCP servers asynchronously underneath.
    """

    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
    ) -> None:
        self.server_parameters = StdioServerParameters(
            command=command,
            args=args,
            cwd=cwd,
            env=os.environ.copy(),
        )

    async def _call_async(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:

        async with stdio_client(
            self.server_parameters
        ) as (read, write):

            async with ClientSession(
                read,
                write,
            ) as session:

                await session.initialize()

                result = await session.call_tool(
                    tool_name,
                    arguments=arguments,
                )

                return self._normalize_result(
                    result
                )

    def call(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        return asyncio.run(
            self._call_async(
                tool_name=tool_name,
                arguments=arguments or {},
            )
        )

    @staticmethod
    def _normalize_result(
        result: Any,
    ) -> dict[str, Any]:

        if hasattr(result, "structuredContent"):
            structured = result.structuredContent

            if isinstance(structured, dict):
                return structured

        if hasattr(result, "structured_content"):
            structured = result.structured_content

            if isinstance(structured, dict):
                return structured

        content = getattr(
            result,
            "content",
            [],
        )

        if len(content) == 1:
            item = content[0]

            text = getattr(
                item,
                "text",
                None,
            )

            if text:
                return {
                    "status": "success",
                    "result": text,
                }

        return {
            "status": "success",
            "result": str(result),
        }
