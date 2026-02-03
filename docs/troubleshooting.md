# Troubleshooting Guide

This guide covers common issues, their causes, and solutions when using the Call Center Quality Grading System.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [File Processing Issues](#file-processing-issues)
- [API Errors](#api-errors)
- [Performance Issues](#performance-issues)
- [UI Issues](#ui-issues)
- [Testing Issues](#testing-issues)
- [Debugging Tips](#debugging-tips)
- [Getting Help](#getting-help)

---

## Installation Issues

### Python Version Mismatch

**Error**: `Python 3.13 is required`

**Cause**: The system requires Python 3.13 or higher.

**Solution**:
```bash
# Check your Python version
python --version

# Install Python 3.13+ using pyenv
pyenv install 3.13.0
pyenv local 3.13.0

# Or use uv to manage Python
uv python install 3.13
```

### Dependency Installation Fails

**Error**: `Failed to build package X`

**Cause**: Missing system dependencies or incompatible package versions.

**Solutions**:

1. **Update pip/uv**:
   ```bash
   uv pip install --upgrade pip
   ```

2. **Install system dependencies** (macOS):
   ```bash
   brew install portaudio  # For audio processing
   ```

3. **Install system dependencies** (Ubuntu):
   ```bash
   sudo apt-get install python3-dev portaudio19-dev
   ```

4. **Clear cache and retry**:
   ```bash
   uv cache clean
   uv pip install -e .
   ```

### Virtual Environment Issues

**Error**: `ModuleNotFoundError` after installation

**Cause**: Not using the correct virtual environment.

**Solution**:
```bash
# Ensure you're in the project directory
cd call-center

# Activate the virtual environment
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate  # Windows

# Verify installation
uv pip list | grep langgraph
```

---

## Configuration Issues

### Missing API Key

**Error**: `ValidationError: OPENAI_API_KEY field required`

**Cause**: Environment variables not configured.

**Solution**:

1. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

2. Add your API keys:
   ```env
   OPENAI_API_KEY=sk-your-key-here
   DEEPGRAM_API_KEY=your-deepgram-key
   ```

3. Verify the file is loaded:
   ```python
   from app.config import settings
   print(settings.openai_api_key[:10])  # Should show first 10 chars
   ```

### Invalid API Key

**Error**: `AuthenticationError: Incorrect API key provided`

**Cause**: API key is malformed or expired.

**Solutions**:

1. **Verify key format**:
   - OpenAI keys start with `sk-`
   - No extra spaces or quotes

2. **Test the key**:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. **Generate new key** if expired:
   - OpenAI: https://platform.openai.com/api-keys
   - Deepgram: https://console.deepgram.com/

### Environment File Not Loading

**Error**: Settings show default values instead of `.env` values

**Cause**: `.env` file not in correct location or not readable.

**Solutions**:

1. **Check file location**:
   ```bash
   ls -la .env  # Should show the file
   ```

2. **Check file permissions**:
   ```bash
   chmod 644 .env
   ```

3. **Verify file encoding** (should be UTF-8):
   ```bash
   file .env  # Should show "ASCII text" or "UTF-8"
   ```

4. **Force reload**:
   ```python
   from dotenv import load_dotenv
   load_dotenv(override=True)
   ```

---

## File Processing Issues

### File Not Found

**Error**: `FileNotFoundError: File not found: /path/to/file`

**Cause**: File path is incorrect or file doesn't exist.

**Solutions**:

1. **Use absolute paths**:
   ```python
   import os
   file_path = os.path.abspath("call.wav")
   ```

2. **Check file exists**:
   ```python
   import os
   if not os.path.exists(file_path):
       print(f"File not found: {file_path}")
   ```

### File Too Large

**Error**: `FileTooLargeError: File too large: 150.5MB (max 100MB)`

**Cause**: File exceeds the configured maximum size.

**Solutions**:

1. **Compress the audio file**:
   ```bash
   ffmpeg -i large_file.wav -b:a 128k compressed.mp3
   ```

2. **Increase the limit** (in `.env`):
   ```env
   MAX_FILE_SIZE_MB=200
   ```

3. **Split long recordings**:
   ```bash
   ffmpeg -i long_call.wav -f segment -segment_time 1800 -c copy call_%03d.wav
   ```

### Unsupported Format

**Error**: `UnsupportedFormatError: This file format is not supported`

**Cause**: File extension not in supported list.

**Supported formats**:
- Audio: `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.webm`
- Text: `.txt`, `.json`

**Solutions**:

1. **Convert audio format**:
   ```bash
   ffmpeg -i input.aac -acodec pcm_s16le output.wav
   ```

2. **Rename if extension is wrong**:
   ```bash
   mv transcript transcript.txt
   ```

### Content Validation Failed

**Error**: `ContentValidationError: This does not appear to be a call center conversation`

**Cause**: The system determined the content is not a valid call center transcript.

**Solutions**:

1. **Check transcript format** - ensure it has dialogue:
   ```text
   Agent: Hello, thank you for calling...
   Customer: Hi, I need help with...
   ```

2. **Add speaker labels** if missing:
   ```text
   Agent: [First speaker's text]
   Customer: [Second speaker's text]
   ```

3. **Check for minimum length** - transcripts need at least 100 characters

4. **Review content type**:
   - Must be customer service dialogue
   - Not acceptable: podcasts, interviews, articles, monologues

---

## API Errors

### OpenAI Rate Limit

**Error**: `RateLimitError: Rate limit reached for requests`

**Cause**: Too many API requests in a short time.

**Solutions**:

1. **Wait and retry** - the system automatically retries with exponential backoff

2. **Reduce concurrent requests**:
   ```python
   # Process files sequentially instead of parallel
   for file in files:
       result = analyze_call(file)
       time.sleep(1)  # Add delay between calls
   ```

3. **Upgrade API tier** on OpenAI platform for higher limits

### OpenAI Timeout

**Error**: `APITimeoutError: Request timed out`

**Cause**: API request took too long to complete.

**Solutions**:

1. **Retry** - the system automatically retries

2. **Check OpenAI status**: https://status.openai.com/

3. **Use shorter transcripts** - very long texts may timeout

### Deepgram Error

**Error**: `TranscriptionError: Could not transcribe the audio`

**Cause**: Deepgram API failure or audio quality issues.

**Solutions**:

1. **Check audio quality**:
   - Ensure audio is audible
   - Check for corruption
   - Verify format is correct

2. **Test with simpler file**:
   ```bash
   # Create a test audio file
   ffmpeg -f lavfi -i "sine=frequency=1000:duration=5" test.wav
   ```

3. **Check Deepgram status**: https://status.deepgram.com/

4. **Verify API key** has transcription permissions

---

## Performance Issues

### Slow Transcription

**Symptoms**: Transcription takes several minutes

**Causes and Solutions**:

1. **Long audio files** - Deepgram processes in real-time ratio
   - 10-minute audio ≈ 1-2 minutes processing
   - Consider splitting very long files

2. **Network latency** - slow internet connection
   - Check connection speed
   - Use wired connection if possible

3. **API load** - high traffic on Deepgram
   - Try during off-peak hours
   - Check status page

### Slow Scoring

**Symptoms**: Scoring step takes a long time

**Causes and Solutions**:

1. **Very long transcripts**
   - GPT-4o processes entire transcript
   - Consider summarizing first

2. **Model selection** - GPT-4o is thorough but slower
   - For faster results (less detailed), use gpt-4o-mini in `.env`:
     ```env
     OPENAI_MODEL=gpt-4o-mini
     ```

### High Memory Usage

**Symptoms**: Application uses excessive RAM

**Solutions**:

1. **Process files sequentially** instead of loading all at once

2. **Clear Streamlit cache**:
   ```python
   st.cache_data.clear()
   ```

3. **Restart the application** periodically for batch processing

---

## UI Issues

### Streamlit Won't Start

**Error**: `streamlit: command not found`

**Solution**:
```bash
# Use uv run to ensure correct environment
uv run streamlit run app/main.py
```

### Page Not Loading

**Symptoms**: Browser shows blank page or connection refused

**Solutions**:

1. **Check if Streamlit is running**:
   ```bash
   # Look for Streamlit process
   ps aux | grep streamlit
   ```

2. **Try different port**:
   ```bash
   uv run streamlit run app/main.py --server.port 8502
   ```

3. **Check firewall** - ensure port 8501 is open

4. **Clear browser cache** - try incognito mode

### Results Not Displaying

**Symptoms**: Analysis completes but no results shown

**Solutions**:

1. **Check for errors** in terminal output

2. **Verify session state**:
   ```python
   # Add to main.py for debugging
   st.write(st.session_state)
   ```

3. **Clear session state**:
   - Click "Analyze Call" again
   - Or refresh the page

### Emojis Not Rendering

**Symptoms**: Emoji characters show as text codes

**Solution**: The system uses Unicode emojis. If they don't render:

1. **Update browser** to latest version
2. **Check font support** - use a font with emoji support
3. **Use a modern terminal** if running headless

---

## Testing Issues

### Tests Not Discovering

**Error**: `no tests ran`

**Solution**:
```bash
# Ensure pytest configuration is correct
uv run pytest --collect-only

# Check test file naming (should be test_*.py)
ls tests/test_*/test_*.py
```

### Import Errors in Tests

**Error**: `ModuleNotFoundError: No module named 'agents'`

**Solution**:
```bash
# Install package in editable mode
uv pip install -e .

# Run tests with correct path
uv run pytest tests/
```

### Mock Not Working

**Error**: Tests calling real APIs instead of mocks

**Solution**:
```python
# Ensure mock path matches import path
@patch("agents.scoring_agent.OpenAIService")  # Correct
@patch("services.openai_service.OpenAIService")  # Wrong location
```

### Fixture Not Found

**Error**: `fixture 'sample_quality_scores' not found`

**Solution**:
```bash
# Ensure conftest.py is in tests/ directory
ls tests/conftest.py

# Check fixture is defined correctly
grep -n "sample_quality_scores" tests/conftest.py
```

---

## Debugging Tips

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific modules
logging.getLogger("agents").setLevel(logging.DEBUG)
```

### Inspect Workflow State

```python
from graph.workflow import workflow

# Use stream to see each step
for event in workflow.stream(initial_state):
    for node, state in event.items():
        print(f"\n=== {node} ===")
        print(f"Error: {state.get('error')}")
        print(f"Status: {state.get('workflow_status')}")
```

### Test Individual Components

```python
# Test OpenAI connection
from services.openai_service import OpenAIService
service = OpenAIService()
response = service.generate("Say hello")
print(response)

# Test Deepgram connection
from services.deepgram_service import DeepgramService
service = DeepgramService()
# Test with a small audio file
```

### Check API Responses

```python
# Add to openai_service.py temporarily
def generate(self, prompt, system_prompt=None):
    response = self.client.chat.completions.create(...)
    print(f"Response: {response}")  # Debug
    return response.choices[0].message.content
```

### Validate File Before Processing

```python
import os
from services.audio_processor import AudioProcessor

file_path = "/path/to/file.wav"

print(f"Exists: {os.path.exists(file_path)}")
print(f"Size: {os.path.getsize(file_path) / 1024 / 1024:.2f} MB")

processor = AudioProcessor()
print(f"Valid format: {processor.is_valid_format(file_path)}")
print(f"Info: {processor.get_audio_info(file_path)}")
```

---

## Getting Help

### Before Asking for Help

1. **Check this guide** for your specific error
2. **Search existing issues** on GitHub
3. **Collect relevant information**:
   - Full error message and stack trace
   - Python version (`python --version`)
   - Package versions (`uv pip list`)
   - Operating system
   - Steps to reproduce

### Reporting Issues

When creating an issue, include:

```markdown
**Environment**
- OS: macOS 14.0 / Ubuntu 22.04 / Windows 11
- Python: 3.13.0
- Package version: (from pyproject.toml)

**Description**
Clear description of the issue

**Steps to Reproduce**
1. Step one
2. Step two
3. ...

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Error Message**
```
Full error message and stack trace
```

**Additional Context**
Any other relevant information
```

### Resources

- **GitHub Issues**: [Report bugs and feature requests](https://github.com/your-repo/issues)
- **OpenAI Status**: https://status.openai.com/
- **Deepgram Status**: https://status.deepgram.com/
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Streamlit Docs**: https://docs.streamlit.io/

---

## Quick Reference: Error Messages

| Error Message | Likely Cause | Quick Fix |
|--------------|--------------|-----------|
| `OPENAI_API_KEY field required` | Missing .env | Create .env with API keys |
| `Incorrect API key provided` | Invalid key | Check/regenerate API key |
| `File not found` | Wrong path | Use absolute path |
| `File too large` | Over 100MB | Compress or split file |
| `Unsupported format` | Wrong extension | Convert to supported format |
| `Content validation failed` | Not a call transcript | Ensure dialogue format |
| `Rate limit reached` | Too many requests | Wait and retry |
| `Request timed out` | API slow | Retry or check status |
| `Transcription failed` | Audio issue | Check audio quality |
| `No transcript available` | Missing data | Check previous steps |
