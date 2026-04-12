import asyncio
import json
from typing import List, Dict, Any

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions

from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

from shared.context_tools import get_product_details, get_brand_guidelines


def create_mcp_server() -> Server:
    server = Server("moniepoint-product-brand-mcp")

    product_tool = FunctionTool(get_product_details)
    brand_tool = FunctionTool(get_brand_guidelines)

    @server.list_tools()
    async def list_tools() -> List[types.Tool]:
        return [
            adk_to_mcp_tool_type(product_tool),
            adk_to_mcp_tool_type(brand_tool),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        tools = {
            product_tool.name: product_tool,
            brand_tool.name: brand_tool,
        }

        if name not in tools:
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool '{name}'"}),
                )
            ]

        try:
            result = await tools[name].run_async(
                args=arguments,
                tool_context=None,
            )
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result),
                )
            ]
        except Exception as exc:
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({"error": str(exc)}),
                )
            ]

    return server


async def run_mcp_server() -> None:
    server = create_mcp_server()

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="moniepoint-product-brand-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run_mcp_server())
