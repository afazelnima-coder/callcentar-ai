from typing import TypedDict, Optional, List, Annotated
from datetime import datetime

from schemas.output_schemas import QualityScores, CallSummary
from schemas.metadata_schemas import CallMetadata


def merge_lists(left: List, right: List) -> List:
    """Reducer function for list merging."""
    if left is None:
        return right or []
    if right is None:
        return left
    return left + right


class CallCenterState(TypedDict, total=False):
    """
    Central state object passed between all agents.

    All fields are optional (total=False) to allow partial updates.
    Each agent reads from and writes to this shared state.
    """

    # === Input Fields ===
    input_file_path: str  # Path to uploaded file
    input_file_type: str  # 'audio' or 'transcript'
    input_file_name: str  # Original filename
    raw_transcript: Optional[str]  # If user provided transcript directly

    # === Metadata (from Intake Agent) ===
    metadata: Optional[CallMetadata]  # Extracted call metadata
    has_audio: bool  # True if audio file provided
    file_validated: bool  # True if intake validation passed
    validation_errors: List[str]  # List of validation issues

    # === Transcription (from Transcription Agent) ===
    transcript: Optional[str]  # Transcript with speaker labels
    transcript_plain: Optional[str]  # Plain transcript without speaker labels
    speaker_segments: Optional[List[dict]]  # Speaker-labeled segments with timestamps
    num_speakers: Optional[int]  # Number of detected speakers
    transcription_language: Optional[str]  # Detected language
    transcription_duration: Optional[float]  # Audio duration in seconds

    # === Summarization (from Summarization Agent) ===
    summary: Optional[CallSummary]  # Structured call summary
    key_points: Optional[List[str]]  # Bullet points of key topics
    customer_intent: Optional[str]  # Identified customer intent
    resolution_status: Optional[str]  # 'resolved', 'escalated', 'pending'

    # === Quality Scores (from Scoring Agent) ===
    quality_scores: Optional[QualityScores]  # Structured quality assessment
    overall_grade: Optional[str]  # Letter grade (A, B, C, D, F)
    recommendations: Optional[List[str]]  # Improvement suggestions

    # === Routing & Control (from Routing Agent) ===
    workflow_status: str  # 'in_progress', 'completed', 'failed', 'retrying'
    current_step: str  # Current agent/node name
    next_step: Optional[str]  # Determined next step
    partial_results: Optional[dict]  # Any partial results on failure

    # === Error Handling ===
    error: Optional[str]  # Current error message
    error_type: Optional[str]  # Error classification
    error_count: int  # Number of retries attempted
    max_retries: int  # Maximum retry attempts (default: 2)
    error_history: Annotated[List[dict], merge_lists]  # All errors encountered

    # === Timestamps ===
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time_seconds: Optional[float]
