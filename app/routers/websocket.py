from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections: {device_id: websocket}
active_connections: Dict[str, WebSocket] = {}

# Command storage (import from commands.py storage)
from app.routers.commands import commands_db


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    device_id = None
    
    try:
        # Receive initial message with device identification
        init_message_text = await websocket.receive_text()
        init_message = json.loads(init_message_text)
        
        device_type = init_message.get("device_type", "unknown")
        device_id = init_message.get("device_id")
        
        if not device_id:
            logger.warning("WebSocket connection without device_id")
            await websocket.close(code=4001, reason="No device_id provided")
            return
        
        # Register connection
        active_connections[device_id] = websocket
        logger.info(f"Device connected via WebSocket: {device_id} ({device_type})")
        
        # Acknowledge connection
        await websocket.send_json({
            "type": "connection_ack",
            "device_id": device_id,
            "message": "Connected successfully"
        })
        
        # Main message loop
        while True:
            try:
                message_text = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=120.0  # 2 minute timeout
                )
                message = json.loads(message_text)
                message_type = message.get("type")
                
                logger.debug(f"Received WebSocket message from {device_id}: {message_type}")
                
                # Handle different message types
                if message_type == "heartbeat":
                    # Echo heartbeat
                    await websocket.send_json({
                        "type": "heartbeat_ack",
                        "timestamp": message.get("timestamp")
                    })
                
                elif message_type == "command_dispatch":
                    # Desktop requesting commands (not used in current architecture)
                    pass
                
                elif message_type == "command_chunk":
                    # Desktop sending response chunk - relay to mobile
                    command_id = message.get("command_id")
                    if command_id in commands_db:
                        # Update command status
                        commands_db[command_id]["status"] = "executing"
                        
                        # Relay to requesting device (mobile)
                        # For MVP: just log, in production relay to mobile client
                        logger.info(f"Command {command_id} chunk received: {message.get('chunk')[:50]}...")
                
                elif message_type == "command_complete":
                    # Desktop finished executing command
                    command_id = message.get("command_id")
                    if command_id in commands_db:
                        commands_db[command_id]["status"] = "completed"
                        commands_db[command_id]["completed_at"] = message.get("timestamp")
                        commands_db[command_id]["success"] = message.get("success", True)
                        logger.info(f"Command {command_id} completed")
            
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({"type": "ping"})
            
            except WebSocketDisconnect:
                logger.info(f"Device {device_id} disconnected")
                break
            
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
            
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    
    finally:
        # Remove from active connections
        if device_id and device_id in active_connections:
            del active_connections[device_id]
            logger.info(f"Device {device_id} WebSocket closed")


async def send_command_to_device(device_id: str, command: dict) -> bool:
    """Send a command to a connected device via WebSocket"""
    if device_id not in active_connections:
        logger.warning(f"Device {device_id} not connected via WebSocket")
        return False
    
    try:
        websocket = active_connections[device_id]
        await websocket.send_json({
            "type": "command_dispatch",
            "command_id": command["command_id"],
            "command_type": command["type"],
            "payload": command["payload"]
        })
        logger.info(f"Command {command['command_id']} sent to device {device_id}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send command to {device_id}: {e}")
        return False
