from typing import Literal

from graph.state import CallCenterState


def route_after_intake(
    state: CallCenterState,
) -> Literal["transcription", "summarization", "error_handler"]:
    """
    Determine next step after intake based on input type.

    Routes to:
    - error_handler: if validation failed
    - transcription: if audio file needs transcribing
    - summarization: if transcript already provided
    """
    if state.get("error"):
        return "error_handler"

    if state.get("has_audio") and not state.get("transcript"):
        return "transcription"

    return "summarization"


def route_after_routing(
    state: CallCenterState,
) -> Literal["__end__", "transcription", "error_handler"]:
    """
    Determine outcome after routing agent analysis.

    Routes to:
    - __end__: workflow completed successfully
    - transcription: retry from transcription step
    - error_handler: max retries exceeded or unrecoverable error
    """
    next_step = state.get("next_step")

    if next_step == "success":
        return "__end__"
    elif next_step == "retry":
        return "transcription"
    else:  # fallback
        return "error_handler"
