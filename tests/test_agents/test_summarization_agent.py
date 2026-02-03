"""
Tests for agents/summarization_agent.py - Call summarization.
"""

import pytest
from unittest.mock import patch, MagicMock

from agents.summarization_agent import summarization_node


class TestSummarizationNode:
    """Tests for summarization_node function."""

    def test_propagates_failed_workflow_status(self):
        """Should propagate error when workflow already failed."""
        state = {
            "workflow_status": "failed",
            "error": "Previous step failed",
            "error_type": "ContentValidationError",
        }
        result = summarization_node(state)

        assert result["current_step"] == "summarization"
        assert result["error"] == "Previous step failed"
        assert result["error_type"] == "ContentValidationError"
        assert result["workflow_status"] == "failed"

    def test_propagates_existing_error(self):
        """Should propagate existing error from state."""
        state = {
            "error": "Intake validation failed",
            "error_type": "ValidationError",
        }
        result = summarization_node(state)

        assert result["current_step"] == "summarization"
        assert result["error"] == "Intake validation failed"
        assert result["workflow_status"] == "failed"

    def test_error_when_no_transcript(self):
        """Should return error when no transcript is available."""
        state = {
            "transcript": None,
            "error_count": 0,
        }
        result = summarization_node(state)

        assert "No transcript available" in result["error"]
        assert result["error_type"] == "MissingTranscriptError"
        assert result["error_count"] == 1
        assert result["current_step"] == "summarization"

    def test_error_when_transcript_missing(self):
        """Should return error when transcript key is missing."""
        state = {"error_count": 0}
        result = summarization_node(state)

        assert "No transcript available" in result["error"]
        assert result["error_type"] == "MissingTranscriptError"

    @patch("agents.summarization_agent.OpenAIService")
    def test_successful_summarization(
        self, mock_openai_class, sample_transcript, sample_call_summary
    ):
        """Should generate summary successfully."""
        # Setup mock
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate_structured.return_value = sample_call_summary

        state = {
            "transcript": sample_transcript,
            "error_count": 0,
        }
        result = summarization_node(state)

        assert result["summary"] == sample_call_summary
        assert result["key_points"] == sample_call_summary.key_topics
        assert result["customer_intent"] == sample_call_summary.customer_issue
        assert result["current_step"] == "summarization"
        assert result["error"] is None

    @patch("agents.summarization_agent.OpenAIService")
    def test_resolution_status_resolved(self, mock_openai_class, sample_transcript):
        """Should detect resolved status from resolution text."""
        from schemas.output_schemas import CallSummary

        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service

        summary = CallSummary(
            brief_summary="Test summary",
            customer_issue="Test issue",
            resolution_provided="Issue was resolved successfully",
            customer_sentiment="positive",
            call_category="support",
            key_topics=["test"],
            action_items=[],
        )
        mock_service.generate_structured.return_value = summary

        state = {"transcript": sample_transcript}
        result = summarization_node(state)

        assert result["resolution_status"] == "resolved"

    @patch("agents.summarization_agent.OpenAIService")
    def test_resolution_status_escalated(self, mock_openai_class, sample_transcript):
        """Should detect escalated status from resolution text."""
        from schemas.output_schemas import CallSummary

        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service

        summary = CallSummary(
            brief_summary="Test summary",
            customer_issue="Complex issue",
            resolution_provided="Issue was escalated to supervisor",
            customer_sentiment="neutral",
            call_category="support",
            key_topics=["test"],
            action_items=["Supervisor callback"],
        )
        mock_service.generate_structured.return_value = summary

        state = {"transcript": sample_transcript}
        result = summarization_node(state)

        assert result["resolution_status"] == "escalated"

    @patch("agents.summarization_agent.OpenAIService")
    def test_resolution_status_pending(self, mock_openai_class, sample_transcript):
        """Should default to pending status when not resolved or escalated."""
        from schemas.output_schemas import CallSummary

        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service

        summary = CallSummary(
            brief_summary="Test summary",
            customer_issue="Ongoing issue",
            resolution_provided="Agent provided information, customer will call back",
            customer_sentiment="neutral",
            call_category="inquiry",
            key_topics=["test"],
            action_items=["Customer callback"],
        )
        mock_service.generate_structured.return_value = summary

        state = {"transcript": sample_transcript}
        result = summarization_node(state)

        assert result["resolution_status"] == "pending"

    @patch("agents.summarization_agent.OpenAIService")
    def test_handles_api_exception(self, mock_openai_class, sample_transcript):
        """Should handle API exceptions gracefully."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate_structured.side_effect = Exception("API error")

        state = {
            "transcript": sample_transcript,
            "error_count": 0,
        }
        result = summarization_node(state)

        assert "Summarization failed" in result["error"]
        assert result["error_type"] == "SummarizationError"
        assert result["error_count"] == 1
        assert result["current_step"] == "summarization"

    @patch("agents.summarization_agent.OpenAIService")
    def test_increments_error_count(self, mock_openai_class, sample_transcript):
        """Should increment existing error count."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate_structured.side_effect = Exception("API error")

        state = {
            "transcript": sample_transcript,
            "error_count": 1,
        }
        result = summarization_node(state)

        assert result["error_count"] == 2

    def test_default_error_type_for_existing_error(self):
        """Should use default error type when not specified."""
        state = {
            "error": "Some validation error",
            # error_type not specified
        }
        result = summarization_node(state)

        assert result["error_type"] == "ValidationError"

    def test_default_error_type_for_failed_workflow(self):
        """Should use default error type for failed workflow status."""
        state = {
            "workflow_status": "failed",
            # error and error_type not specified
        }
        result = summarization_node(state)

        assert result["error"] == "Previous step failed"
        assert result["error_type"] == "PreviousStepError"
