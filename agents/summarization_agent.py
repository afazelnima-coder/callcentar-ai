import logging
from typing import Any

from services.openai_service import OpenAIService
from schemas.output_schemas import CallSummary

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a call center quality assurance analyst. Your job is to
analyze call transcripts and provide structured summaries that capture the key
information from customer service interactions."""

SUMMARIZATION_PROMPT = """Analyze this call center transcript and provide a structured summary.

Transcript:
{transcript}

Provide your analysis with:
- A brief summary (2-3 sentences overview)
- The customer's primary issue or reason for calling
- How the issue was addressed/resolved
- The customer's overall sentiment (positive, neutral, negative, or mixed)
- The call category (support, complaint, inquiry, sales, etc.)
- Key topics discussed (as a list)
- Any action items or follow-up needed (as a list, can be empty)
"""


def summarization_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Generates structured call summary using GPT.

    This agent:
    1. Takes the transcript from state
    2. Uses GPT with structured output to generate a CallSummary
    3. Extracts key points, customer intent, and resolution status

    Returns:
        dict with summary and related analysis
    """
    logger.info("=== SUMMARIZATION AGENT START ===")
    logger.info(f"Current state: workflow_status={state.get('workflow_status')}, error={state.get('error')}")

    try:
        # Check if workflow has already failed (e.g., content validation)
        if state.get("workflow_status") == "failed":
            logger.info("Workflow already failed, propagating error")
            return {
                "current_step": "summarization",
                "error": state.get("error", "Previous step failed"),
                "error_type": state.get("error_type", "PreviousStepError"),
                "workflow_status": "failed",
            }

        # Check if there's an existing error from intake validation
        if state.get("error"):
            logger.info(f"Found existing error: {state.get('error')}")
            return {
                "current_step": "summarization",
                "error": state.get("error"),
                "error_type": state.get("error_type", "ValidationError"),
                "workflow_status": "failed",
            }

        transcript = state.get("transcript")
        logger.info(f"Transcript present: {transcript is not None}, length: {len(transcript) if transcript else 0}")

        if not transcript:
            return {
                "error": "No transcript available for summarization",
                "error_type": "MissingTranscriptError",
                "error_count": state.get("error_count", 0) + 1,
                "current_step": "summarization",
            }

        openai_service = OpenAIService()

        # Use structured output for consistent results
        summary = openai_service.generate_structured(
            prompt=SUMMARIZATION_PROMPT.format(transcript=transcript),
            response_model=CallSummary,
            system_prompt=SYSTEM_PROMPT,
        )

        # Determine resolution status from summary
        resolution_lower = summary.resolution_provided.lower()
        if any(word in resolution_lower for word in ["resolved", "fixed", "completed", "done"]):
            resolution_status = "resolved"
        elif any(word in resolution_lower for word in ["escalated", "transferred", "supervisor"]):
            resolution_status = "escalated"
        else:
            resolution_status = "pending"

        logger.info("=== SUMMARIZATION AGENT COMPLETE ===")
        return {
            "summary": summary,
            "key_points": summary.key_topics,
            "customer_intent": summary.customer_issue,
            "resolution_status": resolution_status,
            "current_step": "summarization",
            "error": None,
        }

    except Exception as e:
        logger.error(f"Summarization error: {type(e).__name__}: {str(e)}")
        return {
            "error": f"Summarization failed: {str(e)}",
            "error_type": "SummarizationError",
            "error_count": state.get("error_count", 0) + 1,
            "current_step": "summarization",
        }
