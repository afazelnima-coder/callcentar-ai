import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError, APITimeoutError

from app.config import settings


# Whisper API limit is 25MB
MAX_WHISPER_FILE_SIZE_MB = 25


class WhisperService:
    """Service for transcribing audio using OpenAI Whisper API."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.whisper_model
        self.max_file_size_bytes = MAX_WHISPER_FILE_SIZE_MB * 1024 * 1024

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
            dict with 'text', 'language', 'duration'

        Raises:
            ValueError: If file exceeds 25MB limit
        """
        file_size = os.path.getsize(file_path)

        # Check file size (Whisper API limit is 25MB)
        if file_size > self.max_file_size_bytes:
            size_mb = file_size / (1024 * 1024)
            raise ValueError(
                f"Audio file is {size_mb:.1f}MB, which exceeds the 25MB limit. "
                "Please use a shorter audio file or compress it."
            )

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
