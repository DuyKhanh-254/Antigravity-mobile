from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, TokenRefresh
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_device_id
)
from datetime import timedelta
from app.config import settings

# Import shared storage
from app.storage import users_db, devices_db

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Registration attempt for email: {user_data.email}")
        
        # Check if user already exists
        if user_data.email in users_db:
            logger.warning(f"Email already registered: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user_id = f"usr_{len(users_db) + 1}"
        users_db[user_data.email] = {
            "user_id": user_id,
            "email": user_data.email,
            "password_hash": get_password_hash(user_data.password),
            "created_at": "2026-01-19T10:53:55Z"
        }
        
        # Create device for this user
        device_id = generate_device_id("mobile")
        devices_db[device_id] = {
            "device_id": device_id,
            "user_id": user_id,
            "device_name": user_data.device_name,
            "device_type": "mobile",
            "status": "online"
        }
        
        logger.info(f"User registered successfully: {user_id}, Device: {device_id}")
        
        # Generate tokens
        token_data = {"sub": user_id, "email": user_data.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login user"""
    # Find user
    user = users_db.get(user_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Generate tokens
    token_data = {"sub": user["user_id"], "email": user["email"]}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh):
    """Refresh access token"""
    # Verify refresh token
    payload = verify_token(token_data.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Generate new tokens
    new_token_data = {"sub": payload["sub"], "email": payload["email"]}
    access_token = create_access_token(new_token_data)
    new_refresh_token = create_refresh_token(new_token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/logout")
async def logout():
    """Logout user (invalidate tokens in production)"""
    # In production, add token to blacklist
    return {"message": "Logged out successfully"}
