from fastapi import APIRouter, HTTPException, status
from app.schemas.command import CommandCreate, CommandResponse, CommandListResponse
from datetime import datetime
import uuid

router = APIRouter()

# In-memory storage (replace with database + Redis in production)
commands_db = {}


@router.post("", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
async def create_command(command_data: CommandCreate):
    """Create a new command"""
    command_id = f"cmd_{uuid.uuid4().hex[:8]}"
    
    command = {
        "command_id": command_id,
        "target_device_id": command_data.target_device_id,
        "type": command_data.type,
        "payload": command_data.payload,
        "status": "queued",
        "created_at": datetime.utcnow(),
        "started_at": None,
        "completed_at": None,
        "result": None
    }
    
    commands_db[command_id] = command
    
    # Send command to desktop via WebSocket
    from app.routers.websocket import send_command_to_device
    try:
        sent = await send_command_to_device(command_data.target_device_id, command)
        if sent:
            command["status"] = "dispatched"
    except Exception as e:
        import logging
        logging.error(f"Failed to send command via WebSocket: {e}")
    
    return CommandResponse(**command)


@router.get("/{command_id}", response_model=CommandResponse)
async def get_command(command_id: str):
    """Get command status and result"""
    command = commands_db.get(command_id)
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    
    return CommandResponse(**command)


@router.get("", response_model=CommandListResponse)
async def list_commands(device_id: str = None, limit: int = 20, offset: int = 0):
    """List commands with pagination"""
    # Filter by device if specified
    filtered_commands = list(commands_db.values())
    if device_id:
        filtered_commands = [
            cmd for cmd in filtered_commands 
            if cmd["target_device_id"] == device_id
        ]
    
    # Sort by created_at descending
    filtered_commands.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Pagination
    total = len(filtered_commands)
    paginated = filtered_commands[offset:offset + limit]
    
    return CommandListResponse(
        commands=[CommandResponse(**cmd) for cmd in paginated],
        total=total,
        limit=limit,
        offset=offset
    )
