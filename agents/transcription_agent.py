from typing import Any

from services.deepgram_service import DeepgramService


def transcription_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Transcribes audio file using Deepgram API with speaker diarization.

    This agent:
    1. Checks if a transcript already exists (skips if so)
    2. Calls Deepgram API to transcribe the audio
    3. Identifies different speakers in the conversation
    4. Returns formatted transcript with speaker labels

    Returns:
        dict with transcript, speaker segments, and related metadata
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

        deepgram = DeepgramService()

        # Transcribe with speaker diarization
        result = deepgram.transcribe(file_path)

        # Use formatted transcript with speaker labels as the main transcript
        # This will be used by summarization and scoring agents
        transcript = result.get("formatted_transcript") or result.get("text", "")

        return {
            "transcript": transcript,
            "transcript_plain": result.get("text"),  # Plain text without labels
            "speaker_segments": result.get("speakers", []),
            "num_speakers": result.get("num_speakers", 0),
            "transcription_language": result.get("language"),
            "transcription_duration": result.get("duration"),
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
