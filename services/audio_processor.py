import os
from typing import Optional
from pydub import AudioSegment
from pydub.utils import mediainfo


class AudioProcessor:
    """Service for processing and validating audio files."""

    SUPPORTED_FORMATS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}

    def __init__(self):
        pass

    def get_audio_info(self, file_path: str) -> dict:
        """
        Extract audio file information.

        Args:
            file_path: Path to the audio file

        Returns:
            dict with duration, sample_rate, channels, format
        """
        try:
            # Use pydub's mediainfo for detailed info
            info = mediainfo(file_path)

            return {
                "duration": float(info.get("duration", 0)),
                "sample_rate": int(info.get("sample_rate", 0)),
                "channels": int(info.get("channels", 0)),
                "format": info.get("format_name", "unknown"),
                "bit_rate": info.get("bit_rate"),
            }
        except Exception as e:
            # Fallback to pydub for basic info
            audio = AudioSegment.from_file(file_path)
            return {
                "duration": len(audio) / 1000,  # Convert ms to seconds
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "format": os.path.splitext(file_path)[1][1:],
                "bit_rate": None,
            }

    def is_valid_format(self, file_path: str) -> bool:
        """Check if the file format is supported."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS

    def convert_to_mp3(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert audio file to MP3 format.

        Args:
            file_path: Path to the input audio file
            output_path: Optional output path (defaults to same name with .mp3)

        Returns:
            Path to the converted file
        """
        if output_path is None:
            base = os.path.splitext(file_path)[0]
            output_path = f"{base}.mp3"

        audio = AudioSegment.from_file(file_path)
        audio.export(output_path, format="mp3")

        return output_path

    def get_duration_seconds(self, file_path: str) -> float:
        """Get the duration of an audio file in seconds."""
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000
