from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, devices, commands, files, audit, websocket
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

# CORS middleware - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
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
app.include_router(websocket.router, prefix="/api/v1", tags=["WebSocket"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Antigravity Link Backend...")
    # Initialize database connection pool
    # Initialize Redis connection
    # Initialize Firebase Admin SDK
    logger.info("Backend started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Antigravity Link Backend...")
    # Close database connections
    # Close Redis connections
    logger.info("Backend shut down successfully")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Antigravity Link API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: actual DB check
        "redis": "connected",      # TODO: actual Redis check
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
