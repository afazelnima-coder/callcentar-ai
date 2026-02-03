"""
Tests for services/openai_service.py - OpenAI API wrapper.
"""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel

from services.openai_service import OpenAIService


class MockResponse(BaseModel):
    """Simple model for testing structured output."""
    message: str
    count: int


class TestOpenAIServiceGenerate:
    """Tests for OpenAIService.generate method."""

    @patch("services.openai_service.OpenAI")
    @patch("services.openai_service.settings")
    def test_generates_text_with_prompt(self, mock_settings, mock_openai_class):
        """Should generate text from prompt."""
        # Setup
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated text"
        mock_client.chat.completions.create.return_value = mock_response

        # Execute
        service = OpenAIService()
        result = service.generate("Test prompt")

        # Verify
        assert result == "Generated text"
        mock_client.chat.completions.create.assert_called_once()

    @patch("services.openai_service.OpenAI")
    @patch("services.openai_service.settings")
    def test_includes_system_prompt(self, mock_settings, mock_openai_class):
        """Should include system prompt in messages."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_client.chat.completions.create.return_value = mock_response

        service = OpenAIService()
        service.generate("User prompt", system_prompt="System prompt")

        # Verify messages include system prompt
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System prompt"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "User prompt"

    @patch("services.openai_service.OpenAI")
    @patch("services.openai_service.settings")
    def test_no_system_prompt_when_none(self, mock_settings, mock_openai_class):
        """Should not include system message when system_prompt is None."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_client.chat.completions.create.return_value = mock_response

        service = OpenAIService()
        service.generate("User prompt")

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    @patch("services.openai_service.OpenAI")
    @patch("services.openai_service.settings")
    def test_uses_configured_model(self, mock_settings, mock_openai_class):
        """Should use the model from settings."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o-mini"

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_client.chat.completions.create.return_value = mock_response

        service = OpenAIService()
        service.generate("Test")

        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4o-mini"


class TestOpenAIServiceGenerateStructured:
    """Tests for OpenAIService.generate_structured method."""

    @patch("services.openai_service.OpenAI")
    @patch("services.openai_service.settings")
    def test_generates_structured_output(self, mock_settings, mock_openai_class):
        """Should generate structured output matching model."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        expected_result = MockResponse(message="Hello", count=42)
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = expected_result
        mock_client.beta.chat.completions.parse.return_value = mock_response

        service = OpenAIService()
        result = service.generate_structured("Test", MockResponse)

        assert result == expected_result
        assert result.message == "Hello"
        assert result.count == 42

    @patch("services.openai_service.OpenAI")
    @patch("services.openai_service.settings")
    def test_uses_beta_parse_endpoint(self, mock_settings, mock_openai_class):
        """Should use the beta parse endpoint for structured output."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = MockResponse(message="Test", count=1)
        mock_client.beta.chat.completions.parse.return_value = mock_response

        service = OpenAIService()
        service.generate_structured("Test", MockResponse)

        mock_client.beta.chat.completions.parse.assert_called_once()

    @patch("services.openai_service.OpenAI")
    @patch("services.openai_service.settings")
    def test_passes_response_format(self, mock_settings, mock_openai_class):
        """Should pass response model as response_format."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = MockResponse(message="Test", count=1)
        mock_client.beta.chat.completions.parse.return_value = mock_response

        service = OpenAIService()
        service.generate_structured("Test", MockResponse)

        call_args = mock_client.beta.chat.completions.parse.call_args
        assert call_args.kwargs["response_format"] == MockResponse

    @patch("services.openai_service.OpenAI")
    @patch("services.openai_service.settings")
    def test_includes_system_prompt(self, mock_settings, mock_openai_class):
        """Should include system prompt in structured calls."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o"

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.parsed = MockResponse(message="Test", count=1)
        mock_client.beta.chat.completions.parse.return_value = mock_response

        service = OpenAIService()
        service.generate_structured("User prompt", MockResponse, system_prompt="System")

        call_args = mock_client.beta.chat.completions.parse.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"


class TestOpenAIServiceInit:
    """Tests for OpenAIService initialization."""

    @patch("services.openai_service.OpenAI")
    @patch("services.openai_service.settings")
    def test_initializes_with_api_key(self, mock_settings, mock_openai_class):
        """Should initialize OpenAI client with API key from settings."""
        mock_settings.openai_api_key = "sk-test-key"
        mock_settings.openai_model = "gpt-4o"

        OpenAIService()

        mock_openai_class.assert_called_once_with(api_key="sk-test-key")

    @patch("services.openai_service.OpenAI")
    @patch("services.openai_service.settings")
    def test_stores_model_from_settings(self, mock_settings, mock_openai_class):
        """Should store model name from settings."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.openai_model = "gpt-4o-mini"

        service = OpenAIService()

        assert service.model == "gpt-4o-mini"
