# Usage Examples

Practical examples and code snippets for integrating with the Call Center Quality Grading System.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Programmatic Integration](#programmatic-integration)
- [Batch Processing](#batch-processing)
- [Custom Workflows](#custom-workflows)
- [Working with Results](#working-with-results)
- [Error Handling](#error-handling)
- [Testing](#testing)

---

## Basic Usage

### Using the Streamlit UI

The simplest way to use the system is through the web interface:

```bash
# Start the application
uv run streamlit run app/main.py
```

1. Open `http://localhost:8501` in your browser
2. Upload an audio file (WAV, MP3, etc.) or text transcript
3. Click "Analyze Call"
4. View the results

### Sample Transcript Format

For text file input, format transcripts with speaker labels:

```text
Agent: Thank you for calling ABC Company, my name is Sarah. How can I help you today?

Customer: Hi Sarah, I'm having trouble with my internet connection.

Agent: I'm sorry to hear that. Can I have your account number please?

Customer: Yes, it's 12345678.

Agent: Thank you. Let me look into this for you. I can see there was a service interruption in your area this morning. Have you tried restarting your router?

Customer: No, I haven't tried that yet.

Agent: Please unplug your router, wait 30 seconds, and plug it back in.

Customer: Okay, done. It's working now! Thank you!

Agent: Wonderful! Is there anything else I can help you with?

Customer: No, that's all. Thanks!

Agent: You're welcome! Thank you for calling ABC Company. Have a great day!
```

---

## Programmatic Integration

### Basic Workflow Invocation

```python
from datetime import datetime
from graph.workflow import workflow

def analyze_call(file_path: str) -> dict:
    """
    Analyze a call recording or transcript.

    Args:
        file_path: Path to audio file or transcript

    Returns:
        Complete workflow result state
    """
    initial_state = {
        "input_file_path": file_path,
        "max_retries": 2,
        "started_at": datetime.now(),
        "error_count": 0,
        "error_history": [],
    }

    result = workflow.invoke(initial_state)
    return result

# Usage
result = analyze_call("/path/to/call.wav")

if result.get("workflow_status") == "completed":
    print(f"Grade: {result['overall_grade']}")
    print(f"Score: {result['quality_scores'].percentage_score:.1f}%")
else:
    print(f"Error: {result.get('error')}")
```

### Streaming Progress Updates

```python
from datetime import datetime
from graph.workflow import workflow

def analyze_call_with_progress(file_path: str):
    """
    Analyze call with real-time progress updates.
    """
    initial_state = {
        "input_file_path": file_path,
        "max_retries": 2,
        "started_at": datetime.now(),
        "error_count": 0,
        "error_history": [],
    }

    # Use stream() instead of invoke() for progress updates
    for event in workflow.stream(initial_state):
        # Each event contains the node name and state updates
        for node_name, state_update in event.items():
            current_step = state_update.get("current_step", node_name)
            print(f"Completed: {current_step}")

            # Check for errors
            if state_update.get("error"):
                print(f"  Error: {state_update['error']}")

    return state_update

# Usage
result = analyze_call_with_progress("/path/to/call.wav")
```

### Using Individual Agents

```python
from agents.intake_agent import call_intake_node
from agents.summarization_agent import summarization_node
from agents.scoring_agent import scoring_node

# Step 1: Validate and extract metadata
intake_result = call_intake_node({
    "input_file_path": "/path/to/transcript.txt"
})

if intake_result.get("error"):
    print(f"Validation failed: {intake_result['error']}")
else:
    # Step 2: Generate summary
    summary_result = summarization_node({
        "transcript": intake_result["transcript"]
    })

    # Step 3: Score the call
    scoring_result = scoring_node({
        "transcript": intake_result["transcript"],
        "summary": summary_result["summary"]
    })

    print(f"Grade: {scoring_result['overall_grade']}")
```

---

## Batch Processing

### Process Multiple Files

```python
import os
from datetime import datetime
from pathlib import Path
from graph.workflow import workflow
import json

def process_batch(input_dir: str, output_dir: str):
    """
    Process all call files in a directory.

    Args:
        input_dir: Directory containing call files
        output_dir: Directory for results
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Supported extensions
    extensions = {'.wav', '.mp3', '.m4a', '.txt'}

    results = []

    for file_path in input_path.iterdir():
        if file_path.suffix.lower() not in extensions:
            continue

        print(f"Processing: {file_path.name}")

        try:
            result = workflow.invoke({
                "input_file_path": str(file_path),
                "max_retries": 2,
                "started_at": datetime.now(),
                "error_count": 0,
                "error_history": [],
            })

            # Extract key results
            summary = {
                "file": file_path.name,
                "status": result.get("workflow_status"),
                "grade": result.get("overall_grade"),
                "score": result.get("quality_scores", {}).percentage_score if result.get("quality_scores") else None,
                "error": result.get("error"),
            }

            results.append(summary)

            # Save detailed results
            detail_file = output_path / f"{file_path.stem}_results.json"
            with open(detail_file, "w") as f:
                # Convert Pydantic models to dict
                serializable = {
                    k: v.model_dump() if hasattr(v, 'model_dump') else v
                    for k, v in result.items()
                    if k not in ['started_at', 'completed_at']  # Skip datetime
                }
                json.dump(serializable, f, indent=2, default=str)

        except Exception as e:
            results.append({
                "file": file_path.name,
                "status": "error",
                "error": str(e),
            })

    # Save summary
    with open(output_path / "batch_summary.json", "w") as f:
        json.dump(results, f, indent=2)

    return results

# Usage
results = process_batch("./calls/", "./results/")

# Print summary
for r in results:
    status = "PASS" if r.get("grade") in ["A", "B", "C"] else "FAIL"
    print(f"{r['file']}: {r.get('grade', 'N/A')} ({status})")
```

### Parallel Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from graph.workflow import workflow

def analyze_single(file_path: str) -> dict:
    """Process a single file."""
    return workflow.invoke({
        "input_file_path": file_path,
        "max_retries": 2,
        "started_at": datetime.now(),
        "error_count": 0,
        "error_history": [],
    })

def process_parallel(file_paths: list[str], max_workers: int = 4) -> list[dict]:
    """
    Process multiple files in parallel.

    Args:
        file_paths: List of file paths
        max_workers: Maximum concurrent workers

    Returns:
        List of results
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(analyze_single, file_paths))

    return results

# Usage
files = [
    "/path/to/call1.wav",
    "/path/to/call2.wav",
    "/path/to/call3.wav",
]

results = process_parallel(files, max_workers=3)
```

---

## Custom Workflows

### Adding Pre-processing

```python
from datetime import datetime
from graph.workflow import workflow

def preprocess_transcript(text: str) -> str:
    """Clean up transcript before processing."""
    # Remove timestamps
    import re
    text = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', text)

    # Normalize speaker labels
    text = text.replace("Rep:", "Agent:")
    text = text.replace("CSR:", "Agent:")
    text = text.replace("Caller:", "Customer:")

    return text.strip()

def analyze_with_preprocessing(file_path: str) -> dict:
    """Analyze with custom preprocessing."""

    # Read and preprocess
    with open(file_path, 'r') as f:
        raw_text = f.read()

    cleaned_text = preprocess_transcript(raw_text)

    # Save to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(cleaned_text)
        temp_path = f.name

    try:
        result = workflow.invoke({
            "input_file_path": temp_path,
            "max_retries": 2,
            "started_at": datetime.now(),
            "error_count": 0,
            "error_history": [],
        })
    finally:
        import os
        os.unlink(temp_path)

    return result
```

### Custom Scoring Thresholds

```python
def evaluate_with_custom_thresholds(result: dict) -> dict:
    """
    Apply custom pass/fail thresholds.

    Args:
        result: Workflow result

    Returns:
        Evaluation with custom criteria
    """
    scores = result.get("quality_scores")

    if not scores:
        return {"passed": False, "reason": "No scores available"}

    # Custom thresholds
    MINIMUM_SCORE = 75.0  # Overall minimum
    CRITICAL_CATEGORIES = ["empathy", "solution_quality", "first_call_resolution"]
    CRITICAL_MINIMUM = 3  # Minimum score for critical items

    evaluation = {
        "passed": True,
        "overall_score": scores.percentage_score,
        "failures": [],
    }

    # Check overall score
    if scores.percentage_score < MINIMUM_SCORE:
        evaluation["passed"] = False
        evaluation["failures"].append(
            f"Overall score {scores.percentage_score:.1f}% below minimum {MINIMUM_SCORE}%"
        )

    # Check critical categories
    critical_scores = {
        "empathy": scores.communication.empathy.score,
        "solution_quality": scores.resolution.solution_quality.score,
        "first_call_resolution": scores.resolution.first_call_resolution.score,
    }

    for category, score in critical_scores.items():
        if score < CRITICAL_MINIMUM:
            evaluation["passed"] = False
            evaluation["failures"].append(
                f"{category} score ({score}) below minimum ({CRITICAL_MINIMUM})"
            )

    return evaluation

# Usage
result = workflow.invoke(initial_state)
evaluation = evaluate_with_custom_thresholds(result)

if evaluation["passed"]:
    print("Call PASSED quality standards")
else:
    print("Call FAILED:")
    for failure in evaluation["failures"]:
        print(f"  - {failure}")
```

---

## Working with Results

### Extracting Detailed Scores

```python
def print_detailed_scores(result: dict):
    """Print all rubric scores with evidence."""
    scores = result.get("quality_scores")

    if not scores:
        print("No scores available")
        return

    categories = [
        ("Greeting & Opening", scores.greeting),
        ("Communication Skills", scores.communication),
        ("Problem Resolution", scores.resolution),
        ("Professionalism", scores.professionalism),
        ("Call Closing", scores.closing),
    ]

    for category_name, category in categories:
        print(f"\n=== {category_name} ===")

        for field_name, rubric_score in category:
            print(f"\n{field_name.replace('_', ' ').title()}")
            print(f"  Score: {rubric_score.score}/5 ({rubric_score.level.value})")
            print(f"  Evidence: {rubric_score.evidence}")
            print(f"  Feedback: {rubric_score.feedback}")

    print(f"\n=== OVERALL ===")
    print(f"Total Points: {scores.total_points}/{scores.max_possible_points}")
    print(f"Percentage: {scores.percentage_score:.1f}%")
    print(f"Grade: {scores.overall_grade}")

    print(f"\nStrengths:")
    for s in scores.strengths:
        print(f"  + {s}")

    print(f"\nAreas for Improvement:")
    for a in scores.areas_for_improvement:
        print(f"  - {a}")

# Usage
print_detailed_scores(result)
```

### Generating Reports

```python
def generate_report(result: dict, output_path: str):
    """
    Generate a markdown report from results.

    Args:
        result: Workflow result
        output_path: Path for output file
    """
    scores = result.get("quality_scores")
    summary = result.get("summary")

    report = f"""# Call Quality Assessment Report

## Overview

| Metric | Value |
|--------|-------|
| Overall Grade | **{result.get('overall_grade', 'N/A')}** |
| Score | {scores.percentage_score:.1f}% |
| Total Points | {scores.total_points}/{scores.max_possible_points} |
| Status | {result.get('workflow_status', 'N/A')} |

## Call Summary

{summary.brief_summary if summary else 'N/A'}

### Details

- **Customer Issue**: {summary.customer_issue if summary else 'N/A'}
- **Resolution**: {summary.resolution_provided if summary else 'N/A'}
- **Sentiment**: {summary.customer_sentiment if summary else 'N/A'}
- **Category**: {summary.call_category if summary else 'N/A'}

## Scores by Category

### Greeting & Opening
| Criterion | Score | Level |
|-----------|-------|-------|
| Proper Greeting | {scores.greeting.proper_greeting.score}/5 | {scores.greeting.proper_greeting.level.value} |
| Verified Customer | {scores.greeting.verified_customer.score}/5 | {scores.greeting.verified_customer.level.value} |
| Set Expectations | {scores.greeting.set_expectations.score}/5 | {scores.greeting.set_expectations.level.value} |

### Communication Skills
| Criterion | Score | Level |
|-----------|-------|-------|
| Clarity | {scores.communication.clarity.score}/5 | {scores.communication.clarity.level.value} |
| Tone | {scores.communication.tone.score}/5 | {scores.communication.tone.level.value} |
| Active Listening | {scores.communication.active_listening.score}/5 | {scores.communication.active_listening.level.value} |
| Empathy | {scores.communication.empathy.score}/5 | {scores.communication.empathy.level.value} |
| Avoided Jargon | {scores.communication.avoided_jargon.score}/5 | {scores.communication.avoided_jargon.level.value} |

## Key Strengths

"""
    for strength in scores.strengths:
        report += f"- {strength}\n"

    report += "\n## Areas for Improvement\n\n"
    for area in scores.areas_for_improvement:
        report += f"- {area}\n"

    if scores.compliance_issues:
        report += "\n## Compliance Issues\n\n"
        for issue in scores.compliance_issues:
            report += f"- {issue}\n"

    if scores.escalation_recommended:
        report += "\n> **Note**: This call has been flagged for escalation review.\n"

    with open(output_path, "w") as f:
        f.write(report)

    print(f"Report saved to: {output_path}")

# Usage
generate_report(result, "call_report.md")
```

### Exporting to JSON

```python
import json
from datetime import datetime

def export_to_json(result: dict, output_path: str):
    """Export results to JSON format."""

    def serialize(obj):
        """Custom serializer for non-JSON types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, default=serialize)

# Usage
export_to_json(result, "call_results.json")
```

---

## Error Handling

### Handling Workflow Errors

```python
from datetime import datetime
from graph.workflow import workflow
from agents.intake_agent import ContentValidationError

def safe_analyze(file_path: str) -> dict:
    """
    Safely analyze a call with comprehensive error handling.
    """
    try:
        result = workflow.invoke({
            "input_file_path": file_path,
            "max_retries": 2,
            "started_at": datetime.now(),
            "error_count": 0,
            "error_history": [],
        })

        if result.get("workflow_status") == "failed":
            return {
                "success": False,
                "error": result.get("error"),
                "error_type": result.get("error_type"),
                "partial_results": result.get("partial_results"),
            }

        return {
            "success": True,
            "grade": result.get("overall_grade"),
            "score": result.get("quality_scores").percentage_score,
            "summary": result.get("summary"),
        }

    except ContentValidationError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "ContentValidationError",
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "error_type": "FileNotFoundError",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }

# Usage
result = safe_analyze("/path/to/call.wav")

if result["success"]:
    print(f"Grade: {result['grade']}")
else:
    print(f"Failed: {result['error']}")
```

### Retry with Different Settings

```python
def analyze_with_fallback(file_path: str) -> dict:
    """Try with default settings, then fall back to more lenient settings."""

    # First attempt with standard settings
    result = workflow.invoke({
        "input_file_path": file_path,
        "max_retries": 2,
        "started_at": datetime.now(),
        "error_count": 0,
        "error_history": [],
    })

    if result.get("workflow_status") == "completed":
        return result

    # Retry with more retries
    print("First attempt failed, retrying with extended settings...")

    result = workflow.invoke({
        "input_file_path": file_path,
        "max_retries": 5,
        "started_at": datetime.now(),
        "error_count": 0,
        "error_history": [],
    })

    return result
```

---

## Testing

### Unit Test Example

```python
import pytest
from unittest.mock import patch, MagicMock
from agents.scoring_agent import scoring_node

class TestScoringAgent:
    """Tests for scoring agent."""

    @patch("agents.scoring_agent.OpenAIService")
    def test_scores_transcript(self, mock_openai, sample_quality_scores):
        """Should generate scores for valid transcript."""
        # Setup mock
        mock_service = MagicMock()
        mock_openai.return_value = mock_service
        mock_service.generate_structured.return_value = sample_quality_scores

        # Execute
        state = {
            "transcript": "Agent: Hello...",
            "summary": None,
        }
        result = scoring_node(state)

        # Verify
        assert result["quality_scores"] is not None
        assert result["overall_grade"] in ["A", "B", "C", "D", "F"]
        assert result["error"] is None

    def test_error_without_transcript(self):
        """Should return error when no transcript."""
        state = {"transcript": None}
        result = scoring_node(state)

        assert "error" in result
        assert result["error_type"] == "MissingScoringInputError"
```

### Integration Test Example

```python
import pytest
from datetime import datetime
from graph.workflow import workflow

@pytest.fixture
def sample_transcript_file(tmp_path):
    """Create a temporary transcript file."""
    content = """
    Agent: Thank you for calling. How can I help?
    Customer: I have a billing question.
    Agent: I'd be happy to help with that.
    Customer: Great, thanks!
    Agent: Is there anything else?
    Customer: No, that's all.
    Agent: Thank you for calling!
    """
    file_path = tmp_path / "test_transcript.txt"
    file_path.write_text(content)
    return str(file_path)

def test_full_workflow(sample_transcript_file):
    """Test complete workflow execution."""
    result = workflow.invoke({
        "input_file_path": sample_transcript_file,
        "max_retries": 1,
        "started_at": datetime.now(),
        "error_count": 0,
        "error_history": [],
    })

    # Verify completion
    assert result["workflow_status"] in ["completed", "failed"]

    if result["workflow_status"] == "completed":
        assert result["overall_grade"] in ["A", "B", "C", "D", "F"]
        assert result["quality_scores"] is not None
        assert result["summary"] is not None
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=. --cov-report=html

# Run specific test file
uv run pytest tests/test_agents/test_scoring_agent.py -v

# Run tests matching pattern
uv run pytest -k "test_scoring" -v
```
