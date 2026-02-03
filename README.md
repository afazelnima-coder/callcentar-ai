# Call Center Quality Grading System

A production-ready multi-agent AI system that automatically evaluates call center interactions. Upload call recordings or transcripts to receive comprehensive quality assessments, detailed scores across multiple categories, and actionable improvement recommendations.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Quality Rubric](#quality-rubric)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)

## Features

- **Multi-Agent Architecture**: Orchestrated workflow using LangGraph for reliable, fault-tolerant processing
- **Audio Transcription**: High-quality speech-to-text with speaker diarization via Deepgram
- **Intelligent Summarization**: GPT-4o powered analysis extracting key points, customer intent, and resolution status
- **Comprehensive Scoring**: 21-item quality rubric across 5 categories with evidence-based feedback
- **Content Validation**: Guardrails AI integration to ensure only valid call center content is processed
- **Real-time Progress**: Live workflow status updates in the Streamlit UI
- **Error Recovery**: Automatic retry logic with graceful degradation
- **Partial Results**: Access to intermediate results even when later stages fail

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd call-center

# Install with uv
uv venv
uv pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
uv run streamlit run app/main.py
```

## Installation

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- OpenAI API key
- Deepgram API key

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd call-center
   ```

2. **Create virtual environment and install dependencies**

   Using uv (recommended):
   ```bash
   uv venv
   uv pip install -e .
   ```

   Using pip:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

3. **Install development dependencies** (optional, for testing)
   ```bash
   uv pip install -e ".[dev]"
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API keys:
   ```env
   OPENAI_API_KEY=sk-your-openai-api-key
   DEEPGRAM_API_KEY=your-deepgram-api-key
   ```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for GPT-4o |
| `DEEPGRAM_API_KEY` | Yes | - | Deepgram API key for transcription |
| `OPENAI_MODEL` | No | `gpt-4o` | OpenAI model for summarization/scoring |
| `MAX_FILE_SIZE_MB` | No | `100` | Maximum upload file size in MB |
| `MAX_RETRIES` | No | `2` | Retry attempts on transient errors |
| `AUDIO_CHUNK_SIZE_MB` | No | `24` | Chunk size for large audio files |
| `PASSING_GRADE_THRESHOLD` | No | `70.0` | Minimum percentage for passing grade |
| `ESCALATION_THRESHOLD` | No | `50.0` | Score below which escalation is recommended |

### Supported File Formats

| Type | Formats | Max Size |
|------|---------|----------|
| Audio | WAV, MP3, M4A, FLAC, OGG, WEBM | 100MB |
| Text | TXT, JSON | 100MB |

## Usage

### Starting the Application

```bash
uv run streamlit run app/main.py
```

The application will open in your browser at `http://localhost:8501`.

### Processing a Call

1. **Upload a file**: Drag and drop or click to upload an audio recording or transcript
2. **Click "Analyze Call"**: The workflow begins processing
3. **Monitor progress**: Watch real-time status updates in the sidebar
4. **Review results**: View comprehensive quality assessment including:
   - Overall grade (A-F)
   - Category scores with evidence
   - Call summary
   - Strengths and improvement areas
   - Full transcript (with speaker labels for audio)

### Programmatic Usage

```python
from graph.workflow import workflow
from datetime import datetime

# Process a file
initial_state = {
    "input_file_path": "/path/to/call.wav",
    "max_retries": 2,
    "started_at": datetime.now(),
}

# Run the workflow
result = workflow.invoke(initial_state)

# Access results
print(f"Grade: {result['overall_grade']}")
print(f"Score: {result['quality_scores'].percentage_score}%")
print(f"Summary: {result['summary'].brief_summary}")
```

## Architecture

The system uses a multi-agent architecture orchestrated by LangGraph:

```
                                    ┌─────────────────┐
                                    │     START       │
                                    └────────┬────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │  Intake Agent   │
                                    │  (Validation)   │
                                    └────────┬────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              │              │              │
                              ▼              │              ▼
                     ┌────────────────┐      │     ┌───────────────┐
                     │ Transcription  │      │     │ Error Handler │
                     │    Agent       │      │     └───────────────┘
                     └────────┬───────┘      │
                              │              │
                              ▼              ▼
                     ┌─────────────────────────┐
                     │   Summarization Agent   │
                     └───────────┬─────────────┘
                                 │
                                 ▼
                     ┌─────────────────────────┐
                     │     Scoring Agent       │
                     └───────────┬─────────────┘
                                 │
                                 ▼
                     ┌─────────────────────────┐
                     │     Routing Agent       │──────► Retry Loop
                     └───────────┬─────────────┘
                                 │
                                 ▼
                        ┌───────────────┐
                        │      END      │
                        └───────────────┘
```

### Agent Responsibilities

| Agent | Responsibility |
|-------|----------------|
| **Intake** | Validates file format, size, extracts metadata, detects content type |
| **Transcription** | Converts audio to text using Deepgram with speaker diarization |
| **Summarization** | Generates structured summary with GPT-4o (issue, resolution, sentiment) |
| **Scoring** | Evaluates call against 21-item rubric, calculates grades |
| **Routing** | Determines next step (success, retry, or failure) |
| **Error Handler** | Generates user-friendly error messages, preserves partial results |

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).

## Quality Rubric

Calls are evaluated across 5 categories with 21 total criteria:

### Greeting & Opening (3 items)
- Proper greeting and self-introduction
- Customer identity verification
- Setting expectations for the call

### Communication Skills (5 items)
- Clarity and appropriate speaking pace
- Professional and friendly tone
- Active listening and clarifying questions
- Empathy and understanding
- Avoiding technical jargon

### Problem Resolution (5 items)
- Correctly identifying the issue
- Product/service knowledge
- Solution quality and appropriateness
- First call resolution
- Proactive assistance

### Professionalism (4 items)
- Courtesy and politeness
- Patience with difficult situations
- Taking ownership (no blame)
- Handling confidential information

### Call Closing (4 items)
- Summarizing the interaction
- Explaining next steps
- Satisfaction check
- Proper closing statement

### Grading Scale

| Grade | Percentage | Description |
|-------|------------|-------------|
| A | 90-100% | Excellent - Exceeds expectations |
| B | 80-89% | Good - Meets all expectations |
| C | 70-79% | Satisfactory - Meets basic expectations |
| D | 60-69% | Needs Improvement - Below expectations |
| F | <60% | Poor - Fails to meet standards |

## Project Structure

```
call-center/
├── app/
│   ├── __init__.py
│   ├── main.py              # Streamlit UI entry point
│   └── config.py            # Pydantic settings configuration
├── agents/
│   ├── __init__.py
│   ├── intake_agent.py      # File validation & metadata extraction
│   ├── transcription_agent.py  # Deepgram transcription
│   ├── summarization_agent.py  # GPT-4o summarization
│   ├── scoring_agent.py     # Quality rubric evaluation
│   └── routing_agent.py     # Workflow control & error handling
├── graph/
│   ├── __init__.py
│   ├── state.py             # TypedDict state schema
│   ├── workflow.py          # LangGraph workflow definition
│   └── edges.py             # Conditional routing functions
├── schemas/
│   ├── __init__.py
│   ├── input_schemas.py     # Input validation schemas
│   ├── output_schemas.py    # QualityScores, CallSummary, etc.
│   └── metadata_schemas.py  # CallMetadata schema
├── services/
│   ├── __init__.py
│   ├── openai_service.py    # OpenAI GPT API wrapper
│   ├── deepgram_service.py  # Deepgram transcription wrapper
│   ├── audio_processor.py   # Audio file metadata extraction
│   └── guardrails_service.py # Content validation service
├── utils/
│   ├── __init__.py
│   └── scoring_utils.py     # Grade calculation utilities
├── tests/                   # Pytest test suite
├── docs/                    # Additional documentation
├── pyproject.toml           # Project dependencies
├── .env.example             # Environment template
└── README.md
```

## Testing

### Running Tests

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest tests/test_agents/test_scoring_agent.py

# Run with verbose output
uv run pytest -v
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_agents/             # Agent unit tests
├── test_graph/              # Workflow and routing tests
├── test_schemas/            # Pydantic model tests
├── test_services/           # Service wrapper tests
└── test_utils/              # Utility function tests
```

## Documentation

- [Architecture Guide](docs/architecture.md) - Detailed system architecture and design decisions
- [API Reference](docs/api.md) - Complete API documentation for all modules
- [Usage Examples](docs/examples.md) - Code examples and integration patterns
- [Deployment Guide](docs/deployment.md) - Deploy to Streamlit Cloud, Docker, Railway, Heroku, or AWS
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## Troubleshooting

### Common Issues

**"No API key provided"**
- Ensure `.env` file exists with valid API keys
- Check that environment variables are loaded

**"File too large"**
- Maximum file size is 100MB by default
- Adjust `MAX_FILE_SIZE_MB` in `.env` if needed

**"Content validation failed"**
- The system validates that content is a call center conversation
- Ensure the audio/text contains a dialogue between agent and customer

**Transcription takes too long**
- Large audio files may take several minutes
- Consider chunking very long recordings

For more troubleshooting help, see [docs/troubleshooting.md](docs/troubleshooting.md).

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
