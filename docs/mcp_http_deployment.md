# MCP HTTP Server Deployment Guide

This guide explains how to deploy the MCP server over HTTP using SSE (Server-Sent Events), enabling remote access from Claude Desktop and other MCP clients.

## Table of Contents

- [Overview](#overview)
- [Local Testing](#local-testing)
- [EC2 Deployment](#ec2-deployment)
- [Claude Desktop Configuration](#claude-desktop-configuration)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

---

## Overview

The MCP HTTP server exposes your call grading tools over HTTP, allowing:
- **Remote access** from any machine
- **Claude Desktop integration** without SSH
- **Multiple concurrent clients**
- **Standard HTTP/HTTPS** (firewall-friendly)

### Architecture

```
┌──────────────────┐         HTTP/SSE          ┌─────────────────┐
│                  │◄──────────────────────────►│                 │
│  Claude Desktop  │   GET /sse (responses)     │  MCP HTTP       │
│  (Your Mac)      │   POST /messages (requests)│  Server (EC2)   │
│                  │                             │  Port 8000      │
└──────────────────┘                             └─────────────────┘
```

### Ports

| Service | Port | Purpose |
|---------|------|---------|
| Streamlit Web UI | 8501 | Browser access |
| MCP HTTP Server | 8000 | Claude Desktop / MCP clients |

---

## Local Testing

Before deploying to EC2, test locally:

### 1. Start the HTTP Server

```bash
cd /Users/Nima/Documents/IK/call-center
source .venv/bin/activate
python3 mcp_http_server.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     SSE endpoint: http://0.0.0.0:8000/sse
```

### 2. Test with curl

In another terminal:

```bash
# Test SSE endpoint (should keep connection open)
curl -N http://localhost:8000/sse

# In another terminal, send a test message
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

### 3. Configure Claude Desktop for Local Testing

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "call-center-grading": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

Restart Claude Desktop and test!

---

## EC2 Deployment

### Option 1: Docker Compose (Recommended)

This runs both Streamlit and MCP HTTP server together.

#### 1. Update Security Group

Add inbound rule for port 8000:
- **Type**: Custom TCP
- **Port**: 8000
- **Source**: 0.0.0.0/0 (or your IP for security)

#### 2. Deploy with Docker Compose

```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@YOUR_EC2_IP

# Navigate to project
cd call-center

# Pull latest changes
git pull origin main

# Start both services
docker-compose -f docker-compose.http.yml up -d

# Check logs
docker-compose -f docker-compose.http.yml logs -f
```

#### 3. Verify Services

```bash
# Check Streamlit (web UI)
curl http://localhost:8501

# Check MCP HTTP server
curl http://localhost:8000/sse
```

#### 4. Test from Outside

From your local machine:

```bash
# Test SSE endpoint
curl -N http://YOUR_EC2_IP:8000/sse
```

---

### Option 2: Single Container with Supervisor

If you prefer running both in one container:

Create `supervisord.conf`:

```ini
[supervisord]
nodaemon=true

[program:streamlit]
command=streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:mcp-http]
command=python3 mcp_http_server.py
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
```

Update Dockerfile:

```dockerfile
# Install supervisor
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose both ports
EXPOSE 8501 8000

# Run supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

---

## Claude Desktop Configuration

### Remote Connection (EC2)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "call-center-grading": {
      "url": "http://YOUR_EC2_PUBLIC_IP:8000/sse"
    }
  }
}
```

**Important:** Replace `YOUR_EC2_PUBLIC_IP` with your actual EC2 public IP address.

### Using HTTPS (Production)

For production, use HTTPS:

```json
{
  "mcpServers": {
    "call-center-grading": {
      "url": "https://your-domain.com/sse"
    }
  }
}
```

Set up HTTPS with:
- Nginx reverse proxy with Let's Encrypt SSL
- AWS Application Load Balancer with ACM certificate
- Cloudflare proxy

---

## Security Considerations

### 1. Restrict Access by IP

Update EC2 security group to only allow your IP:

```
Port 8000 → Source: YOUR_IP/32
```

### 2. Add Authentication

Add API key authentication to the HTTP server:

```python
# In mcp_http_server.py
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware

# Add authentication check
async def handle_sse(request):
    api_key = request.headers.get("X-API-Key")
    if api_key != os.getenv("MCP_API_KEY"):
        return Response("Unauthorized", status_code=401)
    # ... rest of code
```

Then in Claude Desktop config:

```json
{
  "mcpServers": {
    "call-center-grading": {
      "url": "http://YOUR_EC2_IP:8000/sse",
      "headers": {
        "X-API-Key": "your-secret-key"
      }
    }
  }
}
```

### 3. Use HTTPS

Always use HTTPS in production to encrypt traffic.

### 4. Rate Limiting

Add rate limiting to prevent abuse:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("10/minute")
async def handle_messages(request):
    # ... existing code
```

---

## Troubleshooting

### "Connection refused" from Claude Desktop

**Cause:** EC2 security group doesn't allow port 8000

**Solution:**
```bash
# Check if port is open
curl http://YOUR_EC2_IP:8000/sse

# If not, update security group in AWS Console
```

### "SSE connection keeps dropping"

**Cause:** Firewall or proxy timeout

**Solution:** Add keepalive pings:

```python
# In mcp_http_server.py
# SSE sends periodic keepalive to prevent timeout
sse_transport = SseServerTransport("/messages", keepalive_interval=30)
```

### "Tools not appearing in Claude Desktop"

**Cause:** MCP server not properly initialized

**Solution:**
1. Check server logs: `docker logs mcp-server`
2. Verify environment variables are set
3. Test tools endpoint: `curl http://YOUR_EC2_IP:8000/messages`
4. Restart Claude Desktop completely

### "High latency / slow responses"

**Cause:** Network latency to EC2

**Solution:**
- Use EC2 region closer to you
- Consider local MCP server for development
- Use remote for team access only

---

## Management Commands

### View Logs

```bash
# Docker Compose
docker-compose -f docker-compose.http.yml logs -f mcp-server

# Single container
docker logs -f call-center-app
```

### Restart MCP Server

```bash
# Docker Compose
docker-compose -f docker-compose.http.yml restart mcp-server

# Single container
docker restart call-center-app
```

### Update After Code Changes

```bash
cd call-center
git pull origin main
docker-compose -f docker-compose.http.yml down
docker-compose -f docker-compose.http.yml up -d --build
```

---

## Testing the Deployment

### 1. Test HTTP Endpoints

```bash
# Test SSE (should hang waiting for events)
curl -N http://YOUR_EC2_IP:8000/sse

# Test message endpoint (should return quickly)
curl -X POST http://YOUR_EC2_IP:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### 2. Test from Claude Desktop

After configuring Claude Desktop:

1. Completely quit and restart Claude Desktop
2. Start a new conversation
3. Ask: "What MCP tools do you have access to?"
4. You should see the 4 call grading tools
5. Test grading: "Please grade this call: [paste transcript]"

### 3. Monitor Performance

```bash
# Watch resource usage
docker stats

# Monitor requests
docker logs -f mcp-server | grep "Tool called"
```

---

## Cost Estimate

Running both services on EC2:

| Resource | Cost |
|----------|------|
| t3.medium EC2 (2 vCPU, 4GB RAM) | ~$30/month |
| 20 GB EBS storage | ~$2/month |
| Data transfer (minimal) | ~$1/month |
| **Total** | **~$33/month** |

Plus API costs:
- OpenAI GPT-4o: ~$0.10 per call graded
- Deepgram (if using audio): ~$0.10 per 10 min audio

---

## Next Steps

- [Add HTTPS with Nginx](nginx-setup.md)
- [Set up monitoring](monitoring.md)
- [Configure rate limiting](rate-limiting.md)

For questions, see [MCP Server Guide](mcp_server.md)
