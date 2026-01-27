from pydantic import BaseModel, Field
from typing import Optional


SUPPORTED_AUDIO_FORMATS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
SUPPORTED_TEXT_FORMATS = {".txt", ".json"}
MAX_FILE_SIZE_MB = 100


class FileInput(BaseModel):
    """Input file validation schema."""

    file_path: str = Field(description="Path to the uploaded file")
    file_name: str = Field(description="Original filename")
    file_type: Optional[str] = Field(
        default=None, description="'audio' or 'transcript'"
    )


class TranscriptInput(BaseModel):
    """Direct transcript input schema."""

    text: str = Field(description="Raw transcript text")
    call_id: Optional[str] = Field(default=None, description="Optional call identifier")
    agent_id: Optional[str] = Field(default=None, description="Optional agent identifier")
