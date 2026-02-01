import logging
from typing import Any

from agents.intake_agent import validate_transcript_content, ContentValidationError
from services.deepgram_service import DeepgramService
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


SPEAKER_IDENTIFICATION_PROMPT = """Analyze this call center transcript and identify which speaker is the Agent (customer service representative) and which is the Customer.

Transcript:
{transcript}

Based on the context (who greets, who asks for help, who provides solutions, etc.), determine the role of each speaker.

Return ONLY a JSON object mapping speaker IDs to roles, like:
{{"0": "Agent", "1": "Customer"}}

If there are more than 2 speakers, identify additional ones as "Customer 2", "Supervisor", etc.
Return ONLY the JSON, no other text."""


def transcription_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Transcribes audio file using Deepgram API with speaker diarization,
    then uses GPT to identify speaker roles (Agent vs Customer).
    """
    logger.info("=== TRANSCRIPTION AGENT START ===")

    # Skip if transcript already exists (e.g., user provided text file)
    if state.get("transcript"):
        logger.info("Transcript already exists, skipping transcription")
        return {"current_step": "transcription"}

    try:
        file_path = state.get("input_file_path")
        logger.info(f"Transcribing file: {file_path}")

        if not file_path:
            logger.error("No input file path for transcription")
            return {
                "error": "No input file path for transcription",
                "error_type": "MissingInputError",
                "error_count": state.get("error_count", 0) + 1,
                "current_step": "transcription",
            }

        # Step 1: Transcribe with Deepgram
        logger.info("Calling Deepgram API...")
        deepgram = DeepgramService()
        result = deepgram.transcribe(file_path)
        logger.info("Deepgram transcription complete")

        formatted_transcript = result.get("formatted_transcript") or result.get("text", "")
        speakers = result.get("speakers", [])

        # Step 2: Validate the transcribed content is a call center conversation
        logger.info("Validating transcribed content...")
        is_valid, reason = validate_transcript_content(formatted_transcript)
        logger.info(f"Validation result: is_valid={is_valid}, reason={reason}")

        if not is_valid:
            # Raise exception to immediately stop the workflow
            logger.error(f"CONTENT VALIDATION FAILED: {reason}")
            raise ContentValidationError(f"Invalid audio content: {reason}")

        # Step 3: Use GPT to identify speaker roles if we have multiple speakers
        if speakers and result.get("num_speakers", 0) > 1:
            logger.info("Identifying speaker roles...")
            formatted_transcript, speakers = _identify_speaker_roles(
                formatted_transcript, speakers
            )

        logger.info("=== TRANSCRIPTION AGENT COMPLETE ===")
        return {
            "transcript": formatted_transcript,
            "transcript_plain": result.get("text"),
            "speaker_segments": speakers,
            "num_speakers": result.get("num_speakers", 0),
            "transcription_language": result.get("language"),
            "transcription_duration": result.get("duration"),
            "current_step": "transcription",
            "error": None,
        }

    except ContentValidationError:
        # Re-raise ContentValidationError to stop the workflow
        logger.error("Re-raising ContentValidationError to stop workflow")
        raise

    except Exception as e:
        logger.error(f"Transcription error: {type(e).__name__}: {str(e)}")
        return {
            "error": f"Transcription failed: {str(e)}",
            "error_type": "TranscriptionError",
            "error_count": state.get("error_count", 0) + 1,
            "current_step": "transcription",
        }


def _identify_speaker_roles(transcript: str, speakers: list[dict]) -> tuple[str, list[dict]]:
    """
    Use GPT to identify speaker roles and relabel the transcript.
    """
    import json

    try:
        openai_service = OpenAIService()

        # Ask GPT to identify roles
        response = openai_service.generate(
            prompt=SPEAKER_IDENTIFICATION_PROMPT.format(transcript=transcript),
            system_prompt="You are a helpful assistant that analyzes call transcripts. Return only valid JSON.",
        )

        # Parse the response
        # Clean up response in case it has markdown code blocks
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()

        role_mapping = json.loads(response)

        # Relabel the transcript
        updated_transcript = transcript
        updated_speakers = []

        for speaker in speakers:
            # Handle both int and float speaker IDs
            raw_id = speaker.get("speaker_id", 0)
            speaker_id = str(int(raw_id)) if isinstance(raw_id, (int, float)) else str(raw_id)
            role = role_mapping.get(speaker_id, f"Speaker {speaker_id}")

            # Update speaker info
            updated_speaker = speaker.copy()
            updated_speaker["role"] = role
            updated_speakers.append(updated_speaker)

        # Replace speaker labels in transcript - handle multiple formats
        for speaker_id, role in role_mapping.items():
            # Try both "Speaker 0" and "Speaker 0.0" formats
            updated_transcript = updated_transcript.replace(
                f"**Speaker {speaker_id}:**",
                f"**{role}:**"
            )
            updated_transcript = updated_transcript.replace(
                f"**Speaker {speaker_id}.0:**",
                f"**{role}:**"
            )

        return updated_transcript, updated_speakers

    except Exception:
        # If GPT fails, return original transcript
        return transcript, speakers
