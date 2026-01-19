from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import hashlib
import secrets
from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (SHA256-based)"""
    # Extract salt from stored hash (format: salt$hash)
    if '$' not in hashed_password:
        return False
    salt, stored_hash = hashed_password.split('$', 1)
    # Hash the provided password with the stored salt
    password_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
    return password_hash == stored_hash


def get_password_hash(password: str) -> str:
    """Hash a password using SHA256 with salt (simple, no bcrypt issues)"""
    # Generate a random salt
    salt = secrets.token_hex(16)
    # Hash password with salt
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    # Return format: salt$hash
    return f"{salt}${password_hash}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


def generate_pairing_code() -> str:
    """Generate a one-time pairing code"""
    import secrets
    import string
    
    # Generate 8-character code (AG-XXXX-XXXX format)
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(8))
    return f"AG-{code[:4]}-{code[4:]}"


def generate_device_id(device_type: str) -> str:
    """Generate a unique device ID"""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return f"dev_{device_type}_{unique_id}"
