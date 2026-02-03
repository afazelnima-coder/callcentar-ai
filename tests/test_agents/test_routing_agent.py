"""
Tests for agents/routing_agent.py - Routing and error handling.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from agents.routing_agent import (
    routing_node,
    error_handler_node,
    _calculate_processing_time,
    _get_user_friendly_error,
)


class TestRoutingNode:
    """Tests for routing_node function."""

    def test_success_when_quality_scores_present(self, sample_quality_scores):
        """Should route to success when quality_scores exist and no error."""
        state = {
            "quality_scores": sample_quality_scores,
            "started_at": datetime.now(),
        }
        result = routing_node(state)

        assert result["workflow_status"] == "completed"
        assert result["next_step"] == "success"
        assert result["current_step"] == "routing"
        assert "completed_at" in result
        assert "processing_time_seconds" in result

    def test_retry_when_error_and_retries_available(self):
        """Should route to retry when error exists and retries available."""
        state = {
            "error": "Temporary failure",
            "error_type": "TranscriptionError",
            "error_count": 1,
            "max_retries": 2,
            "current_step": "transcription",
        }
        result = routing_node(state)

        assert result["next_step"] == "retry"
        assert result["workflow_status"] == "retrying"
        assert "error_history" in result
        assert len(result["error_history"]) == 1
        assert result["error_history"][0]["error"] == "Temporary failure"

    def test_fallback_when_max_retries_exceeded(self):
        """Should route to fallback when max retries exceeded."""
        state = {
            "error": "Persistent failure",
            "error_count": 2,
            "max_retries": 2,
        }
        result = routing_node(state)

        assert result["workflow_status"] == "failed"
        assert result["next_step"] == "fallback"
        assert result["current_step"] == "routing"

    def test_fallback_when_error_count_greater_than_max(self):
        """Should route to fallback when error_count > max_retries."""
        state = {
            "error": "Too many failures",
            "error_count": 5,
            "max_retries": 2,
        }
        result = routing_node(state)

        assert result["workflow_status"] == "failed"
        assert result["next_step"] == "fallback"

    def test_default_max_retries(self):
        """Should use default max_retries of 2 when not specified."""
        state = {
            "error": "Failure",
            "error_count": 1,
            # max_retries not specified
        }
        result = routing_node(state)

        # Should retry because error_count (1) < default max_retries (2)
        assert result["next_step"] == "retry"

    def test_error_history_includes_all_details(self):
        """Error history entry should include all relevant details."""
        state = {
            "error": "Test error",
            "error_type": "TestError",
            "error_count": 0,
            "max_retries": 2,
            "current_step": "summarization",
        }
        result = routing_node(state)

        error_entry = result["error_history"][0]
        assert error_entry["step"] == "summarization"
        assert error_entry["error"] == "Test error"
        assert error_entry["error_type"] == "TestError"
        assert error_entry["retry_count"] == 0
        assert "timestamp" in error_entry


class TestErrorHandlerNode:
    """Tests for error_handler_node function."""

    def test_generates_user_friendly_message(self):
        """Should convert error type to user-friendly message."""
        state = {
            "error": "File not found: /path/to/file",
            "error_type": "FileNotFoundError",
        }
        result = error_handler_node(state)

        assert result["workflow_status"] == "failed"
        assert "Please try uploading again" in result["error"]
        assert result["current_step"] == "error_handler"

    def test_tracks_partial_results(self, sample_transcript, sample_call_summary):
        """Should identify which partial results are available."""
        state = {
            "error": "Scoring failed",
            "error_type": "ScoringError",
            "transcript": sample_transcript,
            "summary": sample_call_summary,
            "quality_scores": None,
        }
        result = error_handler_node(state)

        assert result["partial_results"]["transcript_available"] is True
        assert result["partial_results"]["summary_available"] is True
        assert result["partial_results"]["scores_available"] is False

    def test_no_partial_results(self):
        """Should show no partial results when none exist."""
        state = {
            "error": "Early failure",
            "error_type": "MissingInputError",
        }
        result = error_handler_node(state)

        assert result["partial_results"]["transcript_available"] is False
        assert result["partial_results"]["summary_available"] is False
        assert result["partial_results"]["scores_available"] is False

    def test_includes_completed_at(self):
        """Should include completion timestamp."""
        state = {
            "error": "Any error",
            "error_type": "AnyError",
        }
        result = error_handler_node(state)

        assert "completed_at" in result
        assert isinstance(result["completed_at"], datetime)

    def test_unknown_error_type(self):
        """Should handle unknown error types gracefully."""
        state = {
            "error": "Something unexpected happened",
            "error_type": "UnexpectedError",
        }
        result = error_handler_node(state)

        assert "An error occurred" in result["error"]
        assert "Something unexpected happened" in result["error"]


class TestCalculateProcessingTime:
    """Tests for _calculate_processing_time helper."""

    def test_calculates_time_from_datetime(self):
        """Should calculate time difference from datetime."""
        started = datetime.now()
        state = {"started_at": started}

        # Processing time should be very small (milliseconds)
        result = _calculate_processing_time(state)
        assert result >= 0.0
        assert result < 1.0  # Should be less than a second

    def test_returns_zero_when_no_start_time(self):
        """Should return 0.0 when started_at is not present."""
        state = {}
        result = _calculate_processing_time(state)
        assert result == 0.0

    def test_returns_zero_for_none_start_time(self):
        """Should return 0.0 when started_at is None."""
        state = {"started_at": None}
        result = _calculate_processing_time(state)
        assert result == 0.0


class TestGetUserFriendlyError:
    """Tests for _get_user_friendly_error helper."""

    @pytest.mark.parametrize(
        "error_type,expected_phrase",
        [
            ("FileNotFoundError", "could not be found"),
            ("FileTooLargeError", "too large"),
            ("UnsupportedFormatError", "not supported"),
            ("TranscriptionError", "Could not transcribe"),
            ("SummarizationError", "Could not generate summary"),
            ("ScoringError", "Could not complete quality scoring"),
            ("MissingInputError", "Required input was not provided"),
            ("MissingTranscriptError", "Transcript is required"),
            ("MissingScoringInputError", "Cannot score without a transcript"),
        ],
    )
    def test_known_error_types(self, error_type, expected_phrase):
        """Should return appropriate message for known error types."""
        result = _get_user_friendly_error(error_type, "Original error")
        assert expected_phrase in result

    def test_content_validation_error_passes_through(self):
        """ContentValidationError should pass through the detailed reason."""
        detailed_reason = "This does not appear to be a call center conversation"
        result = _get_user_friendly_error("ContentValidationError", detailed_reason)
        assert result == detailed_reason

    def test_unknown_error_type_includes_original(self):
        """Unknown error types should include the original error message."""
        result = _get_user_friendly_error("CustomError", "Custom error details")
        assert "An error occurred" in result
        assert "Custom error details" in result
