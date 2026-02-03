"""
Tests for schemas/metadata_schemas.py - Call metadata models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from schemas.metadata_schemas import CallMetadata


class TestCallMetadata:
    """Tests for CallMetadata model."""

    def test_valid_audio_metadata(self, sample_call_metadata):
        """Should create valid audio file metadata."""
        assert sample_call_metadata.file_name == "call_20240115_agent42.wav"
        assert sample_call_metadata.file_size_bytes == 5242880
        assert sample_call_metadata.file_format == "wav"
        assert sample_call_metadata.duration_seconds == 180.5
        assert sample_call_metadata.sample_rate == 44100
        assert sample_call_metadata.channels == 2

    def test_valid_text_metadata(self, sample_text_metadata):
        """Should create valid text file metadata."""
        assert sample_text_metadata.file_name == "transcript.txt"
        assert sample_text_metadata.file_format == "txt"
        assert sample_text_metadata.duration_seconds is None
        assert sample_text_metadata.sample_rate is None
        assert sample_text_metadata.channels is None

    def test_minimal_required_fields(self):
        """Should create metadata with only required fields."""
        metadata = CallMetadata(
            file_name="test.mp3",
            file_size_bytes=1024,
            file_format="mp3",
        )
        assert metadata.file_name == "test.mp3"
        assert metadata.file_size_bytes == 1024
        assert metadata.file_format == "mp3"

    def test_all_optional_fields_are_none_by_default(self):
        """All optional fields should default to None."""
        metadata = CallMetadata(
            file_name="test.wav",
            file_size_bytes=100,
            file_format="wav",
        )
        assert metadata.duration_seconds is None
        assert metadata.sample_rate is None
        assert metadata.channels is None
        assert metadata.call_id is None
        assert metadata.agent_id is None
        assert metadata.customer_id is None
        assert metadata.call_date is None
        assert metadata.call_type is None

    def test_with_call_context(self):
        """Should accept call context fields."""
        call_date = datetime(2024, 1, 15, 10, 30, 0)
        metadata = CallMetadata(
            file_name="call_20240115.wav",
            file_size_bytes=5000000,
            file_format="wav",
            duration_seconds=300.0,
            call_id="CALL-12345",
            agent_id="AGENT-42",
            customer_id="CUST-789",
            call_date=call_date,
            call_type="support",
        )
        assert metadata.call_id == "CALL-12345"
        assert metadata.agent_id == "AGENT-42"
        assert metadata.customer_id == "CUST-789"
        assert metadata.call_date == call_date
        assert metadata.call_type == "support"

    def test_missing_required_fields_fails(self):
        """Missing required fields should fail validation."""
        with pytest.raises(ValidationError):
            CallMetadata(
                file_name="test.wav",
                # Missing file_size_bytes and file_format
            )

    def test_accepts_various_formats(self):
        """Should accept various file format strings."""
        for fmt in ["wav", "mp3", "m4a", "flac", "ogg", "webm", "txt", "json"]:
            metadata = CallMetadata(
                file_name=f"test.{fmt}",
                file_size_bytes=100,
                file_format=fmt,
            )
            assert metadata.file_format == fmt

    def test_accepts_various_sample_rates(self):
        """Should accept various sample rates."""
        for rate in [8000, 16000, 22050, 44100, 48000]:
            metadata = CallMetadata(
                file_name="test.wav",
                file_size_bytes=100,
                file_format="wav",
                sample_rate=rate,
            )
            assert metadata.sample_rate == rate

    def test_accepts_various_channel_counts(self):
        """Should accept various channel counts."""
        for channels in [1, 2, 6]:
            metadata = CallMetadata(
                file_name="test.wav",
                file_size_bytes=100,
                file_format="wav",
                channels=channels,
            )
            assert metadata.channels == channels

    def test_accepts_float_duration(self):
        """Should accept float duration values."""
        metadata = CallMetadata(
            file_name="test.wav",
            file_size_bytes=100,
            file_format="wav",
            duration_seconds=123.456,
        )
        assert metadata.duration_seconds == 123.456

    def test_accepts_datetime_call_date(self):
        """Should accept datetime for call_date."""
        call_date = datetime.now()
        metadata = CallMetadata(
            file_name="test.wav",
            file_size_bytes=100,
            file_format="wav",
            call_date=call_date,
        )
        assert metadata.call_date == call_date
