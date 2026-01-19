from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class CommandCreate(BaseModel):
    """Command creation request"""
    target_device_id: str
    type: str  # "prompt", "file_process", etc.
    payload: dict


class CommandResponse(BaseModel):
    """Command response"""
    command_id: str
    status: str  # "queued", "processing", "completed", "failed"
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    
    class Config:
        from_attributes = True


class CommandListResponse(BaseModel):
    """List of commands with pagination"""
    commands: list[CommandResponse]
    total: int
    limit: int
    offset: int
