"""
Tests for graph/edges.py - Conditional routing functions.
"""

import pytest
from graph.edges import (
    route_after_intake,
    route_after_transcription,
    route_after_summarization,
    route_after_scoring,
    route_after_routing,
)


class TestRouteAfterIntake:
    """Tests for route_after_intake function."""

    def test_routes_to_error_handler_on_error(self):
        """Should route to error_handler when error is present."""
        state = {"error": "Some error occurred"}
        assert route_after_intake(state) == "error_handler"

    def test_routes_to_transcription_for_audio(self):
        """Should route to transcription for audio files without transcript."""
        state = {"has_audio": True, "transcript": None}
        assert route_after_intake(state) == "transcription"

    def test_routes_to_summarization_for_text(self):
        """Should route to summarization when transcript exists."""
        state = {"has_audio": False, "transcript": "Some transcript"}
        assert route_after_intake(state) == "summarization"

    def test_routes_to_summarization_when_transcript_exists(self):
        """Should route to summarization even with audio if transcript exists."""
        state = {"has_audio": True, "transcript": "Already transcribed"}
        assert route_after_intake(state) == "summarization"

    def test_routes_to_summarization_when_no_audio(self):
        """Should route to summarization when no audio flag."""
        state = {"has_audio": False}
        assert route_after_intake(state) == "summarization"

    def test_error_takes_priority(self):
        """Error should take priority over other routing logic."""
        state = {"error": "Error", "has_audio": True, "transcript": None}
        assert route_after_intake(state) == "error_handler"


class TestRouteAfterTranscription:
    """Tests for route_after_transcription function."""

    def test_routes_to_error_handler_on_error(self):
        """Should route to error_handler when error is present."""
        state = {"error": "Transcription failed", "transcript": None}
        assert route_after_transcription(state) == "error_handler"

    def test_routes_to_error_handler_when_no_transcript(self):
        """Should route to error_handler when transcript is missing."""
        state = {"transcript": None}
        assert route_after_transcription(state) == "error_handler"

    def test_routes_to_error_handler_when_transcript_empty(self):
        """Should route to error_handler when transcript is empty."""
        state = {"transcript": ""}
        assert route_after_transcription(state) == "error_handler"

    def test_routes_to_summarization_on_success(self):
        """Should route to summarization when transcript exists."""
        state = {"transcript": "Valid transcript content"}
        assert route_after_transcription(state) == "summarization"

    def test_error_takes_priority_over_transcript(self):
        """Error should take priority even if transcript exists."""
        state = {"error": "Some error", "transcript": "Valid transcript"}
        assert route_after_transcription(state) == "error_handler"


class TestRouteAfterSummarization:
    """Tests for route_after_summarization function."""

    def test_routes_to_error_handler_on_error(self):
        """Should route to error_handler when error is present."""
        state = {"error": "Summarization failed"}
        assert route_after_summarization(state) == "error_handler"

    def test_routes_to_scoring_on_success(self):
        """Should route to scoring when no error."""
        state = {}
        assert route_after_summarization(state) == "scoring"

    def test_routes_to_scoring_with_summary(self):
        """Should route to scoring when summary exists."""
        state = {"summary": {"brief_summary": "Test summary"}}
        assert route_after_summarization(state) == "scoring"


class TestRouteAfterScoring:
    """Tests for route_after_scoring function."""

    def test_routes_to_error_handler_on_error(self):
        """Should route to error_handler when error is present."""
        state = {"error": "Scoring failed"}
        assert route_after_scoring(state) == "error_handler"

    def test_routes_to_routing_on_success(self):
        """Should route to routing when no error."""
        state = {}
        assert route_after_scoring(state) == "routing"

    def test_routes_to_routing_with_scores(self):
        """Should route to routing when scores exist."""
        state = {"quality_scores": {"total_points": 80}}
        assert route_after_scoring(state) == "routing"


class TestRouteAfterRouting:
    """Tests for route_after_routing function."""

    def test_routes_to_end_on_success(self):
        """Should route to __end__ when next_step is success."""
        state = {"next_step": "success"}
        assert route_after_routing(state) == "__end__"

    def test_routes_to_transcription_on_retry(self):
        """Should route to transcription when next_step is retry."""
        state = {"next_step": "retry"}
        assert route_after_routing(state) == "transcription"

    def test_routes_to_error_handler_on_fail(self):
        """Should route to error_handler when next_step is fail."""
        state = {"next_step": "fail"}
        assert route_after_routing(state) == "error_handler"

    def test_routes_to_error_handler_on_unknown(self):
        """Should route to error_handler for unknown next_step values."""
        state = {"next_step": "unknown_value"}
        assert route_after_routing(state) == "error_handler"

    def test_routes_to_error_handler_when_missing(self):
        """Should route to error_handler when next_step is missing."""
        state = {}
        assert route_after_routing(state) == "error_handler"

    def test_routes_to_error_handler_when_none(self):
        """Should route to error_handler when next_step is None."""
        state = {"next_step": None}
        assert route_after_routing(state) == "error_handler"
