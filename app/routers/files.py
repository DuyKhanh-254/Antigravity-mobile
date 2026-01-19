from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from app.schemas.file import FileUploadResponse
from datetime import datetime
import uuid
import os
from pathlib import Path
from app.config import settings

router = APIRouter()

# In-memory storage (replace with database in production)
files_db = {}

# Ensure file storage directory exists
Path(settings.file_storage_path).mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...), target_device_id: str = None):
    """Upload a file"""
    # Check file size
    contents = await file.read()
    file_size = len(contents)
    
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.max_file_size_mb}MB"
        )
    
    # Generate file ID and save
    file_id = f"file_{uuid.uuid4().hex[:8]}"
    file_path = os.path.join(settings.file_storage_path, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Store metadata
    files_db[file_id] = {
        "file_id": file_id,
        "filename": file.filename,
        "size_bytes": file_size,
        "file_path": file_path,
        "target_device_id": target_device_id,
        "uploaded_at": datetime.utcnow()
    }
    
    return FileUploadResponse(
        file_id=file_id,
        filename=file.filename,
        size_bytes=file_size,
        uploaded_at=datetime.utcnow()
    )


@router.get("/{file_id}/download")
async def download_file(file_id: str):
    """Download a file"""
    file_info = files_db.get(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = file_info["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=file_info["filename"],
        media_type="application/octet-stream"
    )


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete a file"""
    file_info = files_db.get(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete file from disk
    try:
        os.remove(file_info["file_path"])
    except OSError:
        pass
    
    # Remove from database
    del files_db[file_id]
    
    return {"message": "File deleted successfully"}
