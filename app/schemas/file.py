from pydantic import BaseModel
from datetime import datetime


class FileUploadResponse(BaseModel):
    """File upload response"""
    file_id: str
    filename: str
    size_bytes: int
    uploaded_at: datetime
    
    class Config:
        from_attributes = True
