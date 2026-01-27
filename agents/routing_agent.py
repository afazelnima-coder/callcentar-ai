from typing import Any
from datetime import datetime


def routing_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Analyzes workflow state and determines next steps.

    This agent:
    1. Checks if the workflow completed successfully
    2. Determines if retry is needed and possible
    3. Routes to error handler if max retries exceeded
    4. Calculates processing time on completion

    Returns:
        dict with workflow status and next step
    """
    current_error = state.get("error")
    error_count = state.get("error_count", 0)
    max_retries = state.get("max_retries", 2)

    # Check for successful completion
    if not current_error and state.get("quality_scores"):
        processing_time = _calculate_processing_time(state)

        return {
            "workflow_status": "completed",
            "next_step": "success",
            "completed_at": datetime.now(),
            "processing_time_seconds": processing_time,
            "current_step": "routing",
        }

    # Check if retry is possible
    if current_error and error_count < max_retries:
        # Log error to history
        error_entry = {
            "step": state.get("current_step"),
            "error": current_error,
            "error_type": state.get("error_type"),
            "timestamp": datetime.now().isoformat(),
            "retry_count": error_count,
        }

        return {
            "next_step": "retry",
            "error_history": [error_entry],
            "workflow_status": "retrying",
            "current_step": "routing",
        }

    # Fallback - max retries exceeded
    return {
        "workflow_status": "failed",
        "next_step": "fallback",
        "current_step": "routing",
    }


def error_handler_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Handles errors that cannot be recovered via retry.

    This agent:
    1. Provides user-friendly error messages
    2. Attempts to preserve any partial results
    3. Logs the final error state

    Returns:
        dict with final error status and any partial results
    """
    error = state.get("error", "Unknown error")
    error_type = state.get("error_type", "UnknownError")

    # Generate user-friendly error message
    user_message = _get_user_friendly_error(error_type, error)

    # Check for partial results
    partial_results = {
        "transcript_available": state.get("transcript") is not None,
        "summary_available": state.get("summary") is not None,
        "scores_available": state.get("quality_scores") is not None,
    }

    return {
        "workflow_status": "failed",
        "error": user_message,
        "partial_results": partial_results,
        "completed_at": datetime.now(),
        "current_step": "error_handler",
    }


def _calculate_processing_time(state: dict[str, Any]) -> float:
    """Calculate total processing time in seconds."""
    started = state.get("started_at")
    if started:
        if isinstance(started, datetime):
            return (datetime.now() - started).total_seconds()
    return 0.0


def _get_user_friendly_error(error_type: str, error: str) -> str:
    """Convert technical errors to user-friendly messages."""
    error_messages = {
        "FileNotFoundError": "The uploaded file could not be found. Please try uploading again.",
        "FileTooLargeError": "The file is too large. Please upload a file under 100MB.",
        "UnsupportedFormatError": "This file format is not supported. Please use WAV, MP3, or TXT files.",
        "TranscriptionError": "Could not transcribe the audio. Please ensure the audio is clear and try again.",
        "SummarizationError": "Could not generate summary. Please try again later.",
        "ScoringError": "Could not complete quality scoring. Please try again later.",
        "MissingInputError": "Required input was not provided.",
        "MissingTranscriptError": "Transcript is required but was not available.",
        "MissingScoringInputError": "Cannot score without a transcript.",
    }
    return error_messages.get(error_type, f"An error occurred: {error}")
