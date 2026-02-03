"""
Tests for agents/scoring_agent.py - Quality scoring.
"""

import pytest
from unittest.mock import patch, MagicMock

from agents.scoring_agent import scoring_node


class TestScoringNode:
    """Tests for scoring_node function."""

    def test_propagates_failed_workflow_status(self):
        """Should propagate error when workflow already failed."""
        state = {
            "workflow_status": "failed",
            "error": "Previous step failed",
            "error_type": "SummarizationError",
        }
        result = scoring_node(state)

        assert result["current_step"] == "scoring"
        assert result["error"] == "Previous step failed"
        assert result["error_type"] == "SummarizationError"
        assert result["workflow_status"] == "failed"

    def test_propagates_existing_error(self):
        """Should propagate existing error from state."""
        state = {
            "error": "Some upstream error",
            "error_type": "UpstreamError",
        }
        result = scoring_node(state)

        assert result["current_step"] == "scoring"
        assert result["error"] == "Some upstream error"
        assert result["workflow_status"] == "failed"

    def test_error_when_no_transcript(self):
        """Should return error when no transcript is available."""
        state = {
            "transcript": None,
            "summary": None,
            "error_count": 0,
        }
        result = scoring_node(state)

        assert "No transcript available for scoring" in result["error"]
        assert result["error_type"] == "MissingScoringInputError"
        assert result["error_count"] == 1
        assert result["current_step"] == "scoring"

    def test_error_when_transcript_missing(self):
        """Should return error when transcript key is missing."""
        state = {"error_count": 0}
        result = scoring_node(state)

        assert "No transcript available for scoring" in result["error"]
        assert result["error_type"] == "MissingScoringInputError"

    @patch("agents.scoring_agent.OpenAIService")
    @patch("agents.scoring_agent.calculate_overall_grade")
    def test_successful_scoring(
        self,
        mock_calculate_grade,
        mock_openai_class,
        sample_transcript,
        sample_call_summary,
        sample_quality_scores,
    ):
        """Should generate scores successfully."""
        # Setup mocks
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate_structured.return_value = sample_quality_scores
        mock_calculate_grade.return_value = "B"

        state = {
            "transcript": sample_transcript,
            "summary": sample_call_summary,
            "error_count": 0,
        }
        result = scoring_node(state)

        assert result["quality_scores"] == sample_quality_scores
        assert result["overall_grade"] == "B"
        assert result["recommendations"] == sample_quality_scores.areas_for_improvement
        assert result["current_step"] == "scoring"
        assert result["error"] is None

    @patch("agents.scoring_agent.OpenAIService")
    @patch("agents.scoring_agent.calculate_overall_grade")
    def test_scoring_without_summary(
        self, mock_calculate_grade, mock_openai_class, sample_transcript, sample_quality_scores
    ):
        """Should work even when summary is not available."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate_structured.return_value = sample_quality_scores
        mock_calculate_grade.return_value = "B"

        state = {
            "transcript": sample_transcript,
            "summary": None,  # No summary
            "error_count": 0,
        }
        result = scoring_node(state)

        # Should still succeed
        assert result["quality_scores"] == sample_quality_scores
        assert result["error"] is None

    @patch("agents.scoring_agent.OpenAIService")
    def test_handles_api_exception(self, mock_openai_class, sample_transcript):
        """Should handle API exceptions gracefully."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate_structured.side_effect = Exception("API error")

        state = {
            "transcript": sample_transcript,
            "summary": None,
            "error_count": 0,
        }
        result = scoring_node(state)

        assert "Scoring failed" in result["error"]
        assert result["error_type"] == "ScoringError"
        assert result["error_count"] == 1
        assert result["current_step"] == "scoring"

    @patch("agents.scoring_agent.OpenAIService")
    def test_increments_error_count(self, mock_openai_class, sample_transcript):
        """Should increment existing error count."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate_structured.side_effect = Exception("API error")

        state = {
            "transcript": sample_transcript,
            "summary": None,
            "error_count": 2,
        }
        result = scoring_node(state)

        assert result["error_count"] == 3

    def test_default_error_message_for_workflow_failure(self):
        """Should use default error message when not specified."""
        state = {
            "workflow_status": "failed",
            # error not specified
        }
        result = scoring_node(state)

        assert result["error"] == "Previous step failed"

    def test_default_error_type_for_workflow_failure(self):
        """Should use default error type when not specified."""
        state = {
            "workflow_status": "failed",
            # error_type not specified
        }
        result = scoring_node(state)

        assert result["error_type"] == "PreviousStepError"

    @patch("agents.scoring_agent.OpenAIService")
    @patch("agents.scoring_agent.calculate_overall_grade")
    def test_uses_summary_brief_summary(
        self,
        mock_calculate_grade,
        mock_openai_class,
        sample_transcript,
        sample_call_summary,
        sample_quality_scores,
    ):
        """Should use brief_summary from CallSummary object."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate_structured.return_value = sample_quality_scores
        mock_calculate_grade.return_value = "B"

        state = {
            "transcript": sample_transcript,
            "summary": sample_call_summary,
        }
        scoring_node(state)

        # Verify the prompt includes the summary
        call_args = mock_service.generate_structured.call_args
        prompt = call_args.kwargs.get("prompt") or call_args[1].get("prompt")
        assert sample_call_summary.brief_summary in prompt

    @patch("agents.scoring_agent.OpenAIService")
    @patch("agents.scoring_agent.calculate_overall_grade")
    def test_grade_verification(
        self,
        mock_calculate_grade,
        mock_openai_class,
        sample_transcript,
        sample_quality_scores,
    ):
        """Should verify grade calculation using utility function."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate_structured.return_value = sample_quality_scores
        mock_calculate_grade.return_value = "A"

        state = {
            "transcript": sample_transcript,
            "summary": None,
        }
        result = scoring_node(state)

        # Verify calculate_overall_grade was called with the percentage
        mock_calculate_grade.assert_called_once_with(sample_quality_scores.percentage_score)
        assert result["overall_grade"] == "A"
