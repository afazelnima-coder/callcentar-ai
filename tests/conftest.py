"""
Shared fixtures for call center quality grading tests.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from schemas.output_schemas import (
    QualityScores,
    CallSummary,
    RubricScore,
    ScoreLevel,
    GreetingAndOpening,
    CommunicationSkills,
    ProblemResolution,
    Professionalism,
    CallClosing,
)
from schemas.metadata_schemas import CallMetadata


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_transcript():
    """Sample call center transcript for testing."""
    return """
**Agent:** Thank you for calling ABC Company, my name is Sarah. How can I help you today?

**Customer:** Hi Sarah, I'm having trouble with my internet connection. It's been dropping out all morning.

**Agent:** I'm sorry to hear that. Let me look into this for you. Can I have your account number please?

**Customer:** Yes, it's 12345678.

**Agent:** Thank you. I can see your account here. Let me run a diagnostic on your line.
Please give me just a moment... I can see there was a service interruption in your area
this morning, but it should be resolved now. Have you tried restarting your router?

**Customer:** No, I haven't tried that yet.

**Agent:** That's okay. Let's try that now. Please unplug your router, wait 30 seconds,
and plug it back in.

**Customer:** Okay, done. Oh, it's working now! Thank you so much!

**Agent:** Wonderful! I'm glad that fixed the issue. Is there anything else I can help you with today?

**Customer:** No, that's all. Thanks for your help!

**Agent:** You're welcome! Thank you for calling ABC Company. Have a great day!
"""


@pytest.fixture
def sample_rubric_score():
    """Create a sample RubricScore."""
    return RubricScore(
        score=4,
        level=ScoreLevel.GOOD,
        evidence="Agent introduced themselves professionally",
        feedback="Consider adding a brief pause after greeting",
    )


@pytest.fixture
def sample_rubric_score_excellent():
    """Create an excellent RubricScore."""
    return RubricScore(
        score=5,
        level=ScoreLevel.EXCELLENT,
        evidence="Exceeded expectations in every way",
        feedback="Keep up the great work",
    )


@pytest.fixture
def sample_rubric_score_poor():
    """Create a poor RubricScore."""
    return RubricScore(
        score=1,
        level=ScoreLevel.POOR,
        evidence="Failed to meet minimum standards",
        feedback="Requires significant improvement",
    )


def create_rubric_score(score: int = 4) -> RubricScore:
    """Helper to create a RubricScore with a given score."""
    level_map = {
        5: ScoreLevel.EXCELLENT,
        4: ScoreLevel.GOOD,
        3: ScoreLevel.SATISFACTORY,
        2: ScoreLevel.NEEDS_IMPROVEMENT,
        1: ScoreLevel.POOR,
    }
    return RubricScore(
        score=score,
        level=level_map[score],
        evidence=f"Sample evidence for score {score}",
        feedback=f"Sample feedback for score {score}",
    )


@pytest.fixture
def sample_quality_scores():
    """Create a sample QualityScores object with all categories."""
    return QualityScores(
        greeting=GreetingAndOpening(
            proper_greeting=create_rubric_score(4),
            verified_customer=create_rubric_score(5),
            set_expectations=create_rubric_score(4),
        ),
        communication=CommunicationSkills(
            clarity=create_rubric_score(4),
            tone=create_rubric_score(5),
            active_listening=create_rubric_score(4),
            empathy=create_rubric_score(4),
            avoided_jargon=create_rubric_score(5),
        ),
        resolution=ProblemResolution(
            understanding=create_rubric_score(5),
            knowledge=create_rubric_score(4),
            solution_quality=create_rubric_score(5),
            first_call_resolution=create_rubric_score(5),
            proactive_help=create_rubric_score(4),
        ),
        professionalism=Professionalism(
            courtesy=create_rubric_score(5),
            patience=create_rubric_score(5),
            ownership=create_rubric_score(4),
            confidentiality=create_rubric_score(5),
        ),
        closing=CallClosing(
            summarized=create_rubric_score(4),
            next_steps=create_rubric_score(4),
            satisfaction_check=create_rubric_score(5),
            proper_closing=create_rubric_score(5),
        ),
        total_points=85,
        percentage_score=89.47,
        overall_grade="B",
        strengths=[
            "Excellent customer verification",
            "Strong problem-solving skills",
            "Professional and courteous demeanor",
        ],
        areas_for_improvement=[
            "Could summarize call details more clearly",
            "Provide more detailed next steps",
            "Be more proactive in offering additional help",
        ],
    )


@pytest.fixture
def sample_call_summary():
    """Create a sample CallSummary object."""
    return CallSummary(
        brief_summary="Customer called about internet connectivity issues. Agent diagnosed the problem as a local service interruption and resolved it by guiding the customer through a router restart.",
        customer_issue="Internet connection dropping intermittently",
        resolution_provided="Router restart resolved the issue after service interruption was cleared",
        customer_sentiment="positive",
        call_category="support",
        key_topics=["internet connectivity", "router restart", "service interruption"],
        action_items=[],
    )


@pytest.fixture
def sample_call_metadata():
    """Create a sample CallMetadata object."""
    return CallMetadata(
        file_name="call_20240115_agent42.wav",
        file_size_bytes=5242880,  # 5MB
        file_format="wav",
        duration_seconds=180.5,
        sample_rate=44100,
        channels=2,
    )


@pytest.fixture
def sample_text_metadata():
    """Create a sample CallMetadata for text file."""
    return CallMetadata(
        file_name="transcript.txt",
        file_size_bytes=4096,
        file_format="txt",
    )


# ============================================================================
# State Fixtures
# ============================================================================


@pytest.fixture
def initial_state():
    """Create an initial workflow state."""
    return {
        "input_file_path": "/tmp/test_call.wav",
        "input_file_name": "test_call.wav",
        "max_retries": 2,
        "error_count": 0,
        "started_at": datetime.now(),
        "workflow_status": "in_progress",
        "error_history": [],
    }


@pytest.fixture
def state_with_transcript(initial_state, sample_transcript):
    """Create a state with transcript."""
    return {
        **initial_state,
        "transcript": sample_transcript,
        "has_audio": False,
        "file_validated": True,
    }


@pytest.fixture
def state_with_summary(state_with_transcript, sample_call_summary):
    """Create a state with summary."""
    return {
        **state_with_transcript,
        "summary": sample_call_summary,
        "resolution_status": "resolved",
    }


@pytest.fixture
def state_with_error():
    """Create a state with an error."""
    return {
        "error": "Test error message",
        "error_type": "TestError",
        "error_count": 1,
        "workflow_status": "failed",
    }


# ============================================================================
# Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_openai_service():
    """Mock OpenAI service."""
    with patch("services.openai_service.OpenAI") as mock:
        service_mock = MagicMock()
        mock.return_value = service_mock
        yield service_mock


@pytest.fixture
def mock_deepgram_service():
    """Mock Deepgram service."""
    with patch("services.deepgram_service.DeepgramClient") as mock:
        service_mock = MagicMock()
        mock.return_value = service_mock
        yield service_mock


@pytest.fixture
def mock_audio_processor():
    """Mock audio processor."""
    with patch("services.audio_processor.mutagen") as mock:
        yield mock


@pytest.fixture
def mock_guardrails():
    """Mock guardrails validation."""
    with patch("services.guardrails_service.Guard") as mock:
        guard_mock = MagicMock()
        mock.return_value = guard_mock
        yield guard_mock


# ============================================================================
# File System Fixtures
# ============================================================================


@pytest.fixture
def temp_audio_file(tmp_path):
    """Create a temporary audio file for testing."""
    audio_file = tmp_path / "test_call.wav"
    # Write some dummy bytes to simulate an audio file
    audio_file.write_bytes(b"RIFF" + b"\x00" * 100)
    return str(audio_file)


@pytest.fixture
def temp_text_file(tmp_path, sample_transcript):
    """Create a temporary text file with transcript."""
    text_file = tmp_path / "transcript.txt"
    text_file.write_text(sample_transcript)
    return str(text_file)


@pytest.fixture
def temp_invalid_file(tmp_path):
    """Create a temporary file with invalid content."""
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("This is just random text, not a call center transcript.")
    return str(invalid_file)
