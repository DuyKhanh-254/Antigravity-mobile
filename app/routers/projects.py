from fastapi import APIRouter, HTTPException, Query, Body
import uuid
import asyncio
import logging
from typing import List, Optional
from app.routers.websocket import active_connections, pending_requests

logger = logging.getLogger(__name__)
router = APIRouter()

async def desktop_request(device_id: str, message_type: str, payload: dict = None, timeout: float = 10.0):
    """Utility to send a request to desktop via WS and wait for response"""
    websocket = active_connections.get(device_id)
    if not websocket:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not connected")
        
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    future = asyncio.get_event_loop().create_future()
    pending_requests[request_id] = future
    
    # Send request
    request_msg = {
        "type": message_type,
        "request_id": request_id,
        "device_id": device_id
    }
    if payload:
        request_msg.update(payload)
        
    try:
        await websocket.send_json(request_msg)
        # Wait for response with timeout
        response = await asyncio.wait_for(future, timeout=timeout)
        if response.get("type") == "error":
             raise HTTPException(status_code=500, detail=response.get("message", "Desktop Error"))
        return response
    except asyncio.TimeoutError:
        if request_id in pending_requests:
            del pending_requests[request_id]
        raise HTTPException(status_code=504, detail="Desktop agent timed out")
    except Exception as e:
        if request_id in pending_requests:
            del pending_requests[request_id]
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
async def list_projects(device_id: str):
    """List projects on a specific desktop device"""
    response = await desktop_request(device_id, "get_projects")
    return response.get("projects", [])

@router.get("/{project_id}/tree")
async def get_project_tree(project_id: str, device_id: str, path: str = ""):
    """Get file tree for a project"""
    response = await desktop_request(device_id, "get_tree", {"project_id": project_id, "path": path})
    return response.get("tree", [])

@router.get("/{project_id}/file")
async def read_project_file(project_id: str, device_id: str, path: str):
    """Read a file's content from a project"""
    response = await desktop_request(device_id, "read_file", {"project_id": project_id, "path": path})
    return {"content": response.get("content")}

@router.put("/{project_id}/file")
async def write_project_file(project_id: str, device_id: str, path: str, content: str = Body(embed=True)):
    """Save content to a project file"""
    response = await desktop_request(device_id, "write_file", {
        "project_id": project_id, 
        "path": path, 
        "content": content
    })
    return {"success": True}

@router.post("/{project_id}/exec")
async def run_project_command(project_id: str, device_id: str, command: str = Body(embed=True)):
    """Run a command in a project (Async results via WS)"""
    exec_id = f"exec_{uuid.uuid4().hex[:8]}"
    # No waiting for response here, just dispatch
    websocket = active_connections.get(device_id)
    if not websocket:
        raise HTTPException(status_code=404, detail="Device not connected")
        
    await websocket.send_json({
        "type": "run_project_command",
        "project_id": project_id,
        "command": command,
        "exec_id": exec_id
    })
    return {"exec_id": exec_id, "status": "started"}
