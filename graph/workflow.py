from langgraph.graph import StateGraph, START, END

from graph.state import CallCenterState
from graph.edges import route_after_intake, route_after_routing
from agents.intake_agent import call_intake_node
from agents.transcription_agent import transcription_node
from agents.summarization_agent import summarization_node
from agents.scoring_agent import scoring_node
from agents.routing_agent import routing_node, error_handler_node


def create_workflow() -> StateGraph:
    """
    Create and compile the call center grading workflow.

    The workflow processes calls through these stages:
    1. Intake: Validate input and extract metadata
    2. Transcription: Convert audio to text (skipped if transcript provided)
    3. Summarization: Generate call summary and key points
    4. Scoring: Evaluate quality using 19-item rubric
    5. Routing: Determine success/retry/failure

    Graph structure:
        START
          |
        intake
          |
        [conditional: has_audio?]
          |           \
    transcription    (skip)
          |           /
        summarization
          |
        scoring
          |
        routing
          |
        [conditional: success/retry/fallback]
         |      |           |
        END   retry    error_handler
              (loop)         |
                           END
    """
    # Initialize the graph with state schema
    builder = StateGraph(CallCenterState)

    # Add all nodes
    builder.add_node("intake", call_intake_node)
    builder.add_node("transcription", transcription_node)
    builder.add_node("summarization", summarization_node)
    builder.add_node("scoring", scoring_node)
    builder.add_node("routing", routing_node)
    builder.add_node("error_handler", error_handler_node)

    # Define edges

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

    # Transcription -> Summarization
    builder.add_edge("transcription", "summarization")

    # Summarization -> Scoring
    builder.add_edge("summarization", "scoring")

    # Scoring -> Routing
    builder.add_edge("scoring", "routing")

    # Routing -> Conditional (end, retry, or error)
    builder.add_conditional_edges(
        "routing",
        route_after_routing,
        {
            "__end__": END,
            "transcription": "transcription",  # Retry loop
            "error_handler": "error_handler",
        },
    )

    # Error handler -> End
    builder.add_edge("error_handler", END)

    # Compile the graph
    return builder.compile()


# Create singleton workflow instance
workflow = create_workflow()
