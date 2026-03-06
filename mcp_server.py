#!/usr/bin/env python3
"""
MCP Server for Call Center Quality Grading System

This server exposes the call center grading workflow as MCP tools that can be used
by Claude Desktop and other MCP clients.

Tools provided:
- grade_call_transcript: Grade a call from text transcript
- grade_call_audio: Grade a call from audio file
- get_scoring_rubric: Get the quality scoring rubric schema
- analyze_call_summary: Get call summary without full quality scoring
"""

import asyncio
import json
import logging
import tempfile
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from graph.workflow import workflow
from graph.state import CallCenterState
from schemas.output_schemas import QualityScores, CallSummary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# Create MCP server
mcp = Server("call-center-grading")


def extract_results(final_state: CallCenterState) -> dict[str, Any]:
    """Extract and format results from workflow state."""
    results = {
        "status": final_state.get("workflow_status", "unknown"),
        "current_step": final_state.get("current_step", "unknown"),
    }

    # Add error information if present
    if final_state.get("error"):
        results["error"] = final_state["error"]
        results["error_type"] = final_state.get("error_type")
        results["partial_results"] = final_state.get("partial_results")
        return results

    # Add transcript if available
    if final_state.get("transcript"):
        results["transcript"] = final_state["transcript"]

    # Add summary if available
    if final_state.get("summary"):
        summary = final_state["summary"]
        if isinstance(summary, CallSummary):
            results["summary"] = summary.model_dump()
        else:
            results["summary"] = summary

    # Add quality scores if available
    if final_state.get("quality_scores"):
        scores = final_state["quality_scores"]
        if isinstance(scores, QualityScores):
            results["quality_scores"] = scores.model_dump()
        else:
            results["quality_scores"] = scores

    # Add overall grade and recommendations
    if final_state.get("overall_grade"):
        results["overall_grade"] = final_state["overall_grade"]
    if final_state.get("recommendations"):
        results["recommendations"] = final_state["recommendations"]

    # Add metadata
    if final_state.get("metadata"):
        results["metadata"] = final_state["metadata"]

    # Add processing time
    if final_state.get("processing_time_seconds"):
        results["processing_time_seconds"] = final_state["processing_time_seconds"]

    return results


@mcp.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return [
        Tool(
            name="grade_call_transcript",
            description="Grade a call center conversation from a text transcript. "
            "Analyzes communication quality, professionalism, problem resolution, and more. "
            "Returns detailed quality scores, overall grade, and improvement recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "transcript": {
                        "type": "string",
                        "description": "The call transcript text (can include speaker labels like 'Agent: ' and 'Customer: ')",
                    },
                    "call_metadata": {
                        "type": "object",
                        "description": "Optional metadata about the call (customer_id, agent_id, call_date, etc.)",
                        "properties": {
                            "customer_id": {"type": "string"},
                            "agent_id": {"type": "string"},
                            "call_date": {"type": "string"},
                            "call_duration_seconds": {"type": "number"},
                            "call_category": {"type": "string"},
                        },
                    },
                },
                "required": ["transcript"],
            },
        ),
        Tool(
            name="grade_call_audio",
            description="Grade a call center conversation from an audio file. "
            "Automatically transcribes the audio, then analyzes quality. "
            "Supports common audio formats (WAV, MP3, M4A, FLAC, OGG).",
            inputSchema={
                "type": "object",
                "properties": {
                    "audio_file_path": {
                        "type": "string",
                        "description": "Absolute path to the audio file",
                    },
                    "call_metadata": {
                        "type": "object",
                        "description": "Optional metadata about the call",
                        "properties": {
                            "customer_id": {"type": "string"},
                            "agent_id": {"type": "string"},
                            "call_date": {"type": "string"},
                        },
                    },
                },
                "required": ["audio_file_path"],
            },
        ),
        Tool(
            name="analyze_call_summary",
            description="Generate a structured summary of a call without full quality scoring. "
            "Faster than full grading when you just need to understand what happened. "
            "Returns customer issue, resolution, sentiment, topics, and action items.",
            inputSchema={
                "type": "object",
                "properties": {
                    "transcript": {
                        "type": "string",
                        "description": "The call transcript text",
                    },
                },
                "required": ["transcript"],
            },
        ),
        Tool(
            name="get_scoring_rubric",
            description="Get the detailed quality scoring rubric used for grading calls. "
            "Shows all evaluation categories, criteria, and the 5-point scoring scale. "
            "Useful for understanding what makes a high-quality call.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@mcp.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    try:
        if name == "grade_call_transcript":
            result = await grade_call_transcript(
                transcript=arguments["transcript"],
                call_metadata=arguments.get("call_metadata"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "grade_call_audio":
            result = await grade_call_audio(
                audio_file_path=arguments["audio_file_path"],
                call_metadata=arguments.get("call_metadata"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "analyze_call_summary":
            result = await analyze_call_summary(transcript=arguments["transcript"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "get_scoring_rubric":
            result = get_scoring_rubric()
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        error_result = {"error": str(e), "tool": name}
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]


async def grade_call_transcript(
    transcript: str, call_metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Grade a call from a text transcript.

    Args:
        transcript: The call transcript text
        call_metadata: Optional metadata about the call

    Returns:
        Dictionary with quality scores, summary, and recommendations
    """
    # Create a temporary file to pass to the workflow
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(transcript)
        temp_path = f.name

    try:
        # Create initial state
        initial_state: CallCenterState = {
            "input_file_path": temp_path,
            "input_file_type": "transcript",
            "input_file_name": "mcp_transcript.txt",
            "raw_transcript": transcript,
            "workflow_status": "in_progress",
            "current_step": "start",
            "error_count": 0,
            "max_retries": 2,
            "validation_errors": [],
        }

        # Add metadata if provided
        if call_metadata:
            from schemas.metadata_schemas import CallMetadata

            initial_state["metadata"] = CallMetadata(**call_metadata)

        # Run the workflow
        final_state = await workflow.ainvoke(initial_state)

        # Extract and return results
        return extract_results(final_state)

    finally:
        # Clean up temporary file
        Path(temp_path).unlink(missing_ok=True)


async def grade_call_audio(
    audio_file_path: str, call_metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Grade a call from an audio file.

    Args:
        audio_file_path: Path to the audio file
        call_metadata: Optional metadata about the call

    Returns:
        Dictionary with transcription, quality scores, summary, and recommendations
    """
    audio_path = Path(audio_file_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    # Create initial state
    initial_state: CallCenterState = {
        "input_file_path": str(audio_path.absolute()),
        "input_file_type": "audio",
        "input_file_name": audio_path.name,
        "has_audio": True,
        "workflow_status": "in_progress",
        "current_step": "start",
        "error_count": 0,
        "max_retries": 2,
        "validation_errors": [],
    }

    # Add metadata if provided
    if call_metadata:
        from schemas.metadata_schemas import CallMetadata

        initial_state["metadata"] = CallMetadata(**call_metadata)

    # Run the workflow
    final_state = await workflow.ainvoke(initial_state)

    # Extract and return results
    return extract_results(final_state)


async def analyze_call_summary(transcript: str) -> dict[str, Any]:
    """
    Generate just the call summary without full quality scoring.

    This is faster than full grading when you only need to understand
    what happened in the call.

    Args:
        transcript: The call transcript text

    Returns:
        Dictionary with call summary information
    """
    # For now, we run the full workflow but only return summary
    # In the future, this could be optimized to skip the scoring step
    result = await grade_call_transcript(transcript)

    # Extract just summary-related fields
    summary_result = {
        "status": result.get("status"),
        "summary": result.get("summary"),
        "metadata": result.get("metadata"),
    }

    if result.get("error"):
        summary_result["error"] = result["error"]

    return summary_result


def get_scoring_rubric() -> dict[str, Any]:
    """
    Get the quality scoring rubric schema.

    Returns:
        Dictionary describing the rubric structure and scoring criteria
    """
    return {
        "description": "Call Center Quality Grading Rubric",
        "scoring_scale": {
            "5": "Excellent - Exceeds expectations",
            "4": "Good - Meets expectations well",
            "3": "Satisfactory - Meets basic expectations",
            "2": "Needs Improvement - Below expectations",
            "1": "Poor - Significantly below expectations",
        },
        "categories": {
            "greeting_and_opening": {
                "description": "How the agent starts the call",
                "criteria": {
                    "proper_greeting": "Used company greeting, introduced self",
                    "verified_customer": "Properly verified customer identity",
                    "set_expectations": "Explained what they can help with",
                },
            },
            "communication_skills": {
                "description": "Verbal communication quality",
                "criteria": {
                    "clarity": "Spoke clearly, appropriate pace",
                    "tone": "Professional, friendly tone throughout",
                    "active_listening": "Acknowledged customer, asked clarifying questions",
                    "empathy": "Showed understanding of customer feelings",
                    "avoided_jargon": "Used customer-friendly language",
                },
            },
            "problem_resolution": {
                "description": "How well the issue was addressed",
                "criteria": {
                    "understanding": "Correctly identified customer issue",
                    "knowledge": "Demonstrated product/service knowledge",
                    "solution_quality": "Provided appropriate solution",
                    "first_call_resolution": "Resolved without need for callback",
                    "proactive_help": "Offered additional assistance",
                },
            },
            "professionalism": {
                "description": "Professional conduct",
                "criteria": {
                    "courtesy": "Maintained polite demeanor",
                    "patience": "Remained patient with difficult situations",
                    "ownership": "Took responsibility, avoided blame",
                    "confidentiality": "Handled sensitive info appropriately",
                },
            },
            "call_closing": {
                "description": "How the agent ended the call",
                "criteria": {
                    "summarized": "Recapped what was discussed/resolved",
                    "next_steps": "Clearly explained any follow-up needed",
                    "satisfaction_check": "Asked if customer needs anything else",
                    "proper_closing": "Used appropriate closing statement",
                },
            },
        },
        "total_possible_points": 95,
        "grading_scale": {
            "A": "90-100% - Excellent performance",
            "B": "80-89% - Good performance",
            "C": "70-79% - Satisfactory performance",
            "D": "60-69% - Needs improvement",
            "F": "Below 60% - Poor performance",
        },
        "output_includes": [
            "Individual scores for each criterion (1-5 scale)",
            "Evidence quotes from the transcript",
            "Constructive feedback for each area",
            "Overall grade (A-F)",
            "Top 3 strengths",
            "Top 3 areas for improvement",
            "Compliance issue flags",
            "Escalation recommendations",
        ],
    }


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    logger.info("Starting Call Center Quality Grading MCP Server")

    async with stdio_server() as (read_stream, write_stream):
        await mcp.run(
            read_stream,
            write_stream,
            mcp.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
