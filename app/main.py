"""
Antigravity Link Backend - FastAPI Application
Production-ready configuration for Railway deployment
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, devices, commands, files, audit, websocket, projects
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Antigravity Link API",
    description="Remote control system for Antigravity",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(commands.router, prefix="/api/v1/commands", tags=["Commands"])
app.include_router(files.router, prefix="/api/v1/files", tags=["Files"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(websocket.router, prefix="/api/v1", tags=["WebSocket"])

logger.info("Antigravity Link Backend started successfully")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "Antigravity Link",
        "version": settings.app_version,
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.app_version}
