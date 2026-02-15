import sys
from pathlib import Path

# Add project root to path for Streamlit Cloud deployment
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime
import tempfile
import os

from graph.workflow import workflow
from graph.state import CallCenterState


# Page configuration
st.set_page_config(
    page_title="Call Center Quality Grading",
    page_icon=":telephone_receiver:",
    layout="wide",
)

def inject_custom_css():
    """Inject custom CSS for agent animations (called once at page load)."""
    st.markdown("""
    <style>
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    @keyframes wave {
        0%, 100% { transform: scaleY(1); }
        25% { transform: scaleY(1.5); }
        50% { transform: scaleY(0.8); }
        75% { transform: scaleY(1.3); }
    }
    @keyframes typing {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    @keyframes stars {
        0%, 100% { transform: scale(1) rotate(0deg); }
        25% { transform: scale(1.2) rotate(5deg); }
        50% { transform: scale(1) rotate(0deg); }
        75% { transform: scale(1.2) rotate(-5deg); }
    }
    @keyframes routing {
        0% { transform: translateX(0); }
        25% { transform: translateX(5px); }
        50% { transform: translateX(0); }
        75% { transform: translateX(-5px); }
        100% { transform: translateX(0); }
    }
    .agent-animation {
        display: inline-flex;
        align-items: center;
        padding: 20px;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(100, 100, 100, 0.1), rgba(150, 150, 150, 0.05));
        margin: 10px 0;
    }
    .agent-icon {
        font-size: 48px;
        display: inline-block;
    }
    .intake-animation .agent-icon { animation: spin 2s linear infinite; }
    .transcription-animation .agent-icon { animation: wave 0.6s ease-in-out infinite; }
    .summarization-animation .agent-icon { animation: typing 1s ease-in-out infinite; }
    .scoring-animation .agent-icon { animation: stars 1s ease-in-out infinite; }
    .routing-animation .agent-icon { animation: routing 0.8s ease-in-out infinite; }
    .error-animation .agent-icon { animation: pulse 1s ease-in-out infinite; color: #ff4b4b; }
    .agent-status-text { margin-left: 15px; font-size: 18px; font-weight: 500; }
    .agent-description { font-size: 14px; color: #888; margin-top: 5px; }
    /* Sidebar animations */
    @keyframes sidebar-pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
    }
    .sidebar-workflow { font-family: sans-serif; }
    .sidebar-step { display: flex; align-items: center; padding: 6px 0; font-size: 14px; }
    .sidebar-step-icon { font-size: 20px; margin-right: 10px; display: inline-block; min-width: 24px; text-align: center; }
    .sidebar-step-running .sidebar-step-icon { animation: sidebar-pulse 1s ease-in-out infinite; }
    .sidebar-step-running .sidebar-step-name { font-weight: bold; color: #ff9500; }
    .sidebar-step-complete .sidebar-step-name { color: #28a745; }
    .sidebar-step-error .sidebar-step-name { color: #dc3545; font-weight: bold; }
    .sidebar-step-pending .sidebar-step-name { color: #6c757d; }
    .sidebar-arrow { padding-left: 30px; color: #aaa; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# Agent configuration with icons and descriptions
AGENT_CONFIG = {
    "intake": {
        "icon": "\U0001F50D",  # Magnifying glass
        "name": "Intake Agent",
        "action": "Scanning and validating file...",
        "description": "Checking file format, size, and extracting metadata",
        "css_class": "intake-animation"
    },
    "transcription": {
        "icon": "\U0001F3A4",  # Microphone
        "name": "Transcription Agent",
        "action": "Converting speech to text...",
        "description": "Processing audio with speaker diarization",
        "css_class": "transcription-animation"
    },
    "summarization": {
        "icon": "\U0001F4DD",  # Memo/writing
        "name": "Summarization Agent",
        "action": "Generating call summary...",
        "description": "Analyzing conversation and extracting key points",
        "css_class": "summarization-animation"
    },
    "scoring": {
        "icon": "\U00002B50",  # Star
        "name": "Scoring Agent",
        "action": "Evaluating call quality...",
        "description": "Scoring against 19-item quality rubric",
        "css_class": "scoring-animation"
    },
    "routing": {
        "icon": "\U0001F3AF",  # Bullseye/target
        "name": "Routing Agent",
        "action": "Finalizing results...",
        "description": "Determining outcome and next steps",
        "css_class": "routing-animation"
    },
    "error_handler": {
        "icon": "\U000026A0",  # Warning
        "name": "Error Handler",
        "action": "Handling error...",
        "description": "Processing error and preserving partial results",
        "css_class": "error-animation"
    }
}


def render_agent_animation(container, agent_name: str):
    """Render an animated status display for a specific agent."""
    config = AGENT_CONFIG.get(agent_name, AGENT_CONFIG["intake"])

    html = f'''<div class="agent-animation {config['css_class']}"><span class="agent-icon">{config['icon']}</span><div><div class="agent-status-text">{config['action']}</div><div class="agent-description">{config['description']}</div></div></div>'''
    container.markdown(html, unsafe_allow_html=True)

# Workflow steps definition
WORKFLOW_STEPS = [
    ("intake", "Intake Agent", "Validates file & extracts metadata"),
    ("transcription", "Transcription Agent", "Converts audio to text"),
    ("summarization", "Summarization Agent", "Generates call summary"),
    ("scoring", "Scoring Agent", "Evaluates quality"),
    ("routing", "Routing Agent", "Determines outcome"),
]


def build_workflow_status_html(current_step: str = None, status: str = "idle") -> str:
    """Build the workflow status as HTML with animations."""
    # Agent icons from config
    AGENT_ICONS = {
        "intake": "\U0001F50D",       # Magnifying glass
        "transcription": "\U0001F3A4", # Microphone
        "summarization": "\U0001F4DD", # Memo
        "scoring": "\U00002B50",       # Star
        "routing": "\U0001F3AF",       # Target
    }
    ICON_PENDING = "\U000026AA"    # White circle
    ICON_COMPLETE = "\U00002705"   # Check mark
    ICON_ERROR = "\U0001F534"      # Red circle
    ICON_ARROW = "\U00002B07"      # Down arrow

    html_parts = ['<div class="sidebar-workflow">', '<h3>Workflow Status</h3>']

    for i, (step_id, step_name, step_desc) in enumerate(WORKFLOW_STEPS):
        # Determine the status of this step
        if status == "idle":
            step_status = "pending"
            icon = ICON_PENDING
        elif status == "error":
            if step_id == current_step:
                step_status = "error"
                icon = ICON_ERROR
            elif _step_index(step_id) < _step_index(current_step):
                step_status = "complete"
                icon = ICON_COMPLETE
            else:
                step_status = "pending"
                icon = ICON_PENDING
        elif status == "complete":
            step_status = "complete"
            icon = ICON_COMPLETE
        elif step_id == current_step:
            step_status = "running"
            icon = AGENT_ICONS.get(step_id, "\U0001F7E0")  # Agent icon or orange circle
        elif _step_index(step_id) < _step_index(current_step):
            step_status = "complete"
            icon = ICON_COMPLETE
        else:
            step_status = "pending"
            icon = ICON_PENDING

        # Build the step HTML
        html_parts.append(f'<div class="sidebar-step sidebar-step-{step_status}">')
        html_parts.append(f'<span class="sidebar-step-icon">{icon}</span>')
        html_parts.append(f'<span class="sidebar-step-name">{step_name}</span>')
        html_parts.append('</div>')

        # Add arrow to next step (except for the last step)
        if i < len(WORKFLOW_STEPS) - 1:
            html_parts.append(f'<div class="sidebar-arrow">{ICON_ARROW}</div>')

    html_parts.append('</div>')
    return ''.join(html_parts)


def render_workflow_status(container, current_step: str = None, status: str = "idle"):
    """Render the workflow status into a given container."""
    container.markdown(build_workflow_status_html(current_step, status), unsafe_allow_html=True)


def _step_index(step_id: str) -> int:
    """Get the index of a step in the workflow."""
    for i, (sid, _, _) in enumerate(WORKFLOW_STEPS):
        if sid == step_id:
            return i
    return -1


def main():
    # Inject custom CSS for animations (once per page load)
    inject_custom_css()

    st.title("Call Center Quality Grading System")
    st.markdown(
        "Upload a call recording or transcript to receive automated quality assessment."
    )

    # Sidebar for settings
    with st.sidebar:
        st.header("Settings")
        max_retries = st.slider("Max Retries on Error", 0, 5, 2)
        show_transcript = st.checkbox("Show Full Transcript", value=True)
        show_detailed_scores = st.checkbox("Show Detailed Rubric Scores", value=True)

        st.divider()
        st.markdown("### Supported Formats")
        st.markdown("**Audio:** WAV, MP3, M4A, FLAC, OGG")
        st.markdown("**Text:** TXT")

        st.divider()

        # Create a placeholder for workflow status that can be updated in real-time
        workflow_status_placeholder = st.empty()

        # Initial render of workflow status
        if "workflow_current_step" in st.session_state:
            render_workflow_status(
                workflow_status_placeholder,
                st.session_state.get("workflow_current_step"),
                st.session_state.get("workflow_status", "idle")
            )
        else:
            render_workflow_status(workflow_status_placeholder)

    # Store the placeholder in session state for access during processing
    st.session_state["workflow_status_placeholder"] = workflow_status_placeholder

    # Upload section at the top
    st.subheader("Upload Call Recording or Transcript")

    upload_col1, upload_col2 = st.columns([2, 1])

    with upload_col1:
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["wav", "mp3", "m4a", "flac", "ogg", "txt"],
            help="Supported formats: WAV, MP3, M4A, FLAC, OGG (audio) or TXT (transcript)",
        )

    with upload_col2:
        # Optional metadata inputs
        with st.expander("Optional: Add Call Metadata"):
            call_id = st.text_input("Call ID")
            agent_id = st.text_input("Agent ID")
            call_type = st.selectbox(
                "Call Type", ["Support", "Sales", "Inquiry", "Complaint", "Other"]
            )

    # Check if we should start processing (triggered by button click on previous run)
    if st.session_state.get("start_analysis") and uploaded_file is not None:
        st.session_state["start_analysis"] = False
        process_file(
            uploaded_file, max_retries, show_transcript, show_detailed_scores
        )
        return  # Exit after processing (process_file calls st.rerun())

    # Process button
    if uploaded_file is not None:
        if st.button("Analyze Call", type="primary"):
            # Clear previous results before starting new analysis
            if "results" in st.session_state:
                del st.session_state["results"]
            if "workflow_current_step" in st.session_state:
                del st.session_state["workflow_current_step"]
            if "workflow_status" in st.session_state:
                del st.session_state["workflow_status"]

            # Set flag to start processing on next run (after UI clears)
            st.session_state["start_analysis"] = True
            st.rerun()

    # Results section - full width below upload
    st.divider()
    if "results" in st.session_state:
        display_results(st.session_state["results"], show_transcript, show_detailed_scores)
    else:
        st.info("Upload a file and click 'Analyze Call' to see results.")


def process_file(uploaded_file, max_retries, show_transcript, show_detailed_scores):
    """Process the uploaded file through the LangGraph workflow."""

    # Save uploaded file to temp location
    file_ext = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        # Initialize state
        initial_state: CallCenterState = {
            "input_file_path": tmp_path,
            "input_file_name": uploaded_file.name,
            "max_retries": max_retries,
            "error_count": 0,
            "started_at": datetime.now(),
            "workflow_status": "in_progress",
            "error_history": [],
        }

        # Progress display - full width
        st.subheader("Processing...")

        # Create progress indicators
        progress_bar = st.progress(0)
        animation_container = st.empty()  # Container for agent animations
        status_text = st.empty()

        # Step tracking for progress bar
        step_progress = {
            "intake": 20,
            "transcription": 40,
            "summarization": 60,
            "scoring": 80,
            "routing": 100,
        }

        # Initial status
        status_text.text("Starting analysis...")
        progress_bar.progress(10)

        # Initialize workflow status in session state
        st.session_state["workflow_current_step"] = "intake"
        st.session_state["workflow_status"] = "running"

        # Get the sidebar placeholder for real-time updates
        sidebar_placeholder = st.session_state.get("workflow_status_placeholder")

        # Execute workflow with streaming to track progress
        try:
            final_state = {}

            # Stream through the workflow to get real-time updates
            for event in workflow.stream(initial_state):
                # event is a dict with node name as key and state update as value
                for node_name, state_update in event.items():
                    # Update session state for sidebar display
                    st.session_state["workflow_current_step"] = node_name

                    # Update progress bar and animated status
                    if node_name in step_progress:
                        progress_bar.progress(step_progress[node_name])
                        # Render agent-specific animation
                        render_agent_animation(animation_container, node_name)
                        status_text.empty()  # Clear text when showing animation

                    # Update sidebar workflow status in real-time
                    if sidebar_placeholder:
                        render_workflow_status(sidebar_placeholder, node_name, "running")

                    # Accumulate state updates
                    if isinstance(state_update, dict):
                        final_state.update(state_update)

            # Mark workflow as complete
            st.session_state["workflow_status"] = "complete"
            progress_bar.progress(100)
            animation_container.empty()  # Clear animation
            status_text.empty()

            # Update sidebar to show completion
            if sidebar_placeholder:
                render_workflow_status(sidebar_placeholder, "routing", "complete")

            # Store in session state - will be displayed by main()
            st.session_state["results"] = final_state

            # Rerun to display results in the proper section
            st.rerun()

        except Exception as e:
            # Mark workflow as failed
            st.session_state["workflow_status"] = "error"
            progress_bar.progress(100)
            # Show error animation
            render_agent_animation(animation_container, "error_handler")
            status_text.empty()

            # Update sidebar to show error state
            current_step = st.session_state.get("workflow_current_step", "intake")
            if sidebar_placeholder:
                render_workflow_status(sidebar_placeholder, current_step, "error")

            # Check if it's a content validation error
            if type(e).__name__ == "ContentValidationError":
                st.error(f"Content Validation Failed: {str(e)}")
                st.warning("Please upload a valid call center recording or transcript.")
            else:
                st.error(f"Workflow error: {str(e)}")

    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def display_results(state: CallCenterState, show_transcript: bool, show_detailed: bool):
    """Display the analysis results."""

    status = state.get("workflow_status")

    if status == "failed":
        st.error(f"Analysis failed: {state.get('error')}")

        # Show partial results if available
        partial = state.get("partial_results", {})
        if partial.get("transcript_available"):
            st.warning("Partial results available: Transcript was generated before failure.")
            if show_transcript and state.get("transcript"):
                with st.expander("View Transcript"):
                    st.text(state["transcript"])
        return

    # Overall Grade Display
    grade = state.get("overall_grade", "N/A")
    scores = state.get("quality_scores")

    st.subheader("Quality Assessment Results")

    # Grade display with color coding
    grade_colors = {
        "A": "green",
        "B": "blue",
        "C": "orange",
        "D": "red",
        "F": "red",
    }

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Grade", grade)
    with col2:
        if scores:
            st.metric("Score", f"{scores.percentage_score:.1f}%")
    with col3:
        resolution = state.get("resolution_status", "N/A")
        st.metric("Resolution Status", resolution.title() if resolution else "N/A")

    # Summary section
    if state.get("summary"):
        st.subheader("Call Summary")
        summary = state["summary"]
        st.write(summary.brief_summary)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Customer Issue:**")
            st.write(summary.customer_issue)
        with col2:
            st.markdown("**Resolution:**")
            st.write(summary.resolution_provided)

        st.markdown(f"**Customer Sentiment:** {summary.customer_sentiment.title()}")
        st.markdown(f"**Call Category:** {summary.call_category.title()}")

        with st.expander("Key Topics"):
            for topic in summary.key_topics:
                st.write(f"- {topic}")

        if summary.action_items:
            with st.expander("Action Items"):
                for item in summary.action_items:
                    st.write(f"- {item}")

    # Detailed Scores
    if show_detailed and scores:
        st.subheader("Detailed Rubric Scores")

        # Create tabs for each category
        tabs = st.tabs(
            ["Greeting", "Communication", "Resolution", "Professionalism", "Closing"]
        )

        categories = [
            ("Greeting & Opening", scores.greeting),
            ("Communication Skills", scores.communication),
            ("Problem Resolution", scores.resolution),
            ("Professionalism", scores.professionalism),
            ("Call Closing", scores.closing),
        ]

        for tab, (name, category) in zip(tabs, categories):
            with tab:
                for field_name, field_value in category:
                    if hasattr(field_value, "score"):
                        # Create a colored indicator based on score
                        score_color = (
                            "green" if field_value.score >= 4
                            else "orange" if field_value.score >= 3
                            else "red"
                        )

                        st.markdown(
                            f"**{field_name.replace('_', ' ').title()}:** "
                            f":{score_color}[{field_value.score}/5]"
                        )
                        st.caption(f"*Evidence:* {field_value.evidence}")
                        if field_value.score < 4:
                            st.caption(f"*Feedback:* {field_value.feedback}")
                        st.divider()

    # Strengths and Areas for Improvement
    if scores:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Strengths")
            for strength in scores.strengths:
                st.success(f"- {strength}")

        with col2:
            st.subheader("Areas for Improvement")
            for area in scores.areas_for_improvement:
                st.warning(f"- {area}")

        # Compliance issues
        if scores.compliance_issues:
            st.subheader("Compliance Issues")
            for issue in scores.compliance_issues:
                st.error(f"- {issue}")

        if scores.escalation_recommended:
            st.error("This call has been flagged for supervisor review.")

    # Transcript with speaker labels
    if show_transcript and state.get("transcript"):
        with st.expander("Full Transcript", expanded=True):
            num_speakers = state.get("num_speakers", 0)
            if num_speakers > 0:
                st.caption(f"Detected {num_speakers} speaker(s)")

            # Display formatted transcript with speaker labels
            transcript = state["transcript"]
            # Use markdown for better formatting of speaker labels
            st.markdown(transcript.replace("\n", "  \n"))

    # Processing info
    with st.expander("Processing Details"):
        st.write(f"**Processing Time:** {state.get('processing_time_seconds', 0):.2f} seconds")
        if state.get("num_speakers"):
            st.write(f"**Speakers Detected:** {state.get('num_speakers')}")
        if state.get("transcription_duration"):
            st.write(f"**Audio Duration:** {state.get('transcription_duration'):.1f} seconds")
        if state.get("metadata"):
            metadata = state["metadata"]
            st.write(f"**File:** {metadata.file_name}")
            st.write(f"**Format:** {metadata.file_format}")
            if metadata.duration_seconds:
                st.write(f"**Duration:** {metadata.duration_seconds:.1f} seconds")


if __name__ == "__main__":
    main()
