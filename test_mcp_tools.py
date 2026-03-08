#!/usr/bin/env python3
"""
Simple interactive test script for MCP HTTP server.
Just run this script and it will show you the available tools.
"""

import asyncio
import json
import httpx
from urllib.parse import parse_qs, urlparse


async def get_tools():
    """Connect to MCP server and get the list of tools."""
    base_url = "http://localhost:8000"

    print("Connecting to MCP server at", base_url)
    print("=" * 80)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Connect to SSE
        async with client.stream("GET", f"{base_url}/sse") as response:
            session_id = None

            # Get session ID
            async for line in response.aiter_lines():
                if line.startswith("data:") and "/messages?session_id=" in line:
                    data_str = line[5:].strip()
                    parsed = urlparse(data_str)
                    query_params = parse_qs(parsed.query)
                    session_id = query_params["session_id"][0]
                    print(f"✓ Connected with session: {session_id}\n")

                    # Initialize MCP session
                    print("Initializing MCP session...")
                    init_msg = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "test", "version": "1.0"}
                        }
                    }

                    await client.post(
                        f"{base_url}/messages?session_id={session_id}",
                        json=init_msg,
                        headers={"Content-Type": "application/json"}
                    )

                elif session_id and line.startswith("data:"):
                    data_str = line[5:].strip()
                    if not data_str:
                        continue

                    try:
                        data = json.loads(data_str)

                        # Got init response, now request tools
                        if data.get("id") == 1 and "result" in data:
                            print("✓ Initialized successfully\n")
                            print("Requesting tools list...")

                            tools_msg = {
                                "jsonrpc": "2.0",
                                "id": 2,
                                "method": "tools/list",
                                "params": {}
                            }

                            await client.post(
                                f"{base_url}/messages?session_id={session_id}",
                                json=tools_msg,
                                headers={"Content-Type": "application/json"}
                            )

                        # Got tools response
                        elif data.get("id") == 2 and "result" in data:
                            print("=" * 80)
                            print("AVAILABLE TOOLS")
                            print("=" * 80)

                            tools = data["result"]["tools"]
                            for i, tool in enumerate(tools, 1):
                                print(f"\n{i}. {tool['name']}")
                                print(f"   Description: {tool['description']}")

                                # Show required parameters
                                schema = tool.get("inputSchema", {})
                                required = schema.get("required", [])
                                if required:
                                    print(f"   Required params: {', '.join(required)}")
                                else:
                                    print(f"   Required params: none")

                            print("\n" + "=" * 80)
                            print(f"Total: {len(tools)} tools available")
                            print("=" * 80)
                            return

                    except json.JSONDecodeError:
                        pass


async def main():
    try:
        await get_tools()
    except httpx.ConnectError:
        print("\n❌ ERROR: Could not connect to MCP server")
        print("\nMake sure the server is running:")
        print("  python3 mcp_http_server.py\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())
