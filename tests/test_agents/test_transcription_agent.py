"""
Tests for agents/transcription_agent.py - Audio transcription.
"""

import pytest
from unittest.mock import patch, MagicMock

from agents.transcription_agent import transcription_node, _identify_speaker_roles
from agents.intake_agent import ContentValidationError


class TestTranscriptionNode:
    """Tests for transcription_node function."""

    def test_skips_when_transcript_exists(self, sample_transcript):
        """Should skip transcription when transcript already exists."""
        state = {
            "transcript": sample_transcript,
            "input_file_path": "/path/to/audio.wav",
        }
        result = transcription_node(state)

        assert result["current_step"] == "transcription"
        assert "transcript" not in result  # Should not override existing

    def test_error_when_no_file_path(self):
        """Should return error when no file path provided."""
        state = {
            "transcript": None,
            "input_file_path": None,
            "error_count": 0,
        }
        result = transcription_node(state)

        assert "No input file path" in result["error"]
        assert result["error_type"] == "MissingInputError"
        assert result["error_count"] == 1
        assert result["current_step"] == "transcription"

    def test_error_when_file_path_missing(self):
        """Should return error when file path key is missing."""
        state = {"transcript": None, "error_count": 0}
        result = transcription_node(state)

        assert "No input file path" in result["error"]
        assert result["error_type"] == "MissingInputError"

    @patch("agents.transcription_agent.validate_transcript_content")
    @patch("agents.transcription_agent.DeepgramService")
    def test_successful_transcription(
        self, mock_deepgram_class, mock_validate, sample_transcript
    ):
        """Should transcribe audio successfully."""
        # Setup mocks
        mock_service = MagicMock()
        mock_deepgram_class.return_value = mock_service
        mock_service.transcribe.return_value = {
            "formatted_transcript": sample_transcript,
            "text": "Plain text version",
            "speakers": [],
            "num_speakers": 2,
            "language": "en",
            "duration": 180.5,
        }
        mock_validate.return_value = (True, "Valid call center conversation")

        state = {
            "transcript": None,
            "input_file_path": "/path/to/audio.wav",
            "error_count": 0,
        }
        result = transcription_node(state)

        assert result["transcript"] == sample_transcript
        assert result["transcript_plain"] == "Plain text version"
        assert result["num_speakers"] == 2
        assert result["transcription_language"] == "en"
        assert result["transcription_duration"] == 180.5
        assert result["current_step"] == "transcription"
        assert result["error"] is None

    @patch("agents.transcription_agent.validate_transcript_content")
    @patch("agents.transcription_agent.DeepgramService")
    def test_raises_content_validation_error(
        self, mock_deepgram_class, mock_validate
    ):
        """Should raise ContentValidationError when content is invalid."""
        mock_service = MagicMock()
        mock_deepgram_class.return_value = mock_service
        mock_service.transcribe.return_value = {
            "formatted_transcript": "Invalid content that is not a call",
            "text": "Invalid content",
            "speakers": [],
            "num_speakers": 0,
        }
        mock_validate.return_value = (False, "This is not a call center conversation")

        state = {
            "transcript": None,
            "input_file_path": "/path/to/audio.wav",
        }

        with pytest.raises(ContentValidationError) as exc_info:
            transcription_node(state)

        assert "Invalid audio content" in str(exc_info.value)

    @patch("agents.transcription_agent._identify_speaker_roles")
    @patch("agents.transcription_agent.validate_transcript_content")
    @patch("agents.transcription_agent.DeepgramService")
    def test_identifies_speaker_roles(
        self, mock_deepgram_class, mock_validate, mock_identify_roles, sample_transcript
    ):
        """Should identify speaker roles when multiple speakers detected."""
        mock_service = MagicMock()
        mock_deepgram_class.return_value = mock_service
        mock_service.transcribe.return_value = {
            "formatted_transcript": sample_transcript,
            "text": "Plain text",
            "speakers": [
                {"speaker_id": 0, "text": "Hello"},
                {"speaker_id": 1, "text": "Hi"},
            ],
            "num_speakers": 2,
        }
        mock_validate.return_value = (True, "Valid")
        mock_identify_roles.return_value = (
            sample_transcript.replace("Speaker 0", "Agent"),
            [{"speaker_id": 0, "role": "Agent"}, {"speaker_id": 1, "role": "Customer"}],
        )

        state = {
            "transcript": None,
            "input_file_path": "/path/to/audio.wav",
        }
        result = transcription_node(state)

        mock_identify_roles.assert_called_once()
        assert result["current_step"] == "transcription"

    @patch("agents.transcription_agent.validate_transcript_content")
    @patch("agents.transcription_agent.DeepgramService")
    def test_handles_transcription_exception(self, mock_deepgram_class, mock_validate):
        """Should handle transcription exceptions gracefully."""
        mock_service = MagicMock()
        mock_deepgram_class.return_value = mock_service
        mock_service.transcribe.side_effect = Exception("API error")

        state = {
            "transcript": None,
            "input_file_path": "/path/to/audio.wav",
            "error_count": 0,
        }
        result = transcription_node(state)

        assert "Transcription failed" in result["error"]
        assert result["error_type"] == "TranscriptionError"
        assert result["error_count"] == 1
        assert result["current_step"] == "transcription"

    @patch("agents.transcription_agent.validate_transcript_content")
    @patch("agents.transcription_agent.DeepgramService")
    def test_increments_error_count(self, mock_deepgram_class, mock_validate):
        """Should increment existing error count."""
        mock_service = MagicMock()
        mock_deepgram_class.return_value = mock_service
        mock_service.transcribe.side_effect = Exception("API error")

        state = {
            "transcript": None,
            "input_file_path": "/path/to/audio.wav",
            "error_count": 2,
        }
        result = transcription_node(state)

        assert result["error_count"] == 3

    @patch("agents.transcription_agent.validate_transcript_content")
    @patch("agents.transcription_agent.DeepgramService")
    def test_uses_text_fallback_for_transcript(
        self, mock_deepgram_class, mock_validate
    ):
        """Should fallback to text when formatted_transcript not available."""
        mock_service = MagicMock()
        mock_deepgram_class.return_value = mock_service
        mock_service.transcribe.return_value = {
            "formatted_transcript": None,
            "text": "Plain text transcript",
            "speakers": [],
            "num_speakers": 1,
        }
        mock_validate.return_value = (True, "Valid")

        state = {
            "transcript": None,
            "input_file_path": "/path/to/audio.wav",
        }
        result = transcription_node(state)

        assert result["transcript"] == "Plain text transcript"


class TestIdentifySpeakerRoles:
    """Tests for _identify_speaker_roles helper function."""

    @patch("agents.transcription_agent.OpenAIService")
    def test_identifies_roles_successfully(self, mock_openai_class):
        """Should identify and relabel speaker roles."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate.return_value = '{"0": "Agent", "1": "Customer"}'

        transcript = "**Speaker 0:** Hello\n**Speaker 1:** Hi"
        speakers = [{"speaker_id": 0}, {"speaker_id": 1}]

        updated_transcript, updated_speakers = _identify_speaker_roles(
            transcript, speakers
        )

        assert "**Agent:**" in updated_transcript
        assert "**Customer:**" in updated_transcript
        assert updated_speakers[0]["role"] == "Agent"
        assert updated_speakers[1]["role"] == "Customer"

    @patch("agents.transcription_agent.OpenAIService")
    def test_handles_markdown_code_blocks(self, mock_openai_class):
        """Should handle GPT response wrapped in markdown code blocks."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate.return_value = '```json\n{"0": "Agent", "1": "Customer"}\n```'

        transcript = "**Speaker 0:** Hello"
        speakers = [{"speaker_id": 0}]

        updated_transcript, updated_speakers = _identify_speaker_roles(
            transcript, speakers
        )

        assert "**Agent:**" in updated_transcript

    @patch("agents.transcription_agent.OpenAIService")
    def test_handles_float_speaker_ids(self, mock_openai_class):
        """Should handle float speaker IDs from Deepgram."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate.return_value = '{"0": "Agent", "1": "Customer"}'

        transcript = "**Speaker 0.0:** Hello"
        speakers = [{"speaker_id": 0.0}]

        updated_transcript, updated_speakers = _identify_speaker_roles(
            transcript, speakers
        )

        assert "**Agent:**" in updated_transcript

    @patch("agents.transcription_agent.OpenAIService")
    def test_returns_original_on_exception(self, mock_openai_class):
        """Should return original transcript on any exception."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate.side_effect = Exception("API error")

        original_transcript = "**Speaker 0:** Hello"
        original_speakers = [{"speaker_id": 0}]

        updated_transcript, updated_speakers = _identify_speaker_roles(
            original_transcript, original_speakers
        )

        assert updated_transcript == original_transcript
        assert updated_speakers == original_speakers

    @patch("agents.transcription_agent.OpenAIService")
    def test_returns_original_on_invalid_json(self, mock_openai_class):
        """Should return original transcript when JSON is invalid."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate.return_value = "not valid json"

        original_transcript = "**Speaker 0:** Hello"
        original_speakers = [{"speaker_id": 0}]

        updated_transcript, updated_speakers = _identify_speaker_roles(
            original_transcript, original_speakers
        )

        assert updated_transcript == original_transcript
        assert updated_speakers == original_speakers
