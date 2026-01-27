# Call Center Quality Grading System

A multi-agent system that automatically grades call center calls using AI. Upload a call recording or transcript and receive detailed quality scores, summaries, and improvement recommendations.

## Features

- **Multi-agent architecture** using LangGraph for orchestration
- **Audio transcription** using OpenAI Whisper API
- **Intelligent summarization** of call content and key points
- **Quality scoring** using a 19-item rubric across 5 categories
- **Streamlit UI** for easy file upload and results viewing

## Architecture

```
START -> Intake -> [Transcription] -> Summarization -> Scoring -> Routing -> END
```

### Agents

1. **Intake Agent** - Validates input files and extracts metadata
2. **Transcription Agent** - Converts audio to text using Whisper (skipped for text files)
3. **Summarization Agent** - Generates call summary and identifies key points
4. **Quality Scoring Agent** - Evaluates against 19-item rubric
5. **Routing Agent** - Handles workflow control and error recovery

## Quality Rubric

The system evaluates calls across 5 categories (19 total items):

| Category | Items |
|----------|-------|
| Greeting & Opening | Proper greeting, customer verification, set expectations |
| Communication | Clarity, tone, active listening, empathy, avoided jargon |
| Problem Resolution | Understanding, knowledge, solution quality, FCR, proactive help |
| Professionalism | Courtesy, patience, ownership, confidentiality |
| Call Closing | Summary, next steps, satisfaction check, proper closing |

**Grading Scale:** A (90%+), B (80-89%), C (70-79%), D (60-69%), F (<60%)

## Installation

1. Clone the repository and navigate to the project directory

2. Create a virtual environment and install dependencies:
   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

3. Install ffmpeg (required for audio processing):
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt-get install ffmpeg
   ```

4. Copy `.env.example` to `.env` and add your OpenAI API key:
   ```bash
   cp .env.example .env
   # Edit .env and set OPENAI_API_KEY
   ```

## Usage

Start the Streamlit app:

```bash
source .venv/bin/activate
streamlit run app/main.py
```

Then:
1. Upload an audio file (WAV, MP3, M4A, FLAC) or transcript (TXT)
2. Click "Analyze Call"
3. View the quality assessment results

## Supported Formats

- **Audio:** WAV, MP3, M4A, FLAC, OGG, WEBM
- **Text:** TXT, JSON

## Configuration

Environment variables (set in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| OPENAI_API_KEY | required | Your OpenAI API key |
| OPENAI_MODEL | gpt-4o | Model for summarization/scoring |
| WHISPER_MODEL | whisper-1 | Model for transcription |
| MAX_FILE_SIZE_MB | 100 | Maximum upload file size |
| MAX_RETRIES | 2 | Retry attempts on API errors |

## Project Structure

```
call-center/
├── app/
│   ├── main.py          # Streamlit UI
│   └── config.py        # Configuration
├── agents/              # LangGraph agent nodes
├── graph/
│   ├── state.py         # State schema
│   ├── workflow.py      # Graph definition
│   └── edges.py         # Conditional routing
├── schemas/             # Pydantic models
├── services/            # API wrappers
└── utils/               # Utilities
```
