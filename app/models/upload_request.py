from pydantic import BaseModel, Field
from datetime import datetime

class UploadRequest(BaseModel):
    channel_id: str
    title: str
    description: str
    video_filename: str
    thumbnail_filename: str
    category_id: int
    status: str = "PENDING"
    video_url: str | None = None
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
