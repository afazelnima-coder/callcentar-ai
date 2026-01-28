import os
from deepgram import DeepgramClient, PrerecordedOptions, FileSource
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


class DeepgramService:
    """Service for transcribing audio using Deepgram API with speaker diarization."""

    def __init__(self):
        self.client = DeepgramClient(settings.deepgram_api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    def transcribe(self, file_path: str) -> dict:
        """
        Transcribe audio file using Deepgram API with speaker diarization.

        Args:
            file_path: Path to the audio file

        Returns:
            dict with:
                - 'text': Full transcript with speaker labels
                - 'speakers': List of speaker segments
                - 'duration': Audio duration in seconds
                - 'language': Detected language
        """
        # Read the audio file
        with open(file_path, "rb") as audio_file:
            buffer_data = audio_file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        # Configure options with diarization
        options = PrerecordedOptions(
            model="nova-2",  # Latest Deepgram model
            smart_format=True,  # Better formatting
            diarize=True,  # Enable speaker diarization
            punctuate=True,  # Add punctuation
            utterances=True,  # Get utterance-level results
        )

        # Transcribe
        response = self.client.listen.rest.v("1").transcribe_file(payload, options)

        # Process the response
        return self._process_response(response)

    def _process_response(self, response) -> dict:
        """Process Deepgram response into structured format with speaker labels."""
        result = response.results

        # Get the main transcript
        channels = result.channels
        if not channels:
            return {
                "text": "",
                "formatted_transcript": "",
                "speakers": [],
                "duration": 0,
                "language": None,
            }

        # Get utterances with speaker info
        utterances = result.utterances or []

        # Build formatted transcript with speaker labels
        formatted_lines = []
        speakers = []
        current_speaker = None

        for utterance in utterances:
            speaker_id = utterance.speaker
            text = utterance.transcript
            start = utterance.start
            end = utterance.end

            # Map speaker IDs to roles (0 = Agent, 1 = Customer typically)
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
                formatted_lines.append(f"\n{speaker_label}:")
                current_speaker = speaker_id

            formatted_lines.append(f"  {text}")

        # Get plain text from first alternative
        plain_text = ""
        if channels and channels[0].alternatives:
            plain_text = channels[0].alternatives[0].transcript

        # Get metadata
        duration = result.metadata.duration if result.metadata else 0
        language = None
        if channels and channels[0].detected_language:
            language = channels[0].detected_language

        formatted_transcript = "\n".join(formatted_lines).strip()

        return {
            "text": plain_text,
            "formatted_transcript": formatted_transcript,
            "speakers": speakers,
            "duration": duration,
            "language": language,
            "num_speakers": len(set(s["speaker_id"] for s in speakers)),
        }
