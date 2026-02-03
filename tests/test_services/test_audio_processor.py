"""
Tests for services/audio_processor.py - Audio file processing.
"""

import pytest
from unittest.mock import patch, MagicMock

from services.audio_processor import AudioProcessor


class TestAudioProcessorInit:
    """Tests for AudioProcessor initialization."""

    def test_initializes_successfully(self):
        """Should initialize without errors."""
        processor = AudioProcessor()
        assert processor is not None

    def test_has_supported_formats(self):
        """Should have supported formats defined."""
        assert AudioProcessor.SUPPORTED_FORMATS == {
            ".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"
        }


class TestAudioProcessorGetAudioInfo:
    """Tests for get_audio_info method."""

    @patch("services.audio_processor.MutagenFile")
    def test_extracts_audio_info(self, mock_mutagen):
        """Should extract audio information from file."""
        mock_audio = MagicMock()
        mock_audio.info.length = 180.5
        mock_audio.info.sample_rate = 44100
        mock_audio.info.channels = 2
        mock_audio.info.bitrate = 320000
        mock_mutagen.return_value = mock_audio

        processor = AudioProcessor()
        result = processor.get_audio_info("/path/to/audio.mp3")

        assert result["duration"] == 180.5
        assert result["sample_rate"] == 44100
        assert result["channels"] == 2
        assert result["format"] == "mp3"
        assert result["bit_rate"] == 320000

    @patch("services.audio_processor.MutagenFile")
    def test_handles_unidentified_file(self, mock_mutagen):
        """Should handle file that mutagen can't identify."""
        mock_mutagen.return_value = None

        processor = AudioProcessor()
        result = processor.get_audio_info("/path/to/unknown.xyz")

        assert result["duration"] == 0
        assert result["sample_rate"] == 0
        assert result["channels"] == 0
        assert result["format"] == "xyz"
        assert result["bit_rate"] is None

    @patch("services.audio_processor.MutagenFile")
    def test_handles_missing_attributes(self, mock_mutagen):
        """Should handle files with missing audio attributes."""
        mock_audio = MagicMock(spec=[])
        mock_audio.info = MagicMock(spec=["length"])
        mock_audio.info.length = 60.0
        mock_mutagen.return_value = mock_audio

        processor = AudioProcessor()
        result = processor.get_audio_info("/path/to/audio.ogg")

        assert result["duration"] == 60.0
        assert result["sample_rate"] == 0
        assert result["channels"] == 0

    @patch("services.audio_processor.MutagenFile")
    def test_handles_exception(self, mock_mutagen):
        """Should return basic info on exception."""
        mock_mutagen.side_effect = Exception("File read error")

        processor = AudioProcessor()
        result = processor.get_audio_info("/path/to/error.wav")

        assert result["duration"] == 0
        assert result["sample_rate"] == 0
        assert result["channels"] == 0
        assert result["format"] == "wav"
        assert result["bit_rate"] is None


class TestAudioProcessorIsValidFormat:
    """Tests for is_valid_format method."""

    def test_accepts_wav(self):
        """Should accept .wav files."""
        processor = AudioProcessor()
        assert processor.is_valid_format("/path/to/audio.wav") is True

    def test_accepts_mp3(self):
        """Should accept .mp3 files."""
        processor = AudioProcessor()
        assert processor.is_valid_format("/path/to/audio.mp3") is True

    def test_accepts_m4a(self):
        """Should accept .m4a files."""
        processor = AudioProcessor()
        assert processor.is_valid_format("/path/to/audio.m4a") is True

    def test_accepts_flac(self):
        """Should accept .flac files."""
        processor = AudioProcessor()
        assert processor.is_valid_format("/path/to/audio.flac") is True

    def test_accepts_ogg(self):
        """Should accept .ogg files."""
        processor = AudioProcessor()
        assert processor.is_valid_format("/path/to/audio.ogg") is True

    def test_accepts_webm(self):
        """Should accept .webm files."""
        processor = AudioProcessor()
        assert processor.is_valid_format("/path/to/audio.webm") is True

    def test_rejects_txt(self):
        """Should reject .txt files."""
        processor = AudioProcessor()
        assert processor.is_valid_format("/path/to/transcript.txt") is False

    def test_rejects_pdf(self):
        """Should reject .pdf files."""
        processor = AudioProcessor()
        assert processor.is_valid_format("/path/to/document.pdf") is False

    def test_rejects_unknown_format(self):
        """Should reject unknown formats."""
        processor = AudioProcessor()
        assert processor.is_valid_format("/path/to/file.xyz") is False

    def test_case_insensitive(self):
        """Should be case insensitive for extensions."""
        processor = AudioProcessor()
        assert processor.is_valid_format("/path/to/AUDIO.WAV") is True
        assert processor.is_valid_format("/path/to/audio.MP3") is True


class TestAudioProcessorGetDurationSeconds:
    """Tests for get_duration_seconds method."""

    @patch("services.audio_processor.MutagenFile")
    def test_returns_duration(self, mock_mutagen):
        """Should return duration from audio info."""
        mock_audio = MagicMock()
        mock_audio.info.length = 120.5
        mock_mutagen.return_value = mock_audio

        processor = AudioProcessor()
        result = processor.get_duration_seconds("/path/to/audio.wav")

        assert result == 120.5

    @patch("services.audio_processor.MutagenFile")
    def test_returns_zero_on_error(self, mock_mutagen):
        """Should return 0 if duration not available."""
        mock_mutagen.side_effect = Exception("Error")

        processor = AudioProcessor()
        result = processor.get_duration_seconds("/path/to/audio.wav")

        assert result == 0


class TestAudioProcessorGetFileSizeMb:
    """Tests for get_file_size_mb method."""

    @patch("os.path.getsize")
    def test_returns_size_in_mb(self, mock_getsize):
        """Should return file size in megabytes."""
        mock_getsize.return_value = 5 * 1024 * 1024  # 5 MB

        processor = AudioProcessor()
        result = processor.get_file_size_mb("/path/to/audio.wav")

        assert result == 5.0

    @patch("os.path.getsize")
    def test_handles_fractional_mb(self, mock_getsize):
        """Should handle fractional megabyte sizes."""
        mock_getsize.return_value = 2.5 * 1024 * 1024  # 2.5 MB

        processor = AudioProcessor()
        result = processor.get_file_size_mb("/path/to/audio.wav")

        assert result == 2.5

    @patch("os.path.getsize")
    def test_handles_small_files(self, mock_getsize):
        """Should handle files smaller than 1 MB."""
        mock_getsize.return_value = 512 * 1024  # 0.5 MB

        processor = AudioProcessor()
        result = processor.get_file_size_mb("/path/to/audio.wav")

        assert result == 0.5
