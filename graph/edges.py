from typing import Literal

from graph.state import CallCenterState


def route_after_intake(
    state: CallCenterState,
) -> Literal["transcription", "summarization", "error_handler"]:
    """Determine next step after intake based on input type."""
    if state.get("error"):
        return "error_handler"

    if state.get("has_audio") and not state.get("transcript"):
        return "transcription"

    return "summarization"


def route_after_transcription(
    state: CallCenterState,
) -> Literal["summarization", "error_handler"]:
    """Check if transcription succeeded before proceeding."""
    if state.get("error") or not state.get("transcript"):
        return "error_handler"
    return "summarization"


def route_after_summarization(
    state: CallCenterState,
) -> Literal["scoring", "error_handler"]:
    """Check if summarization succeeded before proceeding."""
    if state.get("error"):
        return "error_handler"
    return "scoring"


def route_after_scoring(
    state: CallCenterState,
) -> Literal["routing", "error_handler"]:
    """Check if scoring succeeded before proceeding."""
    if state.get("error"):
        return "error_handler"
    return "routing"


def route_after_routing(
    state: CallCenterState,
) -> Literal["__end__", "transcription", "error_handler"]:
    """Determine outcome after routing agent analysis."""
    next_step = state.get("next_step")

    if next_step == "success":
        return "__end__"
    elif next_step == "retry":
        return "transcription"
    else:
        return "error_handler"
