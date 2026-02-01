import logging
from typing import Any

from services.openai_service import OpenAIService
from schemas.output_schemas import QualityScores
from utils.scoring_utils import calculate_overall_grade

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are an expert call center quality assurance evaluator with years
of experience in assessing customer service interactions. You provide fair, detailed,
and constructive evaluations based on industry best practices."""

SCORING_PROMPT = """Evaluate this call center transcript using a comprehensive quality rubric.

Transcript:
{transcript}

Call Summary:
{summary}

Score each criterion from 1-5:
- 5 (Excellent): Exceeds expectations, exemplary performance
- 4 (Good): Meets all expectations with minor areas for polish
- 3 (Satisfactory): Meets basic expectations, room for improvement
- 2 (Needs Improvement): Below expectations, significant gaps
- 1 (Poor): Fails to meet minimum standards

For each score, you MUST provide:
1. The numeric score (1-5)
2. The level (excellent, good, satisfactory, needs_improvement, poor)
3. Specific evidence from the transcript supporting your score (quote or observation)
4. Constructive feedback for improvement

Evaluate ALL of these categories:

GREETING & OPENING:
- proper_greeting: Did the agent use appropriate company greeting and introduce themselves?
- verified_customer: Did the agent properly verify customer identity?
- set_expectations: Did the agent explain what they can help with?

COMMUNICATION SKILLS:
- clarity: Did the agent speak clearly with appropriate pace?
- tone: Was the tone professional and friendly throughout?
- active_listening: Did the agent acknowledge the customer and ask clarifying questions?
- empathy: Did the agent show understanding of customer feelings?
- avoided_jargon: Did the agent use customer-friendly language?

PROBLEM RESOLUTION:
- understanding: Did the agent correctly identify the customer's issue?
- knowledge: Did the agent demonstrate product/service knowledge?
- solution_quality: Was the solution appropriate and effective?
- first_call_resolution: Was the issue resolved without need for callback?
- proactive_help: Did the agent offer additional assistance?

PROFESSIONALISM:
- courtesy: Did the agent maintain a polite demeanor?
- patience: Did the agent remain patient with difficult situations?
- ownership: Did the agent take responsibility and avoid blame?
- confidentiality: Was sensitive information handled appropriately?

CALL CLOSING:
- summarized: Did the agent recap what was discussed/resolved?
- next_steps: Did the agent clearly explain any follow-up needed?
- satisfaction_check: Did the agent ask if the customer needs anything else?
- proper_closing: Did the agent use an appropriate closing statement?

After scoring all items:
- Calculate total_points (sum of all 19 scores)
- Calculate percentage_score (total_points / 95 * 100)
- Determine overall_grade: A (90%+), B (80-89%), C (70-79%), D (60-69%), F (<60%)
- List top 3 strengths
- List top 3 areas_for_improvement
- Note any compliance_issues (empty list if none)
- Set escalation_recommended to true if score is below 50% or serious issues found
"""


def scoring_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluates call quality using structured rubric.

    This agent:
    1. Takes transcript and summary from state
    2. Uses GPT with structured output to evaluate against 19-item rubric
    3. Calculates overall scores and determines letter grade
    4. Identifies strengths and areas for improvement

    Returns:
        dict with quality scores and recommendations
    """
    logger.info("=== SCORING AGENT START ===")
    logger.info(f"Current state: workflow_status={state.get('workflow_status')}, error={state.get('error')}")

    try:
        # Check if workflow has already failed
        if state.get("workflow_status") == "failed" or state.get("error"):
            logger.info("Workflow already failed, propagating error")
            return {
                "current_step": "scoring",
                "error": state.get("error", "Previous step failed"),
                "error_type": state.get("error_type", "PreviousStepError"),
                "workflow_status": "failed",
            }

        transcript = state.get("transcript")
        summary = state.get("summary")
        logger.info(f"Transcript present: {transcript is not None}, Summary present: {summary is not None}")

        if not transcript:
            logger.error("No transcript available for scoring")
            return {
                "error": "No transcript available for scoring",
                "error_type": "MissingScoringInputError",
                "error_count": state.get("error_count", 0) + 1,
                "current_step": "scoring",
            }

        openai_service = OpenAIService()

        # Format summary for prompt
        summary_text = summary.brief_summary if summary else "Not available"

        # Generate structured quality scores
        quality_scores = openai_service.generate_structured(
            prompt=SCORING_PROMPT.format(
                transcript=transcript,
                summary=summary_text,
            ),
            response_model=QualityScores,
            system_prompt=SYSTEM_PROMPT,
        )

        # Verify grade calculation
        overall_grade = calculate_overall_grade(quality_scores.percentage_score)

        logger.info(f"=== SCORING AGENT COMPLETE === Grade: {overall_grade}")
        return {
            "quality_scores": quality_scores,
            "overall_grade": overall_grade,
            "recommendations": quality_scores.areas_for_improvement,
            "current_step": "scoring",
            "error": None,
        }

    except Exception as e:
        return {
            "error": f"Scoring failed: {str(e)}",
            "error_type": "ScoringError",
            "error_count": state.get("error_count", 0) + 1,
            "current_step": "scoring",
        }
