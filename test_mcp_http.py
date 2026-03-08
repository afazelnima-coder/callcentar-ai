#!/usr/bin/env python3
"""
Test script for MCP HTTP server.

This demonstrates the proper way to interact with the MCP HTTP/SSE server,
including handling session IDs.
"""

import asyncio
import json
import httpx
from urllib.parse import parse_qs, urlparse


async def test_mcp_http_server():
    """Test the MCP HTTP server with proper session handling."""
    base_url = "http://localhost:8000"

    print("=" * 80)
    print("Testing MCP HTTP Server")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        print("\n1. Connecting to SSE endpoint...")

        # Start SSE connection
        async with client.stream("GET", f"{base_url}/sse") as response:
            print(f"   Status: {response.status_code}")

            # Read the first SSE event which contains the endpoint info
            session_id = None
            message_endpoint = None
            response_count = 0

            async for line in response.aiter_lines():
                print(f"   Received: {line}")

                if line.startswith("data:"):
                    data_str = line[5:].strip()

                    # Check if this is the endpoint URL (plain text, not JSON)
                    if data_str.startswith("/messages?session_id="):
                        # Extract session_id directly from the URL
                        parsed = urlparse(data_str)
                        query_params = parse_qs(parsed.query)

                        if "session_id" in query_params:
                            session_id = query_params["session_id"][0]
                            message_endpoint = data_str
                            print(f"\n   ✓ Got session ID: {session_id}")
                            print(f"   ✓ Message endpoint: {message_endpoint}")

                            # First, initialize the MCP session
                            print(f"\n2. Initializing MCP session...")

                            init_message = {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "initialize",
                                "params": {
                                    "protocolVersion": "2024-11-05",
                                    "capabilities": {},
                                    "clientInfo": {
                                        "name": "test-client",
                                        "version": "1.0.0"
                                    }
                                }
                            }

                            # POST initialization
                            post_url = f"{base_url}/messages?session_id={session_id}"
                            print(f"   POST URL: {post_url}")

                            init_response = await client.post(
                                post_url,
                                json=init_message,
                                headers={"Content-Type": "application/json"}
                            )
                            print(f"   Init POST Status: {init_response.status_code}")

                    elif data_str and session_id:
                        # We have a session and this might be a response
                        try:
                            data = json.loads(data_str)

                            # Check if this is the initialize response
                            if data.get("id") == 1 and "result" in data:
                                print(f"\n   ✓ Initialization successful!")
                                print(json.dumps(data, indent=2))

                                # Now send tools/list request
                                print(f"\n3. Sending 'tools/list' request...")

                                tools_message = {
                                    "jsonrpc": "2.0",
                                    "id": 2,
                                    "method": "tools/list",
                                    "params": {}
                                }

                                post_url = f"{base_url}/messages?session_id={session_id}"
                                tools_response = await client.post(
                                    post_url,
                                    json=tools_message,
                                    headers={"Content-Type": "application/json"}
                                )
                                print(f"   Tools POST Status: {tools_response.status_code}")
                                print(f"\n4. Waiting for tools/list response...")

                            elif data.get("id") == 2:
                                # This is the tools/list response
                                print(f"\n   ✓ Tools list received:")
                                print(json.dumps(data, indent=2))
                                response_count += 1

                                # Stop after getting the tools response
                                if response_count >= 1:
                                    break
                            else:
                                print(f"\n   Response:")
                                print(json.dumps(data, indent=2))
                        except json.JSONDecodeError:
                            print(f"   Non-JSON data: {data_str}")

                            # POST to the message endpoint with session_id
                            post_url = f"{base_url}/messages?session_id={session_id}"
                            print(f"   POST URL: {post_url}")

                            post_response = await client.post(
                                post_url,
                                json=message,
                                headers={"Content-Type": "application/json"}
                            )

                            print(f"   POST Status: {post_response.status_code}")
                            print(f"\n3. Waiting for response via SSE stream...")

                    elif data_str and session_id:
                        # We have a session and this might be a response
                        try:
                            data = json.loads(data_str)
                            print(f"\n   Response {response_count + 1}:")
                            print(json.dumps(data, indent=2))
                            response_count += 1

                            # Stop after getting the response
                            if response_count >= 1:
                                break
                        except json.JSONDecodeError:
                            print(f"   Non-JSON data: {data_str}")

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    print("\nMake sure the MCP HTTP server is running:")
    print("  python3 mcp_http_server.py\n")

    asyncio.run(test_mcp_http_server())
