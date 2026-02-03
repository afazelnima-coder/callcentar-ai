"""
Tests for services/guardrails_service.py - Content validation.
"""

import pytest
from unittest.mock import patch, MagicMock

from services.guardrails_service import (
    CallCenterContentValidator,
    GuardrailsService,
)
from guardrails.validators import PassResult, FailResult


class TestCallCenterContentValidator:
    """Tests for CallCenterContentValidator."""

    def test_fails_on_empty_content(self):
        """Should fail when content is empty."""
        validator = CallCenterContentValidator()
        result = validator.validate("", {})

        assert isinstance(result, FailResult)
        assert "empty" in result.error_message.lower()

    def test_fails_on_none_content(self):
        """Should fail when content is None."""
        validator = CallCenterContentValidator()
        result = validator.validate(None, {})

        assert isinstance(result, FailResult)

    def test_fails_on_non_string_content(self):
        """Should fail when content is not a string."""
        validator = CallCenterContentValidator()
        result = validator.validate(12345, {})

        assert isinstance(result, FailResult)

    def test_fails_on_short_content(self):
        """Should fail when content is too short."""
        validator = CallCenterContentValidator()
        result = validator.validate("Too short", {})

        assert isinstance(result, FailResult)
        assert "too short" in result.error_message.lower()

    def test_passes_with_agent_indicator(self):
        """Should pass when content has agent: indicator."""
        validator = CallCenterContentValidator()
        content = """
        Agent: Hello, thank you for calling ABC Company. How can I help you today?
        Customer: Hi, I'm having an issue with my account.
        Agent: I'd be happy to help you with that. Can I have your account number?
        """ + ("x" * 50)  # Ensure minimum length

        result = validator.validate(content, {})

        assert isinstance(result, PassResult)

    def test_passes_with_customer_indicator(self):
        """Should pass when content has customer: indicator."""
        validator = CallCenterContentValidator()
        content = """
        Customer: Hello, I need help with my order.
        Representative: Of course, I'll be happy to assist you today.
        """ + ("x" * 50)

        result = validator.validate(content, {})

        assert isinstance(result, PassResult)

    def test_passes_with_speaker_indicators(self):
        """Should pass when content has **Speaker indicators."""
        validator = CallCenterContentValidator()
        content = """
        **Speaker 0:** Thank you for calling, how may I assist you?
        **Speaker 1:** I have a question about my bill.
        """ + ("x" * 50)

        result = validator.validate(content, {})

        assert isinstance(result, PassResult)

    @patch("services.guardrails_service.OpenAIService")
    def test_uses_llm_for_ambiguous_content(self, mock_openai_class):
        """Should use LLM to validate ambiguous content."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate.return_value = "VALID"

        validator = CallCenterContentValidator()
        content = "Hello there, I'm calling about my issue. " * 10  # Long enough, no indicators

        result = validator.validate(content, {})

        assert isinstance(result, PassResult)
        mock_service.generate.assert_called_once()

    @patch("services.guardrails_service.OpenAIService")
    def test_fails_on_llm_invalid_response(self, mock_openai_class):
        """Should fail when LLM says content is invalid."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate.return_value = "INVALID: This is a podcast transcript, not a call center conversation"

        validator = CallCenterContentValidator()
        content = "Welcome to the podcast, today we discuss..." * 10

        result = validator.validate(content, {})

        assert isinstance(result, FailResult)
        assert "podcast" in result.error_message.lower()

    @patch("services.guardrails_service.OpenAIService")
    def test_handles_llm_exception(self, mock_openai_class):
        """Should fail gracefully when LLM throws exception."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate.side_effect = Exception("API error")

        validator = CallCenterContentValidator()
        content = "Some content without clear indicators. " * 10

        result = validator.validate(content, {})

        assert isinstance(result, FailResult)
        assert "failed" in result.error_message.lower()

    @patch("services.guardrails_service.OpenAIService")
    def test_truncates_long_content_for_llm(self, mock_openai_class):
        """Should truncate very long content before sending to LLM."""
        mock_service = MagicMock()
        mock_openai_class.return_value = mock_service
        mock_service.generate.return_value = "VALID"

        validator = CallCenterContentValidator()
        content = "x" * 5000  # More than 3000 characters

        validator.validate(content, {})

        call_args = mock_service.generate.call_args
        prompt = call_args.kwargs.get("prompt") or call_args[0][0]
        # The prompt should contain truncated text (3000 chars max)
        assert len(prompt) < 5000


class TestGuardrailsService:
    """Tests for GuardrailsService."""

    @patch("services.guardrails_service.Guard")
    def test_initializes_with_guard(self, mock_guard_class):
        """Should initialize with Guard and validator."""
        mock_guard = MagicMock()
        mock_guard_class.return_value = mock_guard

        service = GuardrailsService()

        mock_guard.use.assert_called_once()

    @patch("services.guardrails_service.Guard")
    def test_validate_returns_true_on_success(self, mock_guard_class):
        """Should return (True, message) when validation passes."""
        mock_guard = MagicMock()
        mock_guard_class.return_value = mock_guard
        mock_guard.use.return_value = mock_guard
        mock_guard.validate.return_value = None  # No exception means success

        service = GuardrailsService()
        is_valid, message = service.validate_call_center_content("Valid content")

        assert is_valid is True
        assert "validated" in message.lower()

    @patch("services.guardrails_service.Guard")
    def test_validate_returns_false_on_failure(self, mock_guard_class):
        """Should return (False, reason) when validation fails."""
        mock_guard = MagicMock()
        mock_guard_class.return_value = mock_guard
        mock_guard.use.return_value = mock_guard
        mock_guard.validate.side_effect = Exception("Validation failed for field: Not a call transcript")

        service = GuardrailsService()
        is_valid, message = service.validate_call_center_content("Invalid content")

        assert is_valid is False
        assert len(message) > 0

    @patch("services.guardrails_service.Guard")
    def test_cleans_error_message(self, mock_guard_class):
        """Should clean up verbose error messages."""
        mock_guard = MagicMock()
        mock_guard_class.return_value = mock_guard
        mock_guard.use.return_value = mock_guard
        mock_guard.validate.side_effect = Exception(
            "Validation failed for field with name `value`: This is the actual error"
        )

        service = GuardrailsService()
        is_valid, message = service.validate_call_center_content("Content")

        assert is_valid is False
        # Should extract just the relevant part
        assert "This is the actual error" in message or "actual error" in message.lower()
