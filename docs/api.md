# API Reference

Complete API documentation for all modules in the Call Center Quality Grading System.

## Table of Contents

- [Workflow](#workflow)
- [Agents](#agents)
- [Services](#services)
- [Schemas](#schemas)
- [Utilities](#utilities)

---

## Workflow

### `graph.workflow`

Main workflow orchestration module.

#### `create_workflow() -> StateGraph`

Creates and compiles the call center grading workflow.

**Returns**: Compiled LangGraph StateGraph

**Example**:
```python
from graph.workflow import create_workflow

workflow = create_workflow()
result = workflow.invoke(initial_state)
```

#### `workflow`

Pre-compiled singleton workflow instance.

**Example**:
```python
from graph.workflow import workflow

result = workflow.invoke({
    "input_file_path": "/path/to/file.wav",
    "max_retries": 2,
})
```

### `graph.state.CallCenterState`

TypedDict defining the workflow state schema.

**Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `input_file_path` | `str` | Path to input file |
| `input_file_name` | `str` | Original filename |
| `input_file_type` | `str` | "audio" or "transcript" |
| `metadata` | `CallMetadata` | File metadata |
| `has_audio` | `bool` | Whether input is audio |
| `file_validated` | `bool` | Validation status |
| `transcript` | `str` | Full transcript text |
| `transcript_plain` | `str` | Plain text transcript |
| `speaker_segments` | `List[dict]` | Speaker segment data |
| `num_speakers` | `int` | Number of speakers |
| `summary` | `CallSummary` | Call summary |
| `quality_scores` | `QualityScores` | Quality assessment |
| `overall_grade` | `str` | Letter grade (A-F) |
| `recommendations` | `List[str]` | Improvement recommendations |
| `current_step` | `str` | Current workflow step |
| `workflow_status` | `str` | Status: in_progress, completed, failed |
| `error` | `Optional[str]` | Error message if any |
| `error_type` | `Optional[str]` | Error type classification |
| `error_count` | `int` | Number of errors encountered |
| `error_history` | `List[dict]` | History of all errors |
| `max_retries` | `int` | Maximum retry attempts |
| `started_at` | `datetime` | Workflow start time |
| `completed_at` | `datetime` | Workflow end time |
| `processing_time_seconds` | `float` | Total processing time |

### `graph.edges`

Conditional routing functions for workflow edges.

#### `route_after_intake(state: dict) -> str`

Determines next step after intake.

**Parameters**:
- `state`: Current workflow state

**Returns**: `"transcription"`, `"summarization"`, or `"error_handler"`

**Logic**:
```python
if state.get("error"):
    return "error_handler"
if state.get("has_audio") and not state.get("transcript"):
    return "transcription"
return "summarization"
```

#### `route_after_transcription(state: dict) -> str`

Determines next step after transcription.

**Returns**: `"summarization"` or `"error_handler"`

#### `route_after_summarization(state: dict) -> str`

Determines next step after summarization.

**Returns**: `"scoring"` or `"error_handler"`

#### `route_after_scoring(state: dict) -> str`

Determines next step after scoring.

**Returns**: `"routing"` or `"error_handler"`

#### `route_after_routing(state: dict) -> str`

Determines final routing decision.

**Returns**: `"__end__"`, `"transcription"` (retry), or `"error_handler"`

---

## Agents

### `agents.intake_agent`

File validation and metadata extraction.

#### `call_intake_node(state: dict) -> dict`

Entry point agent that validates input files.

**Parameters**:
- `state`: Must contain `input_file_path`

**Returns**: State updates including:
- `metadata`: CallMetadata object
- `has_audio`: bool
- `file_validated`: bool
- `input_file_type`: "audio" or "transcript"
- `transcript`: str (if text file)
- `error`: str (if validation fails)

**Raises**:
- `ContentValidationError`: If content is not a call center conversation

**Example**:
```python
from agents.intake_agent import call_intake_node

state = {"input_file_path": "/path/to/call.wav"}
result = call_intake_node(state)

if result.get("file_validated"):
    print(f"File type: {result['input_file_type']}")
```

#### `validate_transcript_content(transcript: str) -> tuple[bool, str]`

Validates that transcript content is a call center conversation.

**Parameters**:
- `transcript`: Text to validate

**Returns**: Tuple of (is_valid, reason)

#### `ContentValidationError`

Exception raised when content validation fails.

### `agents.transcription_agent`

Audio transcription with speaker identification.

#### `transcription_node(state: dict) -> dict`

Transcribes audio files using Deepgram.

**Parameters**:
- `state`: Must contain `input_file_path`

**Returns**: State updates including:
- `transcript`: Formatted transcript with speaker labels
- `transcript_plain`: Raw text without formatting
- `speaker_segments`: List of speaker segment dictionaries
- `num_speakers`: Number of detected speakers
- `transcription_language`: Detected language code
- `transcription_duration`: Audio duration in seconds

**Skips**: If `state["transcript"]` already exists

**Raises**:
- `ContentValidationError`: If transcribed content is not valid

**Example**:
```python
from agents.transcription_agent import transcription_node

state = {
    "input_file_path": "/path/to/audio.wav",
    "transcript": None,
}
result = transcription_node(state)
print(result["transcript"])
```

### `agents.summarization_agent`

Call summarization using GPT-4o.

#### `summarization_node(state: dict) -> dict`

Generates structured call summary.

**Parameters**:
- `state`: Must contain `transcript`

**Returns**: State updates including:
- `summary`: CallSummary object
- `key_points`: List of key topics
- `customer_intent`: Customer's primary issue
- `resolution_status`: "resolved", "escalated", or "pending"

**Example**:
```python
from agents.summarization_agent import summarization_node

state = {"transcript": "Agent: Hello... Customer: Hi..."}
result = summarization_node(state)
print(result["summary"].brief_summary)
```

### `agents.scoring_agent`

Quality scoring against rubric.

#### `scoring_node(state: dict) -> dict`

Evaluates call quality using 21-item rubric.

**Parameters**:
- `state`: Must contain `transcript`, optionally `summary`

**Returns**: State updates including:
- `quality_scores`: QualityScores object
- `overall_grade`: Letter grade (A-F)
- `recommendations`: List of improvement areas

**Example**:
```python
from agents.scoring_agent import scoring_node

state = {
    "transcript": "Agent: Hello...",
    "summary": call_summary_object,
}
result = scoring_node(state)
print(f"Grade: {result['overall_grade']}")
print(f"Score: {result['quality_scores'].percentage_score}%")
```

### `agents.routing_agent`

Workflow control and error handling.

#### `routing_node(state: dict) -> dict`

Analyzes state and determines next steps.

**Parameters**:
- `state`: Full workflow state

**Returns**: State updates including:
- `workflow_status`: "completed", "retrying", or "failed"
- `next_step`: "success", "retry", or "fallback"
- `completed_at`: datetime (on success)
- `processing_time_seconds`: float (on success)
- `error_history`: List of error entries (on retry)

#### `error_handler_node(state: dict) -> dict`

Handles unrecoverable errors.

**Parameters**:
- `state`: State containing error information

**Returns**: State updates including:
- `workflow_status`: "failed"
- `error`: User-friendly error message
- `partial_results`: Dict indicating available partial results
- `completed_at`: datetime

---

## Services

### `services.openai_service.OpenAIService`

Wrapper for OpenAI GPT API.

#### `__init__()`

Initializes service with API key from settings.

#### `generate(prompt: str, system_prompt: str | None = None) -> str`

Generates text completion.

**Parameters**:
- `prompt`: User prompt
- `system_prompt`: Optional system prompt

**Returns**: Generated text response

**Retry**: 3 attempts with exponential backoff on rate limits

**Example**:
```python
from services.openai_service import OpenAIService

service = OpenAIService()
response = service.generate(
    prompt="Summarize this call...",
    system_prompt="You are a call center analyst.",
)
```

#### `generate_structured(prompt: str, response_model: Type[T], system_prompt: str | None = None) -> T`

Generates structured output using Pydantic model.

**Parameters**:
- `prompt`: User prompt
- `response_model`: Pydantic model class for response
- `system_prompt`: Optional system prompt

**Returns**: Instance of response_model

**Example**:
```python
from services.openai_service import OpenAIService
from schemas.output_schemas import CallSummary

service = OpenAIService()
summary = service.generate_structured(
    prompt="Analyze this transcript...",
    response_model=CallSummary,
)
```

### `services.deepgram_service.DeepgramService`

Wrapper for Deepgram transcription API.

#### `transcribe(file_path: str) -> dict`

Transcribes audio file with speaker diarization.

**Parameters**:
- `file_path`: Path to audio file

**Returns**: Dictionary containing:
- `text`: Plain text transcript
- `formatted_transcript`: Transcript with speaker labels
- `speakers`: List of speaker segments
- `num_speakers`: Number of detected speakers
- `language`: Detected language
- `duration`: Audio duration in seconds

### `services.audio_processor.AudioProcessor`

Audio file metadata extraction using mutagen.

#### `get_audio_info(file_path: str) -> dict`

Extracts audio file information.

**Parameters**:
- `file_path`: Path to audio file

**Returns**: Dictionary containing:
- `duration`: Duration in seconds
- `sample_rate`: Sample rate in Hz
- `channels`: Number of channels
- `format`: File format
- `bit_rate`: Bit rate (if available)

#### `is_valid_format(file_path: str) -> bool`

Checks if file format is supported.

**Supported formats**: `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.webm`

#### `get_duration_seconds(file_path: str) -> float`

Gets audio duration in seconds.

#### `get_file_size_mb(file_path: str) -> float`

Gets file size in megabytes.

### `services.guardrails_service.GuardrailsService`

Content validation using Guardrails AI.

#### `validate_call_center_content(content: str) -> tuple[bool, str]`

Validates content is a call center conversation.

**Parameters**:
- `content`: Text to validate

**Returns**: Tuple of (is_valid, message)

**Example**:
```python
from services.guardrails_service import GuardrailsService

service = GuardrailsService()
is_valid, message = service.validate_call_center_content(transcript)

if not is_valid:
    print(f"Invalid: {message}")
```

---

## Schemas

### `schemas.output_schemas`

Output data structures.

#### `ScoreLevel`

Enum for rubric score levels.

```python
class ScoreLevel(str, Enum):
    EXCELLENT = "excellent"      # 5 points
    GOOD = "good"                # 4 points
    SATISFACTORY = "satisfactory"  # 3 points
    NEEDS_IMPROVEMENT = "needs_improvement"  # 2 points
    POOR = "poor"                # 1 point
```

#### `RubricScore`

Individual rubric item score.

```python
class RubricScore(BaseModel):
    score: int = Field(ge=1, le=5)
    level: ScoreLevel
    evidence: str  # Quote or observation supporting score
    feedback: str  # Constructive improvement feedback
```

#### `GreetingAndOpening`

Greeting category scores (3 items).

```python
class GreetingAndOpening(BaseModel):
    proper_greeting: RubricScore
    verified_customer: RubricScore
    set_expectations: RubricScore
```

#### `CommunicationSkills`

Communication category scores (5 items).

```python
class CommunicationSkills(BaseModel):
    clarity: RubricScore
    tone: RubricScore
    active_listening: RubricScore
    empathy: RubricScore
    avoided_jargon: RubricScore
```

#### `ProblemResolution`

Resolution category scores (5 items).

```python
class ProblemResolution(BaseModel):
    understanding: RubricScore
    knowledge: RubricScore
    solution_quality: RubricScore
    first_call_resolution: RubricScore
    proactive_help: RubricScore
```

#### `Professionalism`

Professionalism category scores (4 items).

```python
class Professionalism(BaseModel):
    courtesy: RubricScore
    patience: RubricScore
    ownership: RubricScore
    confidentiality: RubricScore
```

#### `CallClosing`

Closing category scores (4 items).

```python
class CallClosing(BaseModel):
    summarized: RubricScore
    next_steps: RubricScore
    satisfaction_check: RubricScore
    proper_closing: RubricScore
```

#### `QualityScores`

Complete quality assessment.

```python
class QualityScores(BaseModel):
    # Category scores
    greeting: GreetingAndOpening
    communication: CommunicationSkills
    resolution: ProblemResolution
    professionalism: Professionalism
    closing: CallClosing

    # Aggregate scores
    total_points: int
    max_possible_points: int = 95
    percentage_score: float

    # Overall assessment
    overall_grade: str  # A, B, C, D, F
    strengths: List[str]
    areas_for_improvement: List[str]

    # Compliance
    compliance_issues: List[str] = []
    escalation_recommended: bool = False
```

#### `CallSummary`

Structured call summary.

```python
class CallSummary(BaseModel):
    brief_summary: str = Field(max_length=500)
    customer_issue: str
    resolution_provided: str
    customer_sentiment: str  # positive, neutral, negative, mixed
    call_category: str  # support, complaint, inquiry, sales
    key_topics: List[str]
    action_items: List[str] = []
```

### `schemas.metadata_schemas`

Metadata structures.

#### `CallMetadata`

File metadata.

```python
class CallMetadata(BaseModel):
    # Required
    file_name: str
    file_size_bytes: int
    file_format: str

    # Audio-specific (optional)
    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None

    # Call context (optional)
    call_id: Optional[str] = None
    agent_id: Optional[str] = None
    customer_id: Optional[str] = None
    call_date: Optional[datetime] = None
    call_type: Optional[str] = None
```

---

## Utilities

### `utils.scoring_utils`

Grade calculation utilities.

#### `calculate_overall_grade(percentage: float) -> str`

Converts percentage to letter grade.

**Parameters**:
- `percentage`: Score percentage (0-100+)

**Returns**: Letter grade (A, B, C, D, or F)

**Grade Boundaries**:
- A: 90% and above
- B: 80-89%
- C: 70-79%
- D: 60-69%
- F: Below 60%

**Example**:
```python
from utils.scoring_utils import calculate_overall_grade

grade = calculate_overall_grade(85.5)  # Returns "B"
```

#### `calculate_total_score(scores: QualityScores) -> tuple[int, float]`

Calculates total points and percentage from all rubric items.

**Parameters**:
- `scores`: QualityScores object

**Returns**: Tuple of (total_points, percentage)

**Example**:
```python
from utils.scoring_utils import calculate_total_score

total, percentage = calculate_total_score(quality_scores)
print(f"Total: {total}/105, Percentage: {percentage:.1f}%")
```

---

## Configuration

### `app.config.Settings`

Application configuration using pydantic-settings.

```python
class Settings(BaseSettings):
    # Required
    openai_api_key: str
    deepgram_api_key: str

    # Optional with defaults
    openai_model: str = "gpt-4o"
    max_file_size_mb: int = 100
    max_retries: int = 2
    audio_chunk_size_mb: int = 24
    passing_grade_threshold: float = 70.0
    escalation_threshold: float = 50.0
```

#### `settings`

Singleton settings instance loaded from environment.

```python
from app.config import settings

print(settings.openai_model)  # "gpt-4o"
```
