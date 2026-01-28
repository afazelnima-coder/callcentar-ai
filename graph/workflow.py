from langgraph.graph import StateGraph, START, END

from graph.state import CallCenterState
from graph.edges import (
    route_after_intake,
    route_after_transcription,
    route_after_summarization,
    route_after_scoring,
    route_after_routing,
)
from agents.intake_agent import call_intake_node
from agents.transcription_agent import transcription_node
from agents.summarization_agent import summarization_node
from agents.scoring_agent import scoring_node
from agents.routing_agent import routing_node, error_handler_node


def create_workflow() -> StateGraph:
    """
    Create and compile the call center grading workflow.

    Each step has error checking to route to error_handler if something fails.
    """
    builder = StateGraph(CallCenterState)

    # Add all nodes
    builder.add_node("intake", call_intake_node)
    builder.add_node("transcription", transcription_node)
    builder.add_node("summarization", summarization_node)
    builder.add_node("scoring", scoring_node)
    builder.add_node("routing", routing_node)
    builder.add_node("error_handler", error_handler_node)

    # Start -> Intake
    builder.add_edge(START, "intake")

    # Intake -> Conditional (transcription or summarization or error)
    builder.add_conditional_edges(
        "intake",
        route_after_intake,
        {
            "transcription": "transcription",
            "summarization": "summarization",
            "error_handler": "error_handler",
        },
    )

    # Transcription -> Conditional (summarization or error)
    builder.add_conditional_edges(
        "transcription",
        route_after_transcription,
        {
            "summarization": "summarization",
            "error_handler": "error_handler",
        },
    )

    # Summarization -> Conditional (scoring or error)
    builder.add_conditional_edges(
        "summarization",
        route_after_summarization,
        {
            "scoring": "scoring",
            "error_handler": "error_handler",
        },
    )

    # Scoring -> Conditional (routing or error)
    builder.add_conditional_edges(
        "scoring",
        route_after_scoring,
        {
            "routing": "routing",
            "error_handler": "error_handler",
        },
    )

    # Routing -> Conditional (end, retry, or error)
    builder.add_conditional_edges(
        "routing",
        route_after_routing,
        {
            "__end__": END,
            "transcription": "transcription",
            "error_handler": "error_handler",
        },
    )

    # Error handler -> End
    builder.add_edge("error_handler", END)

    return builder.compile()


# Create singleton workflow instance
workflow = create_workflow()
