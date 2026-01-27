import os
from typing import Any

from schemas.metadata_schemas import CallMetadata
from services.audio_processor import AudioProcessor

SUPPORTED_AUDIO_FORMATS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
SUPPORTED_TEXT_FORMATS = {".txt", ".json"}
MAX_FILE_SIZE_MB = 100


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
    try:
        file_path = state.get("input_file_path")

        if not file_path:
            return {
                "error": "No input file path provided",
                "error_type": "MissingInputError",
                "file_validated": False,
            }

        # Validate file exists
        if not os.path.exists(file_path):
            return {
                "error": f"File not found: {file_path}",
                "error_type": "FileNotFoundError",
                "file_validated": False,
            }

        # Get file info
        file_ext = os.path.splitext(file_path)[1].lower()
        file_size = os.path.getsize(file_path)

        # Check file size
        if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
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
            return {
                "error": f"Unsupported file format: {file_ext}",
                "error_type": "UnsupportedFormatError",
                "file_validated": False,
                "validation_errors": [f"Supported formats: {supported}"],
            }

        # Extract metadata
        if is_audio:
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
            with open(file_path, "r") as f:
                raw_transcript = f.read()

            metadata = CallMetadata(
                file_name=os.path.basename(file_path),
                file_size_bytes=file_size,
                file_format=file_ext[1:],
            )

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

    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "file_validated": False,
            "error_count": state.get("error_count", 0) + 1,
        }
