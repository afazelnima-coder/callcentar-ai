#!/usr/bin/env python3
"""
MCP Server over HTTP using SSE (Server-Sent Events) transport.

This wraps the MCP server to be accessible over HTTP, allowing remote
connections from Claude Desktop and other MCP clients.

Usage:
    python3 mcp_http_server.py

The server will run on http://0.0.0.0:8000
Claude Desktop can connect to http://YOUR_IP:8000/sse
"""

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response

from mcp.server.sse import SseServerTransport
from mcp_server import mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_http_server")


@asynccontextmanager
async def lifespan(app: Starlette):
    """Lifespan context manager for the application."""
    logger.info("Starting MCP HTTP Server with SSE transport")
    logger.info("Server will be available at http://0.0.0.0:8000")
    logger.info("SSE endpoint: http://0.0.0.0:8000/sse")
    yield
    logger.info("Shutting down MCP HTTP Server")


# Create SSE transport
# The SSE transport handles the bidirectional communication:
# - Client → Server: HTTP POST to /messages
# - Server → Client: SSE stream from /sse
sse_transport = SseServerTransport("/messages")


async def handle_sse(request):
    """
    Handle SSE connection endpoint.

    This keeps the connection open and streams server messages to the client.
    Claude Desktop connects to this endpoint to receive responses.
    """
    async with sse_transport.connect_sse(
        request.scope,
        request.receive,
        request._send
    ) as streams:
        await mcp.run(
            streams[0],
            streams[1],
            mcp.create_initialization_options()
        )
    return Response()


async def handle_messages(request):
    """
    Handle client messages endpoint.

    This receives POST requests from the client with MCP protocol messages.
    The response is sent back via the SSE stream, not in the HTTP response.
    """
    await sse_transport.handle_post_message(request.scope, request.receive, request._send)
    return Response()


# Create Starlette application
app = Starlette(
    debug=False,
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ],
    lifespan=lifespan,
)


def main():
    """Run the HTTP server."""
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
