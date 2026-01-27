from openai import OpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError, APITimeoutError
from typing import Type, TypeVar

from app.config import settings


T = TypeVar("T", bound=BaseModel)


class OpenAIService:
    """Service for interacting with OpenAI GPT API."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
    )
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Generate text completion using GPT.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text response
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        return response.choices[0].message.content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
    )
    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: str | None = None,
    ) -> T:
        """
        Generate structured output using GPT with Pydantic model.

        Args:
            prompt: The user prompt
            response_model: Pydantic model class for response structure
            system_prompt: Optional system prompt

        Returns:
            Instance of response_model populated with generated data
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=response_model,
        )

        return response.choices[0].message.parsed
