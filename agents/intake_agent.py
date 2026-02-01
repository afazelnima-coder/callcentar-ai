import os
import logging
from typing import Any

from schemas.metadata_schemas import CallMetadata
from services.audio_processor import AudioProcessor
from services.guardrails_service import GuardrailsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_FORMATS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
SUPPORTED_TEXT_FORMATS = {".txt", ".json"}
MAX_FILE_SIZE_MB = 100


class ContentValidationError(Exception):
    """Raised when content validation fails - stops the workflow immediately."""
    pass


def call_intake_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Validates input file and extracts metadata.

    This agent is the entry point of the workflow. It:
    1. Validates the file exists and is within size limits
    2. Determines if the input is audio or transcript
    3. Extracts metadata (duration, format, etc.)
    4. Sets up state for subsequent agents

    Returns:
        dict with keys to update in state
    """
    logger.info("=== INTAKE AGENT START ===")

    try:
        file_path = state.get("input_file_path")
        logger.info(f"Processing file: {file_path}")

        if not file_path:
            logger.error("No input file path provided")
            return {
                "error": "No input file path provided",
                "error_type": "MissingInputError",
                "file_validated": False,
            }

        # Validate file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return {
                "error": f"File not found: {file_path}",
                "error_type": "FileNotFoundError",
                "file_validated": False,
            }

        # Get file info
        file_ext = os.path.splitext(file_path)[1].lower()
        file_size = os.path.getsize(file_path)
        logger.info(f"File type: {file_ext}, size: {file_size} bytes")

        # Check file size
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            logger.error(f"File too large: {file_size / 1024 / 1024:.1f}MB")
            return {
                "error": f"File too large: {file_size / 1024 / 1024:.1f}MB (max {MAX_FILE_SIZE_MB}MB)",
                "error_type": "FileTooLargeError",
                "file_validated": False,
            }

        # Determine file type
        is_audio = file_ext in SUPPORTED_AUDIO_FORMATS
        is_text = file_ext in SUPPORTED_TEXT_FORMATS

        if not is_audio and not is_text:
            supported = SUPPORTED_AUDIO_FORMATS | SUPPORTED_TEXT_FORMATS
            logger.error(f"Unsupported file format: {file_ext}")
            return {
                "error": f"Unsupported file format: {file_ext}",
                "error_type": "UnsupportedFormatError",
                "file_validated": False,
                "validation_errors": [f"Supported formats: {supported}"],
            }

        # Extract metadata
        if is_audio:
            logger.info("Processing audio file...")
            processor = AudioProcessor()
            audio_info = processor.get_audio_info(file_path)
            metadata = CallMetadata(
                file_name=os.path.basename(file_path),
                file_size_bytes=file_size,
                file_format=file_ext[1:],
                duration_seconds=audio_info["duration"],
                sample_rate=audio_info["sample_rate"],
                channels=audio_info["channels"],
            )

            logger.info("=== INTAKE AGENT COMPLETE (audio) ===")
            return {
                "metadata": metadata,
                "has_audio": True,
                "file_validated": True,
                "input_file_type": "audio",
                "current_step": "intake",
                "workflow_status": "in_progress",
                "error": None,
            }
        else:
            # Text file - read as transcript
            logger.info("Processing text file...")
            with open(file_path, "r") as f:
                raw_transcript = f.read()

            # Validate content is a call center conversation
            logger.info("Validating content...")
            is_valid, reason = _validate_call_center_content(raw_transcript)
            logger.info(f"Validation result: is_valid={is_valid}, reason={reason}")

            if not is_valid:
                # Raise exception to immediately stop the workflow
                logger.error(f"CONTENT VALIDATION FAILED: {reason}")
                raise ContentValidationError(f"Invalid content: {reason}")

            metadata = CallMetadata(
                file_name=os.path.basename(file_path),
                file_size_bytes=file_size,
                file_format=file_ext[1:],
            )

            logger.info("=== INTAKE AGENT COMPLETE (text) ===")
            return {
                "metadata": metadata,
                "has_audio": False,
                "file_validated": True,
                "input_file_type": "transcript",
                "raw_transcript": raw_transcript,
                "transcript": raw_transcript,  # Skip transcription
                "current_step": "intake",
                "workflow_status": "in_progress",
                "error": None,
            }

    except ContentValidationError:
        # Re-raise ContentValidationError to stop the workflow
        logger.error("Re-raising ContentValidationError to stop workflow")
        raise

    except Exception as e:
        logger.error(f"Intake agent error: {type(e).__name__}: {str(e)}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "file_validated": False,
            "error_count": state.get("error_count", 0) + 1,
        }


def _validate_call_center_content(text: str) -> tuple[bool, str]:
    """
    Validate that the text content is a call center conversation using Guardrails AI.

    Returns:
        tuple of (is_valid, reason)
    """
    guardrails = GuardrailsService()
    return guardrails.validate_call_center_content(text)


def validate_transcript_content(transcript: str) -> tuple[bool, str]:
    """
    Public function to validate transcript content after audio transcription.
    Called by transcription_agent after Deepgram processing.

    Returns:
        tuple of (is_valid, reason)
    """
    return _validate_call_center_content(transcript)
