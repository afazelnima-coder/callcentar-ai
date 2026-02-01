from deepgram import DeepgramClient
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


class DeepgramService:
    """Service for transcribing audio using Deepgram API with speaker diarization."""

    def __init__(self):
        self.client = DeepgramClient(api_key=settings.deepgram_api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    def transcribe(self, file_path: str) -> dict:
        """
        Transcribe audio file using Deepgram API with speaker diarization.
        """
        # Read the audio file
        with open(file_path, "rb") as audio_file:
            buffer_data = audio_file.read()

        # Transcribe with diarization options
        response = self.client.listen.v1.media.transcribe_file(
            request=buffer_data,
            model="nova-2",
            smart_format=True,
            diarize=True,
            punctuate=True,
            utterances=True,
        )

        # Process the response
        return self._process_response(response)

    def _process_response(self, response) -> dict:
        """Process Deepgram response into structured format with speaker labels."""
        # Handle the response structure
        results = response.results if hasattr(response, "results") else response

        # Get channels
        channels = getattr(results, "channels", None) or []

        # Get plain text first (fallback)
        plain_text = ""
        if channels:
            alternatives = getattr(channels[0], "alternatives", None) or []
            if alternatives:
                plain_text = getattr(alternatives[0], "transcript", "") or ""

        if not plain_text:
            raise ValueError("Deepgram returned empty transcript. Check audio quality.")

        # Get utterances with speaker info
        utterances = getattr(results, "utterances", None) or []

        # Build formatted transcript with speaker labels
        formatted_lines = []
        speakers = []
        current_speaker = None

        if utterances:
            for utterance in utterances:
                # Convert speaker_id to int to avoid float formatting (0.0 -> 0)
                speaker_id = int(getattr(utterance, "speaker", 0))
                text = getattr(utterance, "transcript", "")
                start = getattr(utterance, "start", 0)
                end = getattr(utterance, "end", 0)

                speaker_label = f"Speaker {speaker_id}"

                speakers.append({
                    "speaker": speaker_label,
                    "speaker_id": speaker_id,
                    "text": text,
                    "start": start,
                    "end": end,
                })

                # Add to formatted transcript
                if speaker_id != current_speaker:
                    formatted_lines.append(f"\n**{speaker_label}:**")
                    current_speaker = speaker_id

                formatted_lines.append(text)

            formatted_transcript = "\n".join(formatted_lines).strip()
        else:
            # No diarization - use plain text
            formatted_transcript = plain_text

        # Get metadata
        metadata = getattr(results, "metadata", None)
        duration = getattr(metadata, "duration", 0) if metadata else 0

        # Get detected language
        language = None
        if channels:
            language = getattr(channels[0], "detected_language", None)

        num_speakers = len(set(s["speaker_id"] for s in speakers)) if speakers else 1

        return {
            "text": plain_text,
            "formatted_transcript": formatted_transcript,
            "speakers": speakers,
            "duration": duration,
            "language": language,
            "num_speakers": num_speakers,
        }
