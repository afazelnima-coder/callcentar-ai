# MCP Server Documentation

This document explains how to use the Call Center Quality Grading System as an MCP (Model Context Protocol) server, allowing Claude Desktop and other MCP clients to use your grading tools.

## What is MCP?

The Model Context Protocol (MCP) is an open protocol that standardizes how AI applications connect to external data sources and tools. By running this application as an MCP server, you can:

- Grade call transcripts directly from Claude Desktop
- Analyze audio files through AI chat interfaces
- Get quality scoring rubrics on demand
- Use the grading system as a tool in other AI workflows

## Available Tools

The MCP server exposes 4 tools:

### 1. `grade_call_transcript`

Grade a call from a text transcript with full quality analysis.

**Input:**
- `transcript` (required): The call transcript text
- `call_metadata` (optional): Metadata like customer_id, agent_id, call_date

**Returns:**
- Full quality scores (19 criteria across 5 categories)
- Overall grade (A-F)
- Strengths and areas for improvement
- Compliance flags
- Recommendations

**Example:**
```json
{
  "transcript": "Agent: Thank you for calling Tech Support, my name is Sarah. How can I help you today?\nCustomer: Hi, my internet has been down for 3 hours..."
}
```

### 2. `grade_call_audio`

Grade a call from an audio file (automatically transcribes first).

**Input:**
- `audio_file_path` (required): Absolute path to audio file
- `call_metadata` (optional): Call metadata

**Supported formats:** WAV, MP3, M4A, FLAC, OGG

**Returns:** Same as `grade_call_transcript` plus the generated transcript

**Example:**
```json
{
  "audio_file_path": "/Users/jane/calls/call_001.wav",
  "call_metadata": {
    "customer_id": "CUST-12345",
    "agent_id": "AGT-789"
  }
}
```

### 3. `analyze_call_summary`

Get a quick call summary without full quality scoring (faster).

**Input:**
- `transcript` (required): The call transcript text

**Returns:**
- Brief summary (2-3 sentences)
- Customer issue and resolution
- Customer sentiment (positive/neutral/negative)
- Call category (support, complaint, inquiry, etc.)
- Key topics discussed
- Action items

**Example:**
```json
{
  "transcript": "Agent: Tech support, this is Mike...\n..."
}
```

### 4. `get_scoring_rubric`

Get the detailed quality scoring rubric and criteria.

**Input:** None required

**Returns:** Complete rubric with all 19 evaluation criteria, scoring scale, and grading thresholds

---

## Setup for Claude Desktop

### 1. Install Dependencies

Make sure you have all dependencies installed:

```bash
# Navigate to project directory
cd /Users/Nima/Documents/IK/call-center

# Install dependencies (including MCP)
pip install -r requirements.txt

# Or with uv
uv pip install -r requirements.txt
```

### 2. Configure Claude Desktop

Edit your Claude Desktop config file to add the MCP server:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "call-center-grading": {
      "command": "python3",
      "args": [
        "/Users/Nima/Documents/IK/call-center/mcp_server.py"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-your-openai-api-key",
        "DEEPGRAM_API_KEY": "your-deepgram-api-key",
        "OPENAI_MODEL": "gpt-4o"
      }
    }
  }
}
```

**Important:** Replace `/Users/Nima/Documents/IK/call-center/` with your actual project path, and add your real API keys.

### 3. Restart Claude Desktop

Completely quit and restart Claude Desktop for the configuration to take effect.

### 4. Verify Connection

In Claude Desktop, you should now see the call center grading tools available. You can verify by asking:

> "What MCP tools do you have access to?"

Claude should list the 4 call center grading tools.

---

## Usage Examples in Claude Desktop

### Example 1: Grade a Transcript

In Claude Desktop, you can now say:

> "Please grade this call transcript:
>
> Agent: Good morning, thank you for calling ABC Company. This is Jennifer speaking. How may I assist you today?
>
> Customer: Hi Jennifer, I'm having trouble with my recent order. It hasn't arrived yet and it's been two weeks.
>
> Agent: I'm sorry to hear you're experiencing a delay with your order. I'd be happy to look into that for you right away. May I please have your order number?
>
> [continues...]"

Claude will use the `grade_call_transcript` tool and provide you with:
- Full quality scores
- Overall grade
- Specific strengths and areas for improvement

### Example 2: Analyze an Audio File

> "Can you grade this call recording at /Users/jane/Desktop/call_recording.wav?"

Claude will use the `grade_call_audio` tool to transcribe and grade the audio file.

### Example 3: Get Just a Summary

> "I don't need full scoring, just summarize what happened in this call: [paste transcript]"

Claude will use `analyze_call_summary` for faster results.

### Example 4: Learn About the Rubric

> "What criteria do you use to grade calls?"

Claude will use `get_scoring_rubric` to show you the complete evaluation framework.

---

## Running the MCP Server Standalone

You can also run the MCP server directly (useful for testing):

```bash
cd /Users/Nima/Documents/IK/call-center

# Set environment variables
export OPENAI_API_KEY="sk-your-key"
export DEEPGRAM_API_KEY="your-key"

# Run the server
python3 mcp_server.py
```

The server will start and listen for MCP protocol messages on stdin/stdout.

---

## Environment Variables

The MCP server requires these environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for GPT models |
| `DEEPGRAM_API_KEY` | Yes* | - | Deepgram API key for audio transcription |
| `OPENAI_MODEL` | No | `gpt-4o` | OpenAI model to use |
| `MAX_FILE_SIZE_MB` | No | `100` | Max audio file size |

\* Only required if you plan to use `grade_call_audio` tool

---

## Architecture

```
┌─────────────────┐
│ Claude Desktop  │
│  (MCP Client)   │
└────────┬────────┘
         │ MCP Protocol (stdio)
         │
┌────────▼────────┐
│  mcp_server.py  │  ← Exposes 4 tools
│  (MCP Server)   │
└────────┬────────┘
         │
         │ Invokes workflow
         │
┌────────▼────────────────────────────┐
│     LangGraph Workflow              │
│                                     │
│  ┌──────────────────────────┐      │
│  │ Intake → Transcription   │      │
│  │    ↓                      │      │
│  │ Summarization → Scoring  │      │
│  │    ↓                      │      │
│  │ Routing → Results        │      │
│  └──────────────────────────┘      │
└─────────────────────────────────────┘
```

The MCP server is a lightweight wrapper around your existing workflow. It:
1. Receives tool calls via MCP protocol
2. Converts them to workflow state
3. Runs the LangGraph workflow
4. Returns results in MCP format

---

## Troubleshooting

### "MCP server not found" in Claude Desktop

**Solution:** Check that:
1. The path in `claude_desktop_config.json` is correct and absolute
2. `mcp_server.py` is executable: `chmod +x mcp_server.py`
3. You've completely restarted Claude Desktop

### "API key not found" errors

**Solution:** Make sure you set the `env` section in `claude_desktop_config.json` with your actual API keys.

### Tools not appearing in Claude Desktop

**Solution:**
1. Open Claude Desktop DevTools: View → Developer → Developer Tools
2. Check Console for any MCP errors
3. Verify the config file is valid JSON (use https://jsonlint.com)

### "Permission denied" when running audio grading

**Solution:** The MCP server runs with your user permissions. Make sure:
1. Audio files are readable by your user
2. You provide absolute paths, not relative paths

### Slow performance

**Solution:**
- Use `analyze_call_summary` instead of `grade_call_transcript` when you only need summaries
- Audio transcription can take 10-30 seconds depending on file length
- Consider using a faster OpenAI model like `gpt-4o-mini` for development

---

## Testing

Test the MCP server manually:

```bash
# Create a test transcript file
cat > test_transcript.txt << 'EOF'
Agent: Thank you for calling. My name is Sarah. How can I help you?
Customer: Hi, my order hasn't arrived yet.
Agent: I apologize for the inconvenience. Let me check that for you right away. May I have your order number?
EOF

# Test the server with a simple Python script
python3 << 'EOF'
import asyncio
from mcp_server import grade_call_transcript

async def test():
    with open("test_transcript.txt") as f:
        transcript = f.read()

    result = await grade_call_transcript(transcript)
    print(result)

asyncio.run(test())
EOF
```

---

## Security Considerations

1. **API Keys**: Never commit API keys to version control. Always use environment variables.

2. **File Access**: The MCP server runs with your user permissions. Be cautious about which files you grant it access to.

3. **Rate Limiting**: The server doesn't implement rate limiting. Monitor your OpenAI and Deepgram usage to avoid unexpected costs.

4. **Data Privacy**: Call transcripts are sent to OpenAI for analysis. Ensure compliance with your privacy policies.

---

## Advanced Usage

### Using with Other MCP Clients

Any MCP-compatible client can use this server. The protocol is standardized, so you can integrate it with:

- Custom Python applications (using `mcp` SDK)
- Other AI assistants that support MCP
- Workflow automation tools

### Extending the Server

To add more tools, edit `mcp_server.py`:

1. Add a new tool definition in `list_tools()`
2. Add the handler in `call_tool()`
3. Implement the tool function

Example - add a "batch grading" tool that processes multiple calls at once.

---

## Cost Estimates

Per call grading (approximate):

| Service | Usage | Cost |
|---------|-------|------|
| OpenAI (transcript input) | ~2,000 tokens | $0.01-0.02 |
| OpenAI (output) | ~3,000 tokens | $0.06-0.12 |
| Deepgram (audio transcription) | 10 min audio | $0.08-0.12 |

**Total per call:**
- Text transcript: ~$0.07-0.14
- Audio file: ~$0.15-0.26

Using `gpt-4o-mini` instead of `gpt-4o` can reduce costs by ~90%.

---

## Next Steps

- [Deployment Guide](deployment.md) - Deploy the MCP server to a remote machine
- [API Documentation](../README.md) - Learn about the underlying workflow
- [Rubric Customization](customization.md) - Customize the scoring criteria (TODO)

---

For questions or issues, please create an issue on the GitHub repository.
