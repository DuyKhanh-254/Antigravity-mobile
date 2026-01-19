from fastapi import APIRouter, HTTPException, status, Header
from app.schemas.device import (
    DeviceResponse,
    DeviceStatusResponse,
    PairingCodeResponse,
    PairingConfirm
)
from app.utils.security import generate_pairing_code, generate_device_id, verify_token
from app.utils.qr_generator import generate_qr_code
from datetime import datetime, timedelta
from typing import Optional

# Import shared storage
from app.storage import devices_db, pairing_codes_db

router = APIRouter()


def get_current_user(authorization: str = Header(None)):
    """Dependency to get current user from token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload


@router.get("", response_model=list[DeviceResponse])
async def get_devices(current_user: dict = None):
    """Get all devices for current user"""
    # In production, filter by current user
    devices = []
    for device in devices_db.values():
        devices.append(DeviceResponse(
            device_id=device["device_id"],
            device_name=device["device_name"],
            device_type=device["device_type"],
            status=device.get("status", "offline"),
            last_seen=datetime.utcnow(),
            paired_at=datetime.utcnow()
        ))
    return devices


@router.get("/{device_id}/status", response_model=DeviceStatusResponse)
async def get_device_status(device_id: str):
    """Get detailed device status"""
    device = devices_db.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return DeviceStatusResponse(
        device_id=device_id,
        status=device.get("status", "offline"),
        system_info=device.get("system_info"),
        last_heartbeat=datetime.utcnow()
    )


@router.post("/pairing/generate", response_model=PairingCodeResponse)
async def generate_pairing_qr():
    """Generate a pairing QR code"""
    pairing_code = generate_pairing_code()
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Store pairing code
    pairing_codes_db[pairing_code] = {
        "code": pairing_code,
        "expires_at": expires_at,
        "used": False
    }
    
    # Generate QR data
    qr_data = f"antigravity://pair?code={pairing_code}&server=relay.example.com"
    qr_image = generate_qr_code(qr_data)
    
    return PairingCodeResponse(
        pairing_code=pairing_code,
        qr_data=qr_data,
        qr_image=qr_image,
        expires_at=expires_at
    )


@router.post("/pairing/confirm")
async def confirm_pairing(pairing_data: PairingConfirm):
    """Confirm device pairing with code"""
    # Verify pairing code
    pairing_info = pairing_codes_db.get(pairing_data.pairing_code)
    if not pairing_info:
        raise HTTPException(status_code=404, detail="Invalid pairing code")
    
    if pairing_info["used"]:
        raise HTTPException(status_code=400, detail="Pairing code already used")
    
    if datetime.utcnow() > pairing_info["expires_at"]:
        raise HTTPException(status_code=400, detail="Pairing code expired")
    
    # Create device
    device_id = generate_device_id("desktop")
    devices_db[device_id] = {
        "device_id": device_id,
        "device_name": pairing_data.device_name,
        "device_type": "desktop",
        "status": "online",
        "paired_at": datetime.utcnow()
    }
    
    # Mark code as used
    pairing_info["used"] = True
    
    return {
        "device_id": device_id,
        "paired": True
    }


@router.delete("/{device_id}")
async def unpair_device(device_id: str):
    """Unpair a device"""
    if device_id not in devices_db:
        raise HTTPException(status_code=404, detail="Device not found")
    
    del devices_db[device_id]
    return {"message": "Device unpaired successfully"}
