import os
from mutagen import File as MutagenFile


class AudioProcessor:
    """Service for processing and validating audio files using mutagen (no ffmpeg required)."""

    SUPPORTED_FORMATS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}

    def __init__(self):
        pass

    def get_audio_info(self, file_path: str) -> dict:
        """
        Extract audio file information using mutagen.

        Args:
            file_path: Path to the audio file

        Returns:
            dict with duration, sample_rate, channels, format
        """
        try:
            audio = MutagenFile(file_path)

            if audio is None:
                # Mutagen couldn't identify the file type
                return {
                    "duration": 0,
                    "sample_rate": 0,
                    "channels": 0,
                    "format": os.path.splitext(file_path)[1][1:],
                    "bit_rate": None,
                }

            # Get duration (available on all mutagen file types)
            duration = audio.info.length if hasattr(audio.info, "length") else 0

            # Get sample rate and channels based on file type
            sample_rate = getattr(audio.info, "sample_rate", 0)
            channels = getattr(audio.info, "channels", 0)
            bit_rate = getattr(audio.info, "bitrate", None)

            return {
                "duration": duration,
                "sample_rate": sample_rate,
                "channels": channels,
                "format": os.path.splitext(file_path)[1][1:],
                "bit_rate": bit_rate,
            }

        except Exception:
            # Return basic info on error
            return {
                "duration": 0,
                "sample_rate": 0,
                "channels": 0,
                "format": os.path.splitext(file_path)[1][1:],
                "bit_rate": None,
            }

    def is_valid_format(self, file_path: str) -> bool:
        """Check if the file format is supported."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS

    def get_duration_seconds(self, file_path: str) -> float:
        """Get the duration of an audio file in seconds."""
        info = self.get_audio_info(file_path)
        return info.get("duration", 0)

    def get_file_size_mb(self, file_path: str) -> float:
        """Get file size in megabytes."""
        return os.path.getsize(file_path) / (1024 * 1024)
