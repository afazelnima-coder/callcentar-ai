"""
Tests for agents/intake_agent.py
"""

import pytest
from unittest.mock import patch, MagicMock
import os

from agents.intake_agent import (
    call_intake_node,
    validate_transcript_content,
    ContentValidationError,
)


class TestCallIntakeNode:
    """Tests for call_intake_node function."""

    def test_returns_error_when_no_file_path(self):
        """Should return error when input_file_path is missing."""
        state = {}
        result = call_intake_node(state)

        assert result["error"] == "No input file path provided"
        assert result["error_type"] == "MissingInputError"
        assert result["file_validated"] is False

    def test_returns_error_when_file_not_found(self, tmp_path):
        """Should return error when file doesn't exist."""
        state = {"input_file_path": str(tmp_path / "nonexistent.wav")}
        result = call_intake_node(state)

        assert "File not found" in result["error"]
        assert result["error_type"] == "FileNotFoundError"
        assert result["file_validated"] is False

    def test_returns_error_when_file_too_large(self, tmp_path):
        """Should return error when file exceeds size limit."""
        # Create a large file path (we'll mock the size check)
        large_file = tmp_path / "large.wav"
        large_file.write_bytes(b"x" * 100)  # Small actual file

        with patch("os.path.getsize") as mock_size:
            # Simulate a file > 100MB
            mock_size.return_value = 150 * 1024 * 1024

            state = {"input_file_path": str(large_file)}
            result = call_intake_node(state)

            assert "File too large" in result["error"]
            assert result["error_type"] == "FileTooLargeError"
            assert result["file_validated"] is False

    def test_returns_error_for_unsupported_format(self, tmp_path):
        """Should return error for unsupported file formats."""
        unsupported_file = tmp_path / "file.xyz"
        unsupported_file.write_text("content")

        state = {"input_file_path": str(unsupported_file)}
        result = call_intake_node(state)

        assert "Unsupported file format" in result["error"]
        assert result["error_type"] == "UnsupportedFormatError"
        assert result["file_validated"] is False

    @patch("agents.intake_agent.AudioProcessor")
    def test_processes_audio_file_successfully(self, mock_audio_processor, tmp_path):
        """Should process valid audio files correctly."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 100)

        # Mock audio processor
        mock_processor = MagicMock()
        mock_processor.get_audio_info.return_value = {
            "duration": 120.5,
            "sample_rate": 44100,
            "channels": 2,
        }
        mock_audio_processor.return_value = mock_processor

        state = {"input_file_path": str(audio_file)}
        result = call_intake_node(state)

        assert result["file_validated"] is True
        assert result["has_audio"] is True
        assert result["input_file_type"] == "audio"
        assert result["metadata"].duration_seconds == 120.5
        assert result["error"] is None

    @patch("agents.intake_agent._validate_call_center_content")
    def test_processes_text_file_successfully(self, mock_validate, tmp_path):
        """Should process valid text files correctly."""
        text_file = tmp_path / "transcript.txt"
        text_file.write_text("Agent: Hello\nCustomer: Hi")

        # Mock validation to pass
        mock_validate.return_value = (True, "Valid call center content")

        state = {"input_file_path": str(text_file)}
        result = call_intake_node(state)

        assert result["file_validated"] is True
        assert result["has_audio"] is False
        assert result["input_file_type"] == "transcript"
        assert result["transcript"] is not None
        assert result["error"] is None

    @patch("agents.intake_agent._validate_call_center_content")
    def test_raises_content_validation_error_for_invalid_content(
        self, mock_validate, tmp_path
    ):
        """Should raise ContentValidationError for invalid content."""
        text_file = tmp_path / "invalid.txt"
        text_file.write_text("This is not a call center transcript")

        # Mock validation to fail
        mock_validate.return_value = (False, "Not a call center conversation")

        state = {"input_file_path": str(text_file)}

        with pytest.raises(ContentValidationError) as exc_info:
            call_intake_node(state)

        assert "Invalid content" in str(exc_info.value)

    @pytest.mark.parametrize(
        "extension,expected_type",
        [
            (".wav", "audio"),
            (".mp3", "audio"),
            (".m4a", "audio"),
            (".flac", "audio"),
            (".ogg", "audio"),
        ],
    )
    @patch("agents.intake_agent.AudioProcessor")
    def test_supports_various_audio_formats(
        self, mock_audio_processor, extension, expected_type, tmp_path
    ):
        """Should support various audio file formats."""
        audio_file = tmp_path / f"test{extension}"
        audio_file.write_bytes(b"audio data")

        mock_processor = MagicMock()
        mock_processor.get_audio_info.return_value = {
            "duration": 60.0,
            "sample_rate": 44100,
            "channels": 1,
        }
        mock_audio_processor.return_value = mock_processor

        state = {"input_file_path": str(audio_file)}
        result = call_intake_node(state)

        assert result["input_file_type"] == expected_type
        assert result["file_validated"] is True

    @patch("agents.intake_agent._validate_call_center_content")
    def test_supports_json_format(self, mock_validate, tmp_path):
        """Should support JSON file format as text."""
        json_file = tmp_path / "transcript.json"
        json_file.write_text('{"transcript": "Agent: Hello"}')

        mock_validate.return_value = (True, "Valid")

        state = {"input_file_path": str(json_file)}
        result = call_intake_node(state)

        assert result["input_file_type"] == "transcript"
        assert result["file_validated"] is True


class TestValidateTranscriptContent:
    """Tests for validate_transcript_content function."""

    @patch("agents.intake_agent._validate_call_center_content")
    def test_calls_internal_validation(self, mock_validate):
        """Should call the internal validation function."""
        mock_validate.return_value = (True, "Valid content")

        result = validate_transcript_content("Some transcript")

        mock_validate.assert_called_once_with("Some transcript")
        assert result == (True, "Valid content")

    @patch("agents.intake_agent._validate_call_center_content")
    def test_returns_validation_result(self, mock_validate):
        """Should return the validation result tuple."""
        mock_validate.return_value = (False, "Invalid content")

        is_valid, reason = validate_transcript_content("Bad content")

        assert is_valid is False
        assert reason == "Invalid content"


class TestContentValidationError:
    """Tests for ContentValidationError exception."""

    def test_can_be_raised(self):
        """Should be raisable with a message."""
        with pytest.raises(ContentValidationError) as exc_info:
            raise ContentValidationError("Test error message")

        assert "Test error message" in str(exc_info.value)

    def test_inherits_from_exception(self):
        """Should inherit from Exception."""
        error = ContentValidationError("Test")
        assert isinstance(error, Exception)
