from typing import Any

from services.whisper_service import WhisperService


def transcription_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Transcribes audio file using OpenAI Whisper API.

    This agent:
    1. Checks if a transcript already exists (skips if so)
    2. Calls Whisper API to transcribe the audio
    3. Handles large files by chunking
    4. Extracts language and confidence information

    Returns:
        dict with transcript and related metadata
    """
    # Skip if transcript already exists (e.g., user provided text file)
    if state.get("transcript"):
        return {"current_step": "transcription"}

    try:
        file_path = state.get("input_file_path")

        if not file_path:
            return {
                "error": "No input file path for transcription",
                "error_type": "MissingInputError",
                "error_count": state.get("error_count", 0) + 1,
                "current_step": "transcription",
            }

        whisper = WhisperService()

        # Transcribe (handles chunking for large files internally)
        result = whisper.transcribe(file_path)

        return {
            "transcript": result["text"],
            "transcription_language": result.get("language"),
            "transcription_duration": result.get("duration"),
            "word_timestamps": result.get("words"),
            "current_step": "transcription",
            "error": None,  # Clear any previous error
        }

    except Exception as e:
        return {
            "error": f"Transcription failed: {str(e)}",
            "error_type": "TranscriptionError",
            "error_count": state.get("error_count", 0) + 1,
            "current_step": "transcription",
        }
