from fastapi import APIRouter

router = APIRouter()

# In-memory storage (replace with database in production)
audit_logs = []


@router.get("/logs")
async def get_audit_logs(device_id: str = None, limit: int = 50, offset: int = 0):
    """Get audit logs"""
    filtered_logs = audit_logs
    if device_id:
        filtered_logs = [log for log in filtered_logs if log.get("device_id") == device_id]
    
    # Pagination
    total = len(filtered_logs)
    paginated = filtered_logs[offset:offset + limit]
    
    return {
        "logs": paginated,
        "total": total,
        "limit": limit,
        "offset": offset
    }


def log_action(action: str, device_id: str, user_id: str, details: dict = None):
    """Helper function to log an action"""
    from datetime import datetime
    
    log_entry = {
        "log_id": f"log_{len(audit_logs) + 1:03d}",
        "timestamp": datetime.utcnow().isoformat(),
        "device_id": device_id,
        "user_id": user_id,
        "action": action,
        "details": details or {}
    }
    audit_logs.append(log_entry)
