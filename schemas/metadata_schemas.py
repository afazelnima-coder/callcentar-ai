from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CallMetadata(BaseModel):
    """Metadata extracted from call file."""

    # File information
    file_name: str
    file_size_bytes: int
    file_format: str  # wav, mp3, m4a, txt, etc.

    # Audio-specific (None if transcript)
    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None

    # Call context (if available from filename or user input)
    call_id: Optional[str] = None
    agent_id: Optional[str] = None
    customer_id: Optional[str] = None
    call_date: Optional[datetime] = None
    call_type: Optional[str] = None  # 'support', 'sales', 'inquiry', etc.
