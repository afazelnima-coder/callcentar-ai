"""
Tests for schemas/output_schemas.py - Pydantic output models.
"""

import pytest
from pydantic import ValidationError

from schemas.output_schemas import (
    ScoreLevel,
    RubricScore,
    GreetingAndOpening,
    CommunicationSkills,
    ProblemResolution,
    Professionalism,
    CallClosing,
    QualityScores,
    CallSummary,
)


class TestScoreLevel:
    """Tests for ScoreLevel enum."""

    def test_all_levels_exist(self):
        """All score levels should be defined."""
        assert ScoreLevel.EXCELLENT == "excellent"
        assert ScoreLevel.GOOD == "good"
        assert ScoreLevel.SATISFACTORY == "satisfactory"
        assert ScoreLevel.NEEDS_IMPROVEMENT == "needs_improvement"
        assert ScoreLevel.POOR == "poor"

    def test_score_level_is_string_enum(self):
        """ScoreLevel should be a string enum."""
        assert isinstance(ScoreLevel.EXCELLENT.value, str)
        assert ScoreLevel.GOOD.value == "good"


class TestRubricScore:
    """Tests for RubricScore model."""

    def test_valid_score_creation(self):
        """Should create a valid RubricScore."""
        score = RubricScore(
            score=4,
            level=ScoreLevel.GOOD,
            evidence="Agent introduced themselves",
            feedback="Consider being more specific",
        )
        assert score.score == 4
        assert score.level == ScoreLevel.GOOD
        assert score.evidence == "Agent introduced themselves"
        assert score.feedback == "Consider being more specific"

    def test_minimum_score(self):
        """Score should accept minimum value of 1."""
        score = RubricScore(
            score=1,
            level=ScoreLevel.POOR,
            evidence="Did not meet standards",
            feedback="Needs improvement",
        )
        assert score.score == 1

    def test_maximum_score(self):
        """Score should accept maximum value of 5."""
        score = RubricScore(
            score=5,
            level=ScoreLevel.EXCELLENT,
            evidence="Exceeded all expectations",
            feedback="Keep it up",
        )
        assert score.score == 5

    def test_score_below_minimum_fails(self):
        """Score below 1 should fail validation."""
        with pytest.raises(ValidationError):
            RubricScore(
                score=0,
                level=ScoreLevel.POOR,
                evidence="Test",
                feedback="Test",
            )

    def test_score_above_maximum_fails(self):
        """Score above 5 should fail validation."""
        with pytest.raises(ValidationError):
            RubricScore(
                score=6,
                level=ScoreLevel.EXCELLENT,
                evidence="Test",
                feedback="Test",
            )

    def test_missing_required_fields_fails(self):
        """Missing required fields should fail validation."""
        with pytest.raises(ValidationError):
            RubricScore(score=4, level=ScoreLevel.GOOD)


class TestGreetingAndOpening:
    """Tests for GreetingAndOpening model."""

    def test_valid_creation(self, sample_rubric_score):
        """Should create a valid GreetingAndOpening."""
        greeting = GreetingAndOpening(
            proper_greeting=sample_rubric_score,
            verified_customer=sample_rubric_score,
            set_expectations=sample_rubric_score,
        )
        assert greeting.proper_greeting == sample_rubric_score
        assert greeting.verified_customer == sample_rubric_score
        assert greeting.set_expectations == sample_rubric_score

    def test_missing_field_fails(self, sample_rubric_score):
        """Missing required fields should fail validation."""
        with pytest.raises(ValidationError):
            GreetingAndOpening(
                proper_greeting=sample_rubric_score,
                # Missing verified_customer and set_expectations
            )


class TestCommunicationSkills:
    """Tests for CommunicationSkills model."""

    def test_valid_creation(self, sample_rubric_score):
        """Should create a valid CommunicationSkills."""
        comm = CommunicationSkills(
            clarity=sample_rubric_score,
            tone=sample_rubric_score,
            active_listening=sample_rubric_score,
            empathy=sample_rubric_score,
            avoided_jargon=sample_rubric_score,
        )
        assert comm.clarity == sample_rubric_score
        assert comm.tone == sample_rubric_score
        assert comm.active_listening == sample_rubric_score
        assert comm.empathy == sample_rubric_score
        assert comm.avoided_jargon == sample_rubric_score


class TestProblemResolution:
    """Tests for ProblemResolution model."""

    def test_valid_creation(self, sample_rubric_score):
        """Should create a valid ProblemResolution."""
        resolution = ProblemResolution(
            understanding=sample_rubric_score,
            knowledge=sample_rubric_score,
            solution_quality=sample_rubric_score,
            first_call_resolution=sample_rubric_score,
            proactive_help=sample_rubric_score,
        )
        assert resolution.understanding == sample_rubric_score
        assert resolution.first_call_resolution == sample_rubric_score


class TestProfessionalism:
    """Tests for Professionalism model."""

    def test_valid_creation(self, sample_rubric_score):
        """Should create a valid Professionalism."""
        prof = Professionalism(
            courtesy=sample_rubric_score,
            patience=sample_rubric_score,
            ownership=sample_rubric_score,
            confidentiality=sample_rubric_score,
        )
        assert prof.courtesy == sample_rubric_score
        assert prof.confidentiality == sample_rubric_score


class TestCallClosing:
    """Tests for CallClosing model."""

    def test_valid_creation(self, sample_rubric_score):
        """Should create a valid CallClosing."""
        closing = CallClosing(
            summarized=sample_rubric_score,
            next_steps=sample_rubric_score,
            satisfaction_check=sample_rubric_score,
            proper_closing=sample_rubric_score,
        )
        assert closing.summarized == sample_rubric_score
        assert closing.proper_closing == sample_rubric_score


class TestQualityScores:
    """Tests for QualityScores model."""

    def test_valid_creation(self, sample_quality_scores):
        """Should have all required fields."""
        assert sample_quality_scores.total_points == 85
        assert sample_quality_scores.max_possible_points == 95
        assert sample_quality_scores.percentage_score == 89.47
        assert sample_quality_scores.overall_grade == "B"
        assert len(sample_quality_scores.strengths) == 3
        assert len(sample_quality_scores.areas_for_improvement) == 3

    def test_default_max_points(self, sample_rubric_score):
        """max_possible_points should default to 95."""
        scores = QualityScores(
            greeting=GreetingAndOpening(
                proper_greeting=sample_rubric_score,
                verified_customer=sample_rubric_score,
                set_expectations=sample_rubric_score,
            ),
            communication=CommunicationSkills(
                clarity=sample_rubric_score,
                tone=sample_rubric_score,
                active_listening=sample_rubric_score,
                empathy=sample_rubric_score,
                avoided_jargon=sample_rubric_score,
            ),
            resolution=ProblemResolution(
                understanding=sample_rubric_score,
                knowledge=sample_rubric_score,
                solution_quality=sample_rubric_score,
                first_call_resolution=sample_rubric_score,
                proactive_help=sample_rubric_score,
            ),
            professionalism=Professionalism(
                courtesy=sample_rubric_score,
                patience=sample_rubric_score,
                ownership=sample_rubric_score,
                confidentiality=sample_rubric_score,
            ),
            closing=CallClosing(
                summarized=sample_rubric_score,
                next_steps=sample_rubric_score,
                satisfaction_check=sample_rubric_score,
                proper_closing=sample_rubric_score,
            ),
            total_points=76,
            percentage_score=80.0,
            overall_grade="B",
            strengths=["Good tone", "Clear communication"],
            areas_for_improvement=["Closing skills"],
        )
        assert scores.max_possible_points == 95

    def test_default_empty_compliance_issues(self, sample_quality_scores):
        """compliance_issues should default to empty list."""
        # sample_quality_scores doesn't specify compliance_issues
        assert sample_quality_scores.compliance_issues == []

    def test_default_escalation_recommended_false(self, sample_quality_scores):
        """escalation_recommended should default to False."""
        assert sample_quality_scores.escalation_recommended is False


class TestCallSummary:
    """Tests for CallSummary model."""

    def test_valid_creation(self, sample_call_summary):
        """Should create a valid CallSummary."""
        assert "internet connectivity" in sample_call_summary.brief_summary.lower()
        assert sample_call_summary.customer_sentiment == "positive"
        assert sample_call_summary.call_category == "support"
        assert len(sample_call_summary.key_topics) > 0

    def test_brief_summary_max_length(self):
        """brief_summary should respect max_length of 500."""
        long_text = "x" * 501
        with pytest.raises(ValidationError):
            CallSummary(
                brief_summary=long_text,
                customer_issue="Test issue",
                resolution_provided="Test resolution",
                customer_sentiment="neutral",
                call_category="support",
                key_topics=["test"],
            )

    def test_default_empty_action_items(self):
        """action_items should default to empty list."""
        summary = CallSummary(
            brief_summary="Test summary",
            customer_issue="Test issue",
            resolution_provided="Test resolution",
            customer_sentiment="neutral",
            call_category="support",
            key_topics=["test"],
            # action_items not specified
        )
        assert summary.action_items == []

    def test_missing_required_fields_fails(self):
        """Missing required fields should fail validation."""
        with pytest.raises(ValidationError):
            CallSummary(
                brief_summary="Test summary",
                # Missing other required fields
            )
