from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DeviceBase(BaseModel):
    """Base device schema"""
    device_name: str
    device_type: str  # "mobile" or "desktop"


class DeviceCreate(DeviceBase):
    """Device creation schema"""
    device_fingerprint: Optional[str] = None


class DeviceResponse(DeviceBase):
    """Device response schema"""
    device_id: str
    status: str  # "online", "offline"
    last_seen: datetime
    paired_at: datetime
    
    class Config:
        from_attributes = True


class DeviceStatusResponse(BaseModel):
    """Detailed device status"""
    device_id: str
    status: str
    system_info: Optional[dict] = None
    last_heartbeat: Optional[datetime] = None


class PairingCodeResponse(BaseModel):
    """Pairing code response"""
    pairing_code: str
    qr_data: str
    qr_image: str  # base64 encoded image
    expires_at: datetime


class PairingConfirm(BaseModel):
    """Pairing confirmation request"""
    pairing_code: str
    device_name: str
