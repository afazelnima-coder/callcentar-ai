import logging
from typing import Literal

from graph.state import CallCenterState

logger = logging.getLogger(__name__)


def route_after_intake(
    state: CallCenterState,
) -> Literal["transcription", "summarization", "error_handler"]:
    """Determine next step after intake based on input type."""
    logger.info(f"=== ROUTING AFTER INTAKE === error={state.get('error')}, has_audio={state.get('has_audio')}, transcript={state.get('transcript') is not None}")

    if state.get("error"):
        logger.info("Routing to: error_handler (error found)")
        return "error_handler"

    if state.get("has_audio") and not state.get("transcript"):
        logger.info("Routing to: transcription")
        return "transcription"

    logger.info("Routing to: summarization")
    return "summarization"


def route_after_transcription(
    state: CallCenterState,
) -> Literal["summarization", "error_handler"]:
    """Check if transcription succeeded before proceeding."""
    logger.info(f"=== ROUTING AFTER TRANSCRIPTION === error={state.get('error')}, transcript={state.get('transcript') is not None}")

    if state.get("error") or not state.get("transcript"):
        logger.info("Routing to: error_handler")
        return "error_handler"

    logger.info("Routing to: summarization")
    return "summarization"


def route_after_summarization(
    state: CallCenterState,
) -> Literal["scoring", "error_handler"]:
    """Check if summarization succeeded before proceeding."""
    logger.info(f"=== ROUTING AFTER SUMMARIZATION === error={state.get('error')}")

    if state.get("error"):
        logger.info("Routing to: error_handler")
        return "error_handler"

    logger.info("Routing to: scoring")
    return "scoring"


def route_after_scoring(
    state: CallCenterState,
) -> Literal["routing", "error_handler"]:
    """Check if scoring succeeded before proceeding."""
    logger.info(f"=== ROUTING AFTER SCORING === error={state.get('error')}")

    if state.get("error"):
        logger.info("Routing to: error_handler")
        return "error_handler"

    logger.info("Routing to: routing")
    return "routing"


def route_after_routing(
    state: CallCenterState,
) -> Literal["__end__", "transcription", "error_handler"]:
    """Determine outcome after routing agent analysis."""
    next_step = state.get("next_step")
    logger.info(f"=== ROUTING AFTER ROUTING === next_step={next_step}")

    if next_step == "success":
        logger.info("Routing to: __end__")
        return "__end__"
    elif next_step == "retry":
        logger.info("Routing to: transcription (retry)")
        return "transcription"
    else:
        logger.info("Routing to: error_handler")
        return "error_handler"
