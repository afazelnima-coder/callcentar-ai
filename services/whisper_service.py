import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError, APITimeoutError

from app.config import settings


class WhisperService:
    """Service for transcribing audio using OpenAI Whisper API."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.whisper_model
        self.chunk_size_bytes = settings.audio_chunk_size_mb * 1024 * 1024

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
    )
    def transcribe(self, file_path: str) -> dict:
        """
        Transcribe audio file using OpenAI Whisper API.

        Args:
            file_path: Path to the audio file

        Returns:
            dict with 'text', 'language', and optionally 'words' for timestamps
        """
        file_size = os.path.getsize(file_path)

        # Check if file needs chunking (Whisper limit is 25MB)
        if file_size > self.chunk_size_bytes:
            return self._transcribe_chunked(file_path)

        return self._transcribe_single(file_path)

    def _transcribe_single(self, file_path: str) -> dict:
        """Transcribe a single audio file."""
        with open(file_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                response_format="verbose_json",
            )

        return {
            "text": response.text,
            "language": response.language,
            "duration": response.duration,
            "words": getattr(response, "words", None),
        }

    def _transcribe_chunked(self, file_path: str) -> dict:
        """
        Transcribe large audio files by splitting into chunks.
        Uses pydub for audio manipulation.
        """
        from pydub import AudioSegment

        # Load audio file
        audio = AudioSegment.from_file(file_path)

        # Calculate chunk duration (based on approximate file size per minute)
        # Assuming ~1MB per minute of audio at standard quality
        chunk_duration_ms = (self.chunk_size_bytes / 1024 / 1024) * 60 * 1000

        chunks = []
        start = 0
        while start < len(audio):
            end = min(start + int(chunk_duration_ms), len(audio))
            chunks.append(audio[start:end])
            start = end

        # Transcribe each chunk
        transcripts = []
        for i, chunk in enumerate(chunks):
            # Export chunk to temporary file
            chunk_path = f"/tmp/chunk_{i}.mp3"
            chunk.export(chunk_path, format="mp3")

            try:
                result = self._transcribe_single(chunk_path)
                transcripts.append(result["text"])
            finally:
                # Clean up temp file
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)

        # Combine transcripts
        return {
            "text": " ".join(transcripts),
            "language": None,  # Can't reliably detect from chunks
            "duration": len(audio) / 1000,  # Convert ms to seconds
            "words": None,  # Timestamps not reliable across chunks
        }
