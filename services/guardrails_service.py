"""Guardrails service for validating call center content."""

from guardrails import Guard, OnFailAction
from guardrails.validators import Validator, register_validator, ValidationResult, FailResult, PassResult
from typing import Any, Callable

from services.openai_service import OpenAIService


VALIDATION_PROMPT = """Analyze this text and determine if it is a call center conversation.

Text:
{text}

A VALID call center transcript MUST have ALL of these:
1. A dialogue between at least 2 parties (agent and customer)
2. Customer service context (support, sales, inquiry, complaint)
3. Back-and-forth conversation pattern

INVALID content includes:
- Single-person narratives or monologues
- Articles, essays, documentation
- Fiction or creative writing
- Podcasts or interviews (unless customer service)
- Non-customer-service chat logs

Respond with ONLY "VALID" or "INVALID: <reason>"
Be strict - reject if uncertain."""


@register_validator(name="call_center_content", data_type="string")
class CallCenterContentValidator(Validator):
    """Validates that content is a call center conversation."""

    def __init__(
        self,
        on_fail: OnFailAction | Callable | None = None,
        **kwargs,
    ):
        super().__init__(on_fail=on_fail, **kwargs)

    def validate(self, value: Any, metadata: dict) -> ValidationResult:
        """Validate that the content is a call center conversation."""

        if not value or not isinstance(value, str):
            return FailResult(
                error_message="Content is empty or not a string",
            )

        text = value.strip()

        # Check minimum length
        if len(text) < 100:
            return FailResult(
                error_message="Content is too short to be a valid call transcript (minimum 100 characters)",
            )

        # Check for strong transcript indicators (skip LLM check)
        text_lower = text.lower()
        strong_indicators = [
            "agent:", "customer:", "representative:", "caller:",
            "**agent**", "**customer**", "**speaker",
        ]
        if any(indicator in text_lower for indicator in strong_indicators):
            return PassResult()

        # Use LLM to validate
        try:
            openai_service = OpenAIService()
            sample_text = text[:3000] if len(text) > 3000 else text

            response = openai_service.generate(
                prompt=VALIDATION_PROMPT.format(text=sample_text),
                system_prompt="You validate if text is a call center conversation. Respond only with VALID or INVALID: <reason>",
            )

            response = response.strip().upper()

            if response.startswith("VALID"):
                return PassResult()
            else:
                # Extract reason from "INVALID: <reason>"
                reason = response.replace("INVALID:", "").replace("INVALID", "").strip()
                if not reason:
                    reason = "Content does not appear to be a call center conversation"
                return FailResult(error_message=reason)

        except Exception as e:
            return FailResult(
                error_message=f"Validation failed: {str(e)}",
            )


class ContentValidationError(Exception):
    """Raised when content validation fails."""
    pass


class GuardrailsService:
    """Service for validating content using Guardrails AI."""

    def __init__(self):
        self.guard = Guard().use(
            CallCenterContentValidator(on_fail=OnFailAction.EXCEPTION)
        )

    def validate_call_center_content(self, content: str) -> tuple[bool, str]:
        """
        Validate that content is a call center conversation.

        Returns:
            tuple of (is_valid, message)

        Raises:
            ContentValidationError if validation fails
        """
        try:
            self.guard.validate(content)
            return True, "Content validated as call center conversation"
        except Exception as e:
            error_msg = str(e)
            # Clean up the error message
            if "Validation failed for field" in error_msg:
                # Extract just the validation reason
                parts = error_msg.split(":")
                if len(parts) > 1:
                    error_msg = parts[-1].strip()
            return False, error_msg
