#!/usr/bin/env python3
"""
MCP Server over HTTP using SSE (Server-Sent Events) transport.

This wraps the MCP server to be accessible over HTTP, allowing remote
connections from Claude Desktop and other MCP clients.

Usage:
    python3 mcp_http_server.py

The server will run on http://0.0.0.0:8000
Claude Desktop can connect to http://YOUR_EC2_IP:8000/sse
"""

import logging

import uvicorn
from mcp.server.sse import SseServerTransport

from mcp_server import mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_http_server")


def main():
    """Run the HTTP server."""
    logger.info("Starting MCP HTTP Server with SSE transport")
    logger.info("Server will be available at http://0.0.0.0:8000")
    logger.info("SSE endpoint: http://0.0.0.0:8000/sse")
    logger.info("Messages endpoint: http://0.0.0.0:8000/messages")

    # Create SSE transport
    # The endpoint parameter is where client sends POST messages
    sse = SseServerTransport("/messages")

    # Create ASGI application from the transport
    # This handles both SSE (GET /sse) and messages (POST /messages)
    async def app(scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]

            if path == "/sse" and scope["method"] == "GET":
                # Handle SSE connection
                async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                    await mcp.run(
                        read_stream,
                        write_stream,
                        mcp.create_initialization_options()
                    )
            elif path == "/messages" and scope["method"] == "POST":
                # Handle client messages
                await sse.handle_post_message(scope, receive, send)
            else:
                # 404 for other paths
                await send({
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [(b"content-type", b"text/plain")],
                })
                await send({
                    "type": "http.response.body",
                    "body": b"Not Found",
                })

    # Run on all interfaces (0.0.0.0) so it's accessible from outside
    # Port 8000 is the default MCP HTTP port
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
