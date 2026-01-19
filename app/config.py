"""
Production-ready configuration
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    app_name: str = "Antigravity Link"
    app_version: str = "1.0.0"
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # CORS - Allow all for development, restrict in production
    allowed_origins: list = ["*"]
    
    # Server
    host: str = "0.0.0.0"
    port: int = int(os.getenv("PORT", 8000))
    
    # File Storage
    file_storage_path: str = "./uploads"
    
    # Database (for future use)
    database_url: str = Field(default="sqlite:///./antigravity.db")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
