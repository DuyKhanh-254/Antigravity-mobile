from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from datetime import datetime
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
        try:
            init_message_text = await asyncio.wait_for(
                websocket.receive_text(),
                timeout=5.0
            )
            init_message = json.loads(init_message_text)
        except Exception as e:
            logger.error(f"WebSocket identification failed: {e}")
            await websocket.close(code=4001, reason="Identification failed")
            return
            
        device_type = init_message.get("device_type", "unknown")
        device_id = init_message.get("device_id")
        
        if not device_id:
            logger.warning("WebSocket connection without device_id")
            await websocket.close(code=4001, reason="No device_id provided")
            return
        
        # Register connection (save reference to this specific websocket for safe cleanup)
        active_connections[device_id] = websocket
        logger.info(f"Device connected via WebSocket: {device_id} ({device_type})")
        
        # Auto-register in devices_db if not exists (Survive backend restarts)
        from app.storage import devices_db
        if device_id not in devices_db:
            devices_db[device_id] = {
                "device_id": device_id,
                "device_name": init_message.get("device_name", "Unknown Device"),
                "device_type": device_type,
                "status": "online",
                "paired_at": datetime.utcnow()
            }
            logger.info(f"Auto-registered device {device_id} in DB")
        else:
            devices_db[device_id]["status"] = "online"
            logger.info(f"Updated status to online for device {device_id}")
        
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
                    timeout=60.0  # 1 minute timeout (use heartbeat to keep alive)
                )
                message = json.loads(message_text)
                message_type = message.get("type")
                
                logger.debug(f"Received WebSocket message from {device_id}: {message_type}")
                
                if message_type == "heartbeat":
                    # Update status in DB
                    if device_id in devices_db:
                        devices_db[device_id]["status"] = "online"
                        devices_db[device_id]["last_seen"] = datetime.utcnow()
                    
                    # Echo heartbeat to keep connection alive
                    await websocket.send_json({
                        "type": "heartbeat_ack",
                        "timestamp": message.get("timestamp")
                    })
                
                elif message_type == "command_complete":
                    # Desktop finished processing
                    command_id = message.get("command_id")
                    response_text = message.get("response", "")
                    
                    logger.info(f"Command {command_id} complete. Processing storage and relay.")
                    
                    # 1. Store in database
                    if command_id in commands_db:
                        commands_db[command_id]["status"] = "completed"
                        commands_db[command_id]["completed_at"] = datetime.utcnow()
                        commands_db[command_id]["result"] = response_text
                        logger.info(f"Stored response for command {command_id}")
                    
                    # 2. Relay to mobile devices
                    for conn_id, conn_ws in list(active_connections.items()):
                        if conn_id.startswith("dev_mobile_"):
                            try:
                                await conn_ws.send_json({
                                    "type": "command_response",
                                    "command_id": command_id,
                                    "response": response_text
                                })
                            except Exception as e:
                                logger.error(f"Failed to relay to {conn_id}: {e}")
                
                elif message_type == "command_error":
                    # Desktop error
                    command_id = message.get("command_id")
                    error = message.get("error", "Unknown error")
                    
                    logger.error(f"Command {command_id} failed on desktop: {error}")
                    
                    # Update DB
                    if command_id in commands_db:
                        commands_db[command_id]["status"] = "failed"
                        commands_db[command_id]["result"] = f"Error: {error}"
                    
                    # Relay to mobile
                    for conn_id, conn_ws in list(active_connections.items()):
                        if conn_id.startswith("dev_mobile_"):
                            try:
                                await conn_ws.send_json({
                                    "type": "command_error",
                                    "command_id": command_id,
                                    "error": error
                                })
                            except Exception as e:
                                logger.error(f"Failed to relay error to {conn_id}: {e}")
                
                elif message_type == "command_chunk":
                    # Desktop sending streaming response chunk
                    command_id = message.get("command_id")
                    chunk = message.get("chunk", "")
                    
                    if command_id in commands_db:
                        commands_db[command_id]["status"] = "executing"
                    
                    # Relay to mobile
                    for conn_id, conn_ws in list(active_connections.items()):
                        if conn_id.startswith("dev_mobile_"):
                            try:
                                await conn_ws.send_json({
                                    "type": "command_chunk",
                                    "command_id": command_id,
                                    "chunk": chunk
                                })
                            except Exception as e:
                                logger.error(f"Failed to relay chunk to {conn_id}: {e}")
            
            except asyncio.TimeoutError:
                # Keep-alive ping
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
            
            except WebSocketDisconnect:
                break
            
            except Exception as e:
                logger.error(f"Error handling message from {device_id}: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket session error for {device_id}: {e}")
    
    finally:
        # Safe cleanup: only remove if it's still THIS specific connection
        if device_id and active_connections.get(device_id) == websocket:
            del active_connections[device_id]
            logger.info(f"Device {device_id} WebSocket removed from registry")
        logger.info(f"WebSocket connection closed for {device_id}")



async def send_command_to_device(device_id: str, command: dict) -> bool:
    """Send command to a specific device via WebSocket"""
    websocket = active_connections.get(device_id)
    
    if not websocket:
        logger.warning(f"Device {device_id} not connected via WebSocket")
        return False
    
    try:
        # Send command_dispatch message
        await websocket.send_json({
            "type": "command_dispatch",
            "command_id": command["command_id"],
            "payload": command["payload"]
        })
        logger.info(f"Command {command['command_id']} dispatched to device {device_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send command to device {device_id}: {e}")
        # Remove dead connection
        if device_id in active_connections:
            del active_connections[device_id]
        return False
