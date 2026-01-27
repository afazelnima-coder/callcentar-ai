from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class ScoreLevel(str, Enum):
    """Standard 5-point scoring scale."""

    EXCELLENT = "excellent"  # 5 points
    GOOD = "good"  # 4 points
    SATISFACTORY = "satisfactory"  # 3 points
    NEEDS_IMPROVEMENT = "needs_improvement"  # 2 points
    POOR = "poor"  # 1 point


class RubricScore(BaseModel):
    """Individual rubric item score."""

    score: int = Field(ge=1, le=5, description="Score from 1-5")
    level: ScoreLevel
    evidence: str = Field(description="Specific quote or observation supporting score")
    feedback: str = Field(description="Constructive feedback for improvement")


class GreetingAndOpening(BaseModel):
    """Evaluates how the agent starts the call."""

    proper_greeting: RubricScore = Field(
        description="Used company greeting, introduced self"
    )
    verified_customer: RubricScore = Field(
        description="Properly verified customer identity"
    )
    set_expectations: RubricScore = Field(
        description="Explained what they can help with"
    )


class CommunicationSkills(BaseModel):
    """Evaluates verbal communication quality."""

    clarity: RubricScore = Field(description="Spoke clearly, appropriate pace")
    tone: RubricScore = Field(description="Professional, friendly tone throughout")
    active_listening: RubricScore = Field(
        description="Acknowledged customer, asked clarifying questions"
    )
    empathy: RubricScore = Field(description="Showed understanding of customer feelings")
    avoided_jargon: RubricScore = Field(description="Used customer-friendly language")


class ProblemResolution(BaseModel):
    """Evaluates how well the issue was addressed."""

    understanding: RubricScore = Field(description="Correctly identified customer issue")
    knowledge: RubricScore = Field(description="Demonstrated product/service knowledge")
    solution_quality: RubricScore = Field(description="Provided appropriate solution")
    first_call_resolution: RubricScore = Field(
        description="Resolved without need for callback"
    )
    proactive_help: RubricScore = Field(description="Offered additional assistance")


class Professionalism(BaseModel):
    """Evaluates professional conduct."""

    courtesy: RubricScore = Field(description="Maintained polite demeanor")
    patience: RubricScore = Field(description="Remained patient with difficult situations")
    ownership: RubricScore = Field(description="Took responsibility, avoided blame")
    confidentiality: RubricScore = Field(
        description="Handled sensitive info appropriately"
    )


class CallClosing(BaseModel):
    """Evaluates how the agent ended the call."""

    summarized: RubricScore = Field(description="Recapped what was discussed/resolved")
    next_steps: RubricScore = Field(description="Clearly explained any follow-up needed")
    satisfaction_check: RubricScore = Field(
        description="Asked if customer needs anything else"
    )
    proper_closing: RubricScore = Field(description="Used appropriate closing statement")


class QualityScores(BaseModel):
    """Complete quality assessment for a call."""

    # Category scores
    greeting: GreetingAndOpening
    communication: CommunicationSkills
    resolution: ProblemResolution
    professionalism: Professionalism
    closing: CallClosing

    # Aggregate scores
    total_points: int = Field(description="Sum of all individual scores")
    max_possible_points: int = Field(
        default=95, description="Maximum possible score (19 items x 5)"
    )
    percentage_score: float = Field(description="Percentage score (total/max * 100)")

    # Overall assessment
    overall_grade: str = Field(
        description="Letter grade: A (90+), B (80-89), C (70-79), D (60-69), F (<60)"
    )
    strengths: List[str] = Field(description="Top 3 areas of strength")
    areas_for_improvement: List[str] = Field(
        description="Top 3 areas needing improvement"
    )

    # Compliance flags
    compliance_issues: List[str] = Field(
        default_factory=list, description="Any compliance violations noted"
    )
    escalation_recommended: bool = Field(
        default=False, description="Whether call should be escalated for review"
    )


class CallSummary(BaseModel):
    """Structured call summary."""

    brief_summary: str = Field(max_length=500, description="2-3 sentence overview")
    customer_issue: str = Field(description="Primary reason for call")
    resolution_provided: str = Field(description="How the issue was addressed")
    customer_sentiment: str = Field(
        description="Overall customer mood: positive, neutral, negative, mixed"
    )
    call_category: str = Field(
        description="Type: support, complaint, inquiry, sales, etc."
    )
    key_topics: List[str] = Field(description="Main topics discussed")
    action_items: List[str] = Field(
        default_factory=list, description="Follow-up actions needed"
    )
