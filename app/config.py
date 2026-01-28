from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration using pydantic-settings."""

    # OpenAI Configuration
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")

    # Deepgram Configuration (for transcription with speaker diarization)
    deepgram_api_key: str = Field(..., alias="DEEPGRAM_API_KEY")

    # Processing Configuration
    max_file_size_mb: int = Field(default=100, alias="MAX_FILE_SIZE_MB")
    max_retries: int = Field(default=2, alias="MAX_RETRIES")
    audio_chunk_size_mb: int = Field(default=24, alias="AUDIO_CHUNK_SIZE_MB")

    # Scoring Configuration
    passing_grade_threshold: float = Field(default=70.0, alias="PASSING_GRADE_THRESHOLD")
    escalation_threshold: float = Field(default=50.0, alias="ESCALATION_THRESHOLD")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
